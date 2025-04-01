from odmantic import Field, Model
from pydantic import field_validator
from typing import Optional
from app.utils.date import formated_date

valid_chatroom_type = ["group", "friend"]

class RoomUser(Model):
    user_id: int
    added_by: Optional[int] = None
    joined_at: str = Field(default_factory=formated_date)
    isAdmin: bool


class Room(Model):
    model_config = {
        "collection":"chat_room"
    }
    users: list[RoomUser]
    created_at: str = Field(default_factory=formated_date)
    type: str
    created_by: Optional[int] = None
    is_active: bool

    @field_validator("type")
    @classmethod
    def validate_roomtype(cls, v: str):
        if v not in valid_chatroom_type:
            raise ValueError(f"chat room type must be one of {valid_chatroom_type}")
        return v

