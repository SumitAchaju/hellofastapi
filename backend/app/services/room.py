from odmantic.session import AIOSession

from app.db.mango.models.room import Room


async def create_room(
    mangodb: AIOSession, main_user_id: int, second_user_id: int, room_type: str
) -> Room:
    room_users = [main_user_id, second_user_id]
    query = {"users.user_id": {"$all": room_users}}
    room = await mangodb.find_one(Room, query)

    if not room:
        new_room = Room(
            users=[
                {"user_id": main_user_id, "isAdmin": True},
                {"user_id": second_user_id, "isAdmin": True},
            ],
            type=room_type,
            is_active=True,
        )
        return new_room

    room.is_active = True

    return await mangodb.save(room)


async def change_room_status(
    mangodb: AIOSession, main_user, second_user, status: bool
) -> Room | None:
    room_users = [main_user, second_user]
    query = {"users.user_id": {"$all": room_users}}
    room = await mangodb.find_one(Room, query)
    if room:
        if room.is_active != status:
            room.is_active = status
            await mangodb.save(room)
    return room
