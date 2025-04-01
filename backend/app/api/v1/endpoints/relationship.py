from fastapi import APIRouter, Request, HTTPException

from app.api.permission import require_authentication
from app.db.postgres.dependency import postgres_dependency
from app.db.mango.dependency import mangodb_dependency
from app.db.postgres.models.notification import (
    Notification,
    NotificationType,
    json_data_friend_request,
)
from app.services.notification import send_notification_to_user
from app.extra.query import UserQuery, NotificationQuery
from app.services.websocket.connections import room_connections
from app.services.user import (
    get_user_for_add,
)
from app.services.room import create_room, change_room_status

router = APIRouter(prefix="/relation", tags=["relationship"])


@router.get("/accept/{user_id}/")
@require_authentication()
async def accept_friend_request(
    request: Request, db: postgres_dependency, mango: mangodb_dependency, user_id: int
):
    main_user, second_user, is_already_friend = await get_user_for_add(
        db, main_user_id=request.user.id, second_user_id=user_id, operation="friend"
    )

    if is_already_friend:
        raise HTTPException(
            detail="user is already in your friend list", status_code=403
        )

    if second_user in main_user.blocked_user:
        raise HTTPException(
            detail="unblock this user to add to friend list",
            status_code=403,
        )

    if second_user not in main_user.requested_by:
        raise HTTPException(detail="request this user to add friend", status_code=403)

    main_user.requested_by.remove(second_user)
    main_user.friend.append(second_user)

    request_notification = await NotificationQuery(
        db,
        {
            "sender_id": second_user.id,
            "receiver_id": main_user.id,
            "notification_type": NotificationType.FRIEND_REQUEST,
        },
    ).get_by_jsonB_filter({"is_active": True})

    if request_notification is None:
        raise HTTPException(detail="invalid request", status_code=400)

    request_notification.extra_data.update({"is_accepted": True})
    request_notification.extra_data.update({"is_active": False})

    add_friend_notification = Notification(
        sender_id=main_user.id,
        receiver_id=second_user.id,
        notification_type=NotificationType.FRIEND_REQUEST_ACCEPTED,
        message=f"{main_user.first_name} {main_user.last_name} accepted your friend request",
    )
    db.add(add_friend_notification)

    await db.commit()
    await db.refresh(add_friend_notification)

    await send_notification_to_user(add_friend_notification, main_user)

    await create_room(
        mango,
        main_user_id=main_user.id,
        second_user_id=second_user.id,
        room_type="friend",
    )

    return main_user


@router.get("/request/{user_id}/")
@require_authentication()
async def request_user_for_friend(
    request: Request, db: postgres_dependency, user_id: int
):
    main_user, second_user, is_already_requested = await get_user_for_add(
        db,
        main_user_id=request.user.id,
        second_user_id=user_id,
        operation="requested_user",
    )

    if is_already_requested:
        return main_user

    if second_user in main_user.blocked_user:
        raise HTTPException(
            detail="unblock this user to request this user",
            status_code=403,
        )

    if second_user in main_user.friend:
        raise HTTPException(
            detail="user is already in your friend list",
            status_code=403,
        )

    main_user.requested_user.append(second_user)

    request_notification = Notification(
        sender_id=main_user.id,
        receiver_id=second_user.id,
        notification_type=NotificationType.FRIEND_REQUEST,
        message=f"{main_user.first_name} {main_user.last_name} send you friend request",
        extra_data=json_data_friend_request,
    )

    db.add(request_notification)
    await db.commit()
    await db.refresh(request_notification)

    await send_notification_to_user(request_notification, main_user)

    return main_user


@router.get("/cancelrequest/{user_id}/")
@require_authentication()
async def cancel_request(request: Request, db: postgres_dependency, user_id: int):
    main_user = await UserQuery.one(db, request.user.id)
    second_user = await UserQuery.one(db, user_id, False)

    if second_user not in main_user.requested_user:
        raise HTTPException(
            detail="user is not in your requested list", status_code=403
        )

    main_user.requested_user.remove(second_user)

    request_notification = await NotificationQuery(
        db,
        {
            "sender_id": main_user.id,
            "receiver_id": second_user.id,
            "notification_type": NotificationType.FRIEND_REQUEST,
        },
    ).get_by_jsonB_filter({"is_active": True}, all=True)

    if request_notification is None:
        raise HTTPException(detail="invalid request", status_code=400)

    for noti in request_notification:
        noti.extra_data.update({"is_canceled": True})
        noti.extra_data.update({"is_active": False})

    cancel_notification = Notification(
        sender_id=main_user.id,
        receiver_id=second_user.id,
        notification_type=NotificationType.FRIEND_REQUEST_CANCELED,
        message=f"{main_user.first_name} {main_user.last_name} canceled friend request",
        linked_notification_id=(
            request_notification[0].id if request_notification else None
        ),
    )

    db.add(cancel_notification)
    await db.commit()
    await db.refresh(cancel_notification)

    await send_notification_to_user(cancel_notification, main_user)

    return main_user


@router.get("/unfriend/{user_id}/")
@require_authentication()
async def unfriend_user(
    request: Request, db: postgres_dependency, mangodb: mangodb_dependency, user_id: int
):
    main_user, second_user, is_not_friend = await get_user_for_add(
        db, main_user_id=request.user.id, second_user_id=user_id, operation="unfriend"
    )

    if is_not_friend:
        raise HTTPException(detail="user is not in your friend list", status_code=403)

    if second_user in main_user.friend:
        main_user.friend.remove(second_user)
    elif second_user in main_user.friend_by:
        main_user.friend_by.remove(second_user)
    else:
        return main_user

    unfriend_notificaiton = Notification(
        sender_id=main_user.id,
        receiver_id=second_user.id,
        notification_type=NotificationType.UNFRIEND,
        message=f"{main_user.first_name} {main_user.last_name} unfriend you",
    )
    db.add(unfriend_notificaiton)
    await db.commit()
    await db.refresh(unfriend_notificaiton)
    await send_notification_to_user(unfriend_notificaiton, main_user)

    # close the room if connected and deactivate the room
    room = await change_room_status(mangodb, main_user.id, second_user.id, False)
    if room:
        if str(room.id) in room_connections:
            await room_connections[str(room.id)].close_room()

    return main_user


@router.get("/block/{user_id}/")
@require_authentication()
async def block_user(
    request: Request, db: postgres_dependency, mangodb: mangodb_dependency, user_id: int
):
    main_user, second_user, is_already_blocked = await get_user_for_add(
        db,
        main_user_id=request.user.id,
        second_user_id=user_id,
        operation="blocked_user",
    )

    if is_already_blocked:
        return main_user

    main_user.blocked_user.append(second_user)

    block_notification = Notification(
        sender_id=main_user.id,
        receiver_id=second_user.id,
        notification_type=NotificationType.BLOCK_FRIEND,
        message=f"{main_user.first_name} {main_user.last_name} blocked you",
    )
    db.add(block_notification)

    await db.commit()
    await db.refresh(block_notification)

    await send_notification_to_user(block_notification, main_user)

    # close the room if connected and deactivate the room
    room = await change_room_status(mangodb, main_user.id, second_user.id, False)
    if room:
        if str(room.id) in room_connections:
            print("closed room: ", room.id)
            await room_connections[str(room.id)].close_room()

    return main_user


@router.get("/unblock/{user_id}/")
@require_authentication()
async def unblock_user(
    request: Request, db: postgres_dependency, mangodb: mangodb_dependency, user_id: int
):
    main_user = await UserQuery.one(db, request.user.id)
    second_user = await UserQuery.one(db, user_id, False)

    if second_user not in main_user.blocked_user:
        raise HTTPException(detail="user is not in your blocked list", status_code=403)

    main_user.blocked_user.remove(second_user)
    unblock_notification = Notification(
        sender_id=main_user.id,
        receiver_id=second_user.id,
        notification_type=NotificationType.UNBLOCK_FRIEND,
        message=f"{main_user.first_name} {main_user.last_name} unblocked you",
    )
    db.add(unblock_notification)
    await db.commit()
    await db.refresh(unblock_notification)

    await send_notification_to_user(unblock_notification, main_user)

    if second_user in main_user.friend or second_user in main_user.friend_by:
        if second_user not in main_user.blocked_by:
            await change_room_status(mangodb, main_user.id, second_user.id, True)

    return main_user
