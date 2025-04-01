from pydantic import BaseModel, Field

from app.db.postgres.models.notification import NotificationType
from app.db.postgres.schemas.user import UserSchema


class NotificationSchema(BaseModel):
    table_name = "notifications"

    id: int
    is_read: bool = False
    created_at: str
    read_at: str | None = None
    notification_type: NotificationType
    message: str
    sender_id: int
    receiver_id: int
    extra_data: dict = Field(default={})

    linked_notification_id: int | None = None

    sender_user: UserSchema
    receiver_user: UserSchema
    linked_notification: "NotificationSchema | None" = None
