from typing import Type

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.v1.schemas.user import CreateUserRequest, UpdateUserRequest
from app.api.v1.schemas.user import FriendSearch
from app.core.settings import SUPER_USER, STATIC
from app.db.postgres.models.user import User
from .auth import bcrypt_context
from app.extra.query import UserQuery

integrity_error_fields = ["email", "username", "contact_number"]


def extract_integrity_error(detail: str) -> str:
    for field in integrity_error_fields:
        if detail.__contains__(f"Key ({field})"):
            return f"user with {field} already exists!!"

    return "something went wrong in database"


async def create_user(postgres: AsyncSession, user_data: CreateUserRequest):
    user = user_data.model_dump()

    superuser_pass = user.pop("superuser_pass")
    password = user.pop("password")

    user["profile"] = f"/{STATIC}/profile/default_profile.jpg"

    if superuser_pass and superuser_pass == SUPER_USER["ACCESS_PASSWORD"]:
        is_superuser = True
    else:
        is_superuser = False

    user_model = User(**user)

    user_model.is_superuser = is_superuser
    user_model.hashed_password = bcrypt_context.hash(password)
    postgres.add(user_model)

    try:
        await postgres.commit()
        await postgres.refresh(user_model)

    except IntegrityError as exc:
        await postgres.rollback()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=extract_integrity_error(str(exc.orig.__cause__)),
        )

    return user_model


async def update_user_data(
    postgres: AsyncSession, user: User, update_data: UpdateUserRequest
):
    user_data = update_data.model_dump()

    for key, value in user_data.items():
        if value is not None and key != "password":
            setattr(user, key, value)
        elif value is not None and key == "password":
            user.hashed_password = bcrypt_context.hash(value)

    try:
        await postgres.commit()
    except IntegrityError as exc:
        await postgres.rollback()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=extract_integrity_error(str(exc.orig.__cause__)),
        )

    return user


async def get_user_for_add(
    postgres: AsyncSession, main_user_id: int, second_user_id: int, operation: str
):
    main_user = await UserQuery.one(postgres, main_user_id)
    second_user = await UserQuery.one(postgres, second_user_id, False)
    is_already_in_operation = False

    if main_user is None or second_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if operation == "unfriend":
        if (
            second_user not in main_user.friend
            and second_user not in main_user.friend_by
        ):
            is_already_in_operation = True

    elif operation == "friend":
        if second_user in main_user.friend or second_user in main_user.friend_by:
            is_already_in_operation = True

    elif second_user in getattr(main_user, operation):
        is_already_in_operation = True

    return main_user, second_user, is_already_in_operation


def get_friend_search_res(users: list[User], self_user: Type[User]):
    response = []
    for usr in users:
        if usr in self_user.friend or usr in self_user.friend_by:
            frnd_status = "friend"
        elif usr in self_user.requested_user:
            frnd_status = "requested"
        elif usr in self_user.requested_by:
            frnd_status = "requested_by"
        elif usr in self_user.blocked_user:
            frnd_status = "blocked"
        else:
            frnd_status = "none"

        response.append(
            FriendSearch(
                **usr.__dict__,
                friend_status=frnd_status,
            )
        )
    return response
