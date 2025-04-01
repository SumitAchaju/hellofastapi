from pydantic import BaseModel
from app.db.mango.models.room import Room
from .user import UserModel
from app.db.mango.models.message import Message


class ChatHistoryResponse(BaseModel):
    users: list[UserModel]
    room: Room
    message: Message | None = None
    quantity: int


class OnlineUserResponse(BaseModel):
    user: UserModel
    room: Room
