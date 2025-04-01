from pydantic import BaseModel

from .user import UserModel
from app.db.postgres.models.notification import NotificationType


class NotificationModel(BaseModel):
    id: int
    is_read: bool
    created_at: str
    read_at: str | None = None
    notification_type: NotificationType
    message: str
    sender_id: int
    receiver_id: int
    extra_data: dict
    linked_notification_id: int | None = None
    sender_user: UserModel | None = None
    receiver_user: UserModel | None = None
    linked_notification: "NotificationModel | None" = None


class NotificationPatchModel(BaseModel):
    is_read: bool | None = None
    is_active: bool | None = None
