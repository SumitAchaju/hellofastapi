from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    messages,
    room,
    user,
    notification,
    websocket,
    relationship,
)

v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(auth.router)
v1_router.include_router(messages.router)
v1_router.include_router(room.router)
v1_router.include_router(user.router)
v1_router.include_router(notification.router)
v1_router.include_router(websocket.router)
v1_router.include_router(relationship.router)
