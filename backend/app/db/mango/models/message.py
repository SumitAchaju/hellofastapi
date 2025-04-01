from odmantic import Field, Model
from pydantic import field_validator
from typing import Optional

from app.utils.date import formated_date

valid_message_type = ["text", "video", "image", "document", "links"]
valid_message_status = ["sent", "delivered", "seen"]


class Message(Model):
    room_id: str
    sender_id: int
    message_text: Optional[str] = None
    message_type: str = Field(default="text")
    created_at: str = Field(default_factory=formated_date)
    file_links: Optional[list[str]] = None
    status: str = Field(default="sent")
    seen_by: list[int] = Field(default=[])

    @field_validator("message_type")
    @classmethod
    def validate_message_type(cls, v: str):
        if v not in valid_message_type:
            raise ValueError(f"message type must be one of {valid_message_type}")
        return v

    @field_validator("status")
    @classmethod
    def validate_message_status(cls, v: str):
        if v not in valid_message_status:
            raise ValueError(f"message type must be one of {valid_message_status}")
        return v
