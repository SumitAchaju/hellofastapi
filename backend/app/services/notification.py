from app.api.v1.schemas.user import UserModel
from app.api.v1.schemas.notification import NotificationModel
from .websocket.connections import main_connections
from app.db.postgres.models.notification import Notification
from app.db.postgres.models.user import User


async def send_notification_to_user(notification: Notification, sender_user: User):
    if notification.receiver_id in main_connections:
        await main_connections[notification.receiver_id].send_notification(
            NotificationModel(**notification.__dict__),
            sender_user=UserModel(**sender_user.__dict__),
        )
        return True

    return False
