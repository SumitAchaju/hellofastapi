from .main_manager import MainConnectionManager
from .room_manager import RoomManager

main_connections: dict[int, MainConnectionManager]
room_connections: dict[str, RoomManager]
