from typing import TypedDict

from bson import ObjectId

from app.db.mango.session import mango_sessionmanager
from app.db.mango.models.message import Message


NewMessageDataType = TypedDict(
    "NewMessageDataType", {"room_id": str, "message_text": str, "sender_id": int}
)


async def save_new_message(msg: NewMessageDataType):
    async with mango_sessionmanager.engine.session() as session:
        new_message = Message(**msg)
        return await session.save(new_message)


async def change_msg_status(
    msg_id_list: list[str],
    msg_status: str,
    sender_user_id: int,
) -> list[Message]:
    msg_object_id_list = [ObjectId(msg_id) for msg_id in msg_id_list]
    async with mango_sessionmanager.engine.session() as session:
        messages = await session.find(Message, {"_id": {"$in": msg_object_id_list}})
        for msg in messages:
            if msg.sender_id != sender_user_id:
                msg.status = msg_status
        await session.save_all(messages)

        return messages
