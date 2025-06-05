from uuid import uuid4

from PIL import Image
from fastapi import APIRouter, Request, HTTPException, UploadFile, File
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from starlette import status

from app.core import settings
from ..handlers.exceptions import UserNotFoundException, IncorrectCredentialsException
from app.api.permission import require_authentication
from app.services.auth import Token, bcrypt_context
from app.db.postgres.dependency import postgres_dependency
from app.db.mango.dependency import mangodb_dependency
from app.db.mango.models.room import Room
from app.extra.query import UserQuery
from app.services.websocket.connections import room_connections, main_connections
from app.db.postgres.models.user import User
from app.api.v1.schemas.user import (
    CreateUserRequest,
    UpdateUserRequest,
    FriendSearch,
    UpdateUsername,
    UpdatePassword,
    UserResponse,
)
from app.services.user import (
    create_user,
    update_user_data,
    get_friend_search_res,
    extract_integrity_error,
)
from app.utils.image import resize_image
from app.api.v1.schemas.message import OnlineUserResponse
from app.api.v1.schemas.user import UserModel

router = APIRouter(prefix="/user", tags=["user"])


@router.get("/getuser/", response_model=UserResponse)
@require_authentication()
async def get_user(
    request: Request,
    db: postgres_dependency,
    uid: str | None = None,
    user_id: int | None = None,
):
    if user_id:
        return await UserQuery.one(db, user_id)
    elif uid:
        return await UserQuery.one_by_uid(db, uid)

    return await UserQuery.one(db, request.user.id)


@router.post("/createuser/", status_code=status.HTTP_201_CREATED)
async def create_new_user(
    request: Request,
    db: postgres_dependency,
    mangodb: mangodb_dependency,
    create_user_request: CreateUserRequest,
):
    user = await create_user(db, create_user_request)
    token = Token(user).get_token()
    await Token.save_refresh_token_to_outstanding(
        mangodb, token.get("refresh_token"), user.id
    )
    return token


@router.patch("/updateuser/", status_code=status.HTTP_202_ACCEPTED)
@require_authentication()
async def update_user(
    request: Request, db: postgres_dependency, update_data: UpdateUserRequest
):
    user = await UserQuery.one(db, request.user.id)
    if user is None:
        raise UserNotFoundException()
    return await update_user_data(db, user, update_data)


@router.post("/upload/profile/")
@require_authentication()
async def upload_file(
    request: Request, db: postgres_dependency, uploaded_file: UploadFile = File(...)
):
    file_name = str(uuid4()) + "." + uploaded_file.filename
    path = f"{settings.STATIC}/profile/{file_name}"

    with Image.open(uploaded_file.file) as img:
        resize_image(img, (300, 300)).save(path)

    user = await UserQuery.one(db, request.user.id)
    user.profile = path
    await db.commit()

    return {
        "file": file_name,
        "content": uploaded_file.content_type,
        "path": path,
    }


@router.put("/updateusername/")
@require_authentication()
async def update_username(
    request: Request, db: postgres_dependency, update_data: UpdateUsername
):
    user = await UserQuery.one(db, request.user.id)
    if user is None:
        raise UserNotFoundException()
    if not bcrypt_context.verify(update_data.password, user.hashed_password):
        raise IncorrectCredentialsException()

    user.username = update_data.username
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=extract_integrity_error(str(exc.orig.__cause__)),
        )

    return user


@router.put("/updatepassword/")
@require_authentication()
async def update_password(
    request: Request, db: postgres_dependency, update_data: UpdatePassword
):
    user = await UserQuery.one(db, request.user.id)
    if user is None:
        raise UserNotFoundException()
    if not bcrypt_context.verify(update_data.old, user.hashed_password):
        raise IncorrectCredentialsException()
    user.hashed_password = bcrypt_context.hash(update_data.new)
    await db.commit()

    return user


@router.delete("/delete/", status_code=status.HTTP_202_ACCEPTED)
@require_authentication()
async def delete_user(
    request: Request,
    db: postgres_dependency,
    mangodb: mangodb_dependency,
):

    user = await UserQuery.one(db, request.user.id, False)
    if user is None:
        raise UserNotFoundException()

    # close the room if connected and deactivate the room
    room_query = {"users": {"$elemMatch": {"user_id": user.id}}}
    rooms = await mangodb.find(Room, room_query)
    for room in rooms:
        if room.is_active:
            room.is_active = False
            await mangodb.commit()
        if str(room.id) in room_connections:
            # close the room
            del room_connections[str(room.id)]

    await db.delete(user)
    await db.commit()
    return user


@router.get("/search/", response_model=list[FriendSearch])
@require_authentication()
async def search_user(
    request: Request,
    db: postgres_dependency,
    search_type: str = "",
    search: str = "",
    offset: int = 0,
    limit: int = 10,
):
    if search_type not in ("name", "uid", "contact"):
        raise HTTPException(
            detail="search type must be in (name, uid, contact)",
            status_code=400,
        )

    self_user = await UserQuery.one(db, request.user.id)

    if search == "" or search_type == "":
        stmt = (
            select(User).where(User.id != request.user.id).offset(offset).limit(limit)
        )
        users = (await db.scalars(stmt)).unique().all()

        return get_friend_search_res(users, self_user)

    stmt = select(User)

    if search_type == "name":
        if search.split(" ").__len__() == 1:
            stmt = stmt.where(
                User.first_name.ilike(f"%{search}%")
                | User.last_name.ilike(f"%{search}")
            )
        else:
            stmt = stmt.where(
                (
                    User.first_name.ilike(f"%{search.split(" ")[0]}%")
                    & User.last_name.ilike(f"%{search.split(" ")[1]}%")
                )
                | (
                    User.first_name.ilike(f"%{search.split(" ")[1]}%")
                    & User.last_name.ilike(f"%{search.split(" ")[0]}%")
                )
            )

    elif search_type == "uid":
        stmt = stmt.where(User.uid == search)
    else:
        try:
            stmt = stmt.where(User.contact_number == int(search))
        except ValueError:
            raise HTTPException(
                detail="search word is not valid for contact number", status_code=400
            )

    stmt = stmt.offset(offset).limit(limit)

    users = (await db.scalars(stmt)).unique().all()

    return get_friend_search_res(users, self_user)


@router.get("/onlineuser/", response_model=list[OnlineUserResponse])
@require_authentication()
async def get_online_user(
    request: Request,
    mango: mangodb_dependency,
    db: postgres_dependency,
):
    user = await UserQuery.one(db, request.user.id, True)
    online_users = []
    for friend in (*user.friend, *user.friend_by):
        if friend.id in main_connections.keys():
            online_users.append(friend)
    response = []
    for user in online_users:
        room_users = [user.id, request.user.id]
        room = await mango.find_one(Room, {"users.user_id": {"$all": room_users}})
        response.append(OnlineUserResponse(user=UserModel(**user.__dict__), room=room))

    return response
