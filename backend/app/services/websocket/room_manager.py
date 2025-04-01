import json

from fastapi import WebSocketException, WebSocket
from starlette import status

from app.api.v1.schemas.user import UserModel
from ..message import save_new_message, change_msg_status
from ..auth import verify_ws_token
from app.db.mango.session import mango_sessionmanager
from app.db.mango.models.room import Room
from app.db.mango.models.message import Message

from bson import ObjectId
from bson.errors import InvalidId
from app.api.v1.schemas.websocket import (
    WebsocketRecievedMessage,
    WebSocketResponse,
    EventType,
)
from .connections import room_connections, main_connections
from app.core.logger import logger


class RoomManager:
    def __init__(self, room_name: str):
        self.room = room_name
        self.connected_users: dict[int, WebSocket] = {}
        self.room_users: list[int] = []

    @classmethod
    async def connect(
        cls, websocket: WebSocket, room_id: str
    ) -> tuple["RoomManager", int]:
        await websocket.accept()
        room = await cls.check_room(room_id)
        if not room:
            raise WebSocketException(
                code=status.WS_1003_UNSUPPORTED_DATA, reason="Invalid room id"
            )

        token = await websocket.receive_text()

        user_id = verify_ws_token(token)
        if room_id in room_connections:
            room_connections[room_id].connected_users[user_id] = websocket
        else:
            new_room = cls(room_id)
            new_room.room_users = [usr.user_id for usr in room.users]
            new_room.connected_users[user_id] = websocket
            room_connections[room_id] = new_room

        return room_connections[room_id], user_id

    @staticmethod
    def disconnect(room_id: str, user_id: int):
        room = room_connections.get(room_id)
        if room:
            room.connected_users.pop(user_id, None)
            if not room.connected_users:
                room.delete_room()

    async def close_room(self):
        for key in self.connected_users.copy().keys():
            await self.connected_users[key].close()
        self.delete_room()

    def delete_room(self):
        if self.room in room_connections:
            del room_connections[self.room]

    async def handle_msg(self, data: str):
        try:
            msg = WebsocketRecievedMessage(**(json.loads(data)))
        except ValueError as e:
            print(e.__traceback__)
            return None

        if msg.event_type == "new_message":
            message = await save_new_message(
                {
                    "room_id": msg.room_id,
                    "message_text": msg.data.message_text,
                    "sender_id": msg.sender_user.id,
                }
            )
            await self.broadcast([message], msg.event_type, msg.sender_user)

        elif msg.event_type == "change_message_status":
            print("change_message_status", msg)

            message = await change_msg_status(
                msg.data.message_id_list, msg.data.status, msg.sender_user.id
            )
            await self.broadcast(message, msg.event_type, msg.sender_user)

    async def broadcast(
        self, msg: list[Message], event_type: EventType, sender_user: UserModel
    ):
        msg_response = WebSocketResponse(
            event_type=event_type, data=msg, sender_user=sender_user
        )

        # send a msg to online user who not connected in room.
        for user in [
            usr for usr in self.room_users if usr not in self.connected_users.keys()
        ]:
            if user in main_connections.keys():
                await main_connections[user].send_msg(msg_response)

        for websocket in self.connected_users.values():
            await websocket.send_text(msg_response.model_dump_json())

    @staticmethod
    async def check_room(room_id: str):
        try:
            room_object_id = ObjectId(room_id)
        except InvalidId:
            return None
        async with mango_sessionmanager.engine.session() as mangodb:
            room = await mangodb.find_one(Room, Room.id == room_object_id)
            if room:
                return room if room.is_active else None
            else:
                return None
