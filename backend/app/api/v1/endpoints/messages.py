from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Request, HTTPException
from app.api.permission import require_authentication
from app.db.mango.dependency import mangodb_dependency
from app.db.mango.models.message import Message
from app.db.mango.models.room import Room

router = APIRouter(prefix="/message", tags=["messages"])


@router.get("/msg/{room_id}/")
@require_authentication()
async def get_room_messages(
    mango: mangodb_dependency,
    request: Request,
    room_id: str,
    offset: int,
    limit: int,
):

    try:
        room_object_id = ObjectId(room_id)
        room = await mango.find_one(Room, {"_id": room_object_id})
        if not room:
            raise HTTPException(detail="Cannot find room", status_code=403)
    except InvalidId:
        raise HTTPException(detail="invalid room id", status_code=403)

    if request.user.id not in [usr.user_id for usr in room.users]:
        raise HTTPException(detail="user not in room", status_code=403)

    messages = await mango.find(
        Message,
        {"room_id": room_id},
        limit=limit,
        skip=offset,
        sort=Message.id.desc(),
    )
    messages.reverse()
    return messages
