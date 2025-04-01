from datetime import datetime, timezone
from typing import cast

from fastapi import WebSocketException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError, ExpiredSignatureError
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres.models.user import User
from starlette import status

from app.api.v1.handlers.exceptions import (
    TokenExpiredException,
    AccountBlockedException,
    AuthException,
    InvalidTokenException,
    IncorrectCredentialsException,
)
from app.db.mango.models.token import (
    OutstandingRefreshToken,
    BlackListedRefreshToken,
)
from app.core.settings import JWT
from odmantic.session import AIOSession
from odmantic.exceptions import DocumentNotFoundError
from odmantic import Model

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/auth/token")


def check_account_status(acc_status: bool):
    if not acc_status:
        raise AccountBlockedException()


async def authenticate_user(db: AsyncSession, username: str, password: str):
    query = select(User).where(User.username == username)
    user = await db.scalar(query)
    if not user or not bcrypt_context.verify(password, cast(str, user.hashed_password)):
        raise IncorrectCredentialsException()
    return user


async def token_document_delete(mango: AIOSession, document: Model):
    try:
        await mango.delete(document)
    except DocumentNotFoundError:
        raise InvalidTokenException()


class Token:
    # must be field name of User model
    extra_encode_fields = [
        "is_superuser",
        "is_active",
    ]

    def __init__(self, user: User):

        self.user = user
        self.refresh_token = None
        self.access_token = None

    def get_token(self):
        return {
            "access_token": self.create_token("access"),
            "refresh_token": self.create_token("refresh"),
            "token_type": "bearer",
        }

    def get_encode_data(self, token_type: str):
        encode = {
            "sub": self.user.username,
            "id": self.user.id,
            "type": token_type,
            "exp": (
                datetime.now(tz=timezone.utc)
                + (
                    JWT["ACCESS_TOKEN_EXPIRES"]
                    if token_type == "access"
                    else JWT["REFRESH_TOKEN_EXPIRES"]
                )
            ),
        }
        for field in self.extra_encode_fields:
            encode[field] = getattr(self.user, field)
        return encode

    def create_token(self, token_type: str):
        encode = self.get_encode_data(token_type)
        token = jwt.encode(encode, JWT["SECRET_KEY"], algorithm=JWT["ALGORITHM"])
        if token_type == "access":
            self.access_token = token
        else:
            self.refresh_token = token
        return token

    @staticmethod
    def verify_token(token: str):
        try:
            payload = jwt.decode(
                token, JWT["SECRET_KEY"], algorithms=[JWT["ALGORITHM"]]
            )
            return payload

        except ExpiredSignatureError:
            raise TokenExpiredException()
        except JWTError:
            raise AuthException()

    @staticmethod
    async def verify_refresh_token(mangodb: AIOSession, token: str):
        refresh_token = Token.verify_token(token)
        if refresh_token["type"] == "access":
            raise InvalidTokenException()

        outstanding_token = await mangodb.find_one(
            OutstandingRefreshToken, OutstandingRefreshToken.token == token
        )
        if outstanding_token is None:
            raise InvalidTokenException()

        blacklisted_token = await mangodb.find_one(
            BlackListedRefreshToken, BlackListedRefreshToken.token == token
        )
        if blacklisted_token:
            raise InvalidTokenException()

        return refresh_token

    @staticmethod
    async def save_refresh_token_to_outstanding(
        mangodb: AIOSession, token: str, user_id: int
    ):
        refresh_token = OutstandingRefreshToken(user_id=user_id, token=token)
        await mangodb.save(refresh_token)

    @staticmethod
    async def save_refresh_token_to_blacklist(
        mangodb: AIOSession, token: str, user_id: int
    ):
        outstanding = await mangodb.find_one(
            OutstandingRefreshToken,
            (OutstandingRefreshToken.user_id == user_id)
            & (OutstandingRefreshToken.token == token),
        )
        if outstanding:
            await token_document_delete(mangodb, outstanding)
        else:
            raise InvalidTokenException()

        refresh_token = BlackListedRefreshToken(
            token=token, user_id=user_id, expires_at=outstanding.expires_at
        )
        await mangodb.save(refresh_token)

    @staticmethod
    async def delete_all_tokens(mangodb: AIOSession, user_id: int):
        outstanding_tokens = await mangodb.find(
            OutstandingRefreshToken, OutstandingRefreshToken.user_id == user_id
        )
        for t in outstanding_tokens:
            await token_document_delete(mangodb, t)

        blacklisted_tokens = await mangodb.find(
            BlackListedRefreshToken, BlackListedRefreshToken.user_id == user_id
        )
        for t in blacklisted_tokens:
            await token_document_delete(mangodb, t)

        return {
            "user_id": user_id,
            "deleted_outstanding_tokens": outstanding_tokens,
            "deleted_black_token": blacklisted_tokens,
        }


def verify_ws_token(token: str):
    try:
        payload = jwt.decode(token, JWT["SECRET_KEY"], algorithms=[JWT["ALGORITHM"]])
        user_id = payload.get("id")
        token_type = payload.get("type")
        if user_id is None or str(token_type) == "refresh":
            raise JWTError
        return int(user_id)

    except ExpiredSignatureError:
        raise WebSocketException(
            code=status.WS_1002_PROTOCOL_ERROR, reason="Token expired"
        )
    except JWTError:
        raise WebSocketException(
            code=status.WS_1002_PROTOCOL_ERROR, reason="Invalid token"
        )
