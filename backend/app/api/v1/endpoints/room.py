from fastapi import APIRouter, Request, HTTPException
from app.db.postgres.dependency import postgres_dependency
from app.db.mango.dependency import mangodb_dependency
from app.api.permission import require_authentication
from app.db.mango.models.room import Room
from app.db.mango.models.message import Message
from sqlalchemy import select
from app.db.postgres.models.user import User
from app.api.v1.schemas.message import ChatHistoryResponse
from app.api.v1.schemas.user import UserModel
from bson import ObjectId
from bson.errors import InvalidId
from app.utils.date import datetime_format
from datetime import datetime


router = APIRouter(prefix="/room", tags=["room"])


@router.get("/")
@require_authentication()
async def get_rooms(request: Request, mango: mangodb_dependency):
    rooms = await mango.find(Room, {"users.user_id": {"$eq": request.user.id}})
    return rooms


@router.get("/history/", response_model=list[ChatHistoryResponse])
@require_authentication()
async def get_chat_history(
    request: Request,
    mangodb: mangodb_dependency,
    db: postgres_dependency,
):
    rooms = await mangodb.find(Room, {"users.user_id": {"$eq": request.user.id}})
    history_user_id = []
    history_user_room = []
    for room in rooms:
        room_data = {"room": room, "users": []}
        for usr in room.users:
            if usr.user_id != request.user.id:
                history_user_id.append(usr.user_id)
                room_data["users"].append(usr.user_id)
        history_user_room.append(room_data)

    history_user_query = select(User).filter(User.id.in_(history_user_id))
    history_user = (await db.scalars(history_user_query)).unique().all()

    results = []

    for room in history_user_room:
        messages = await mangodb.find(
            Message,
            {"room_id": str(room["room"].id)},
            limit=5,
            sort=Message.id.desc(),
        )
        unseen_msg_quantity = 0
        for msg in messages:
            if msg.status != "seen" and msg.sender_id != request.user.id:
                unseen_msg_quantity += 1

        msg = messages[0] if messages else None

        result = ChatHistoryResponse(
            room=room["room"],
            users=[],
            message=msg,
            quantity=unseen_msg_quantity,
        )
        for room_usr in room["users"]:
            for usr in history_user:
                if usr.id == room_usr:
                    result.users.append(UserModel(**usr.__dict__))
                    break
        results.append(result)

    sorted_results = sorted(
        results,
        key=lambda chat_object: (
            datetime.strptime(chat_object.message.created_at, datetime_format)
            if chat_object.message is not None
            else datetime.strptime(chat_object.room.created_at, datetime_format)
        ),
        reverse=True,
    )

    return sorted_results


@router.get("/initialRoom/")
@require_authentication()
async def get_initial_room(request: Request, mango: mangodb_dependency):
    room = await mango.find_one(
        Room, {"users.user_id": request.user.id}, sort=Room.created_at.desc()
    )
    return room


@router.get("/room/{room_id}/")
@require_authentication()
async def get_room_by_id(request: Request, room_id: str, mango: mangodb_dependency):
    try:
        room = await mango.find_one(Room, {"_id": ObjectId(room_id)})
        return room
    except InvalidId:
        raise HTTPException(detail="invalid id", status_code=400)


@router.get("/friend/{room_id}/")
@require_authentication()
async def get_room_friends(
    request: Request, mangodb: mangodb_dependency, db: postgres_dependency, room_id: str
):
    try:
        room_object_id = ObjectId(room_id)
    except InvalidId:
        raise HTTPException(detail="invalid room id", status_code=403)

    room = await mangodb.find_one(Room, Room.id == room_object_id)
    if request.user.id not in [usr.user_id for usr in room.users]:
        raise HTTPException(detail="user not in room", status_code=403)
    friend_user_id = [
        usr.user_id for usr in room.users if usr.user_id != request.user.id
    ]

    friend_users_query = select(User).filter(User.id.in_(friend_user_id))
    friend_users = (await db.scalars(friend_users_query)).unique().all()
    if room.type == "friend":
        if friend_users:
            return friend_users[0]
        else:
            if room.is_active:
                room.is_active = False
                await mangodb.save(room)
            raise HTTPException(detail="friend not found", status_code=404)

    return friend_users
