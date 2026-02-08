from open_cups.room import Room
from open_cups.thread_safe_dict import ThreadSafeDict
from open_cups.user_status import UserStatus


class ApplicationState:
    """Application-wide shared state."""

    def __init__(self) -> None:
        self.rooms: ThreadSafeDict[Room] = ThreadSafeDict()

    def get_session_room(self, session_id: str) -> Room | None:
        for room in self.rooms.values():
            if room.has_session(session_id):
                return room
        return None

    def create_room(self, room_id: str, session_id: str) -> None:
        room = Room(room_id, session_id)
        self.rooms[room_id] = room

    def join_room(self, room_id: str, session_id: str) -> None:
        if room_id not in self.rooms:
            message = f"Room {room_id} does not exist"
            raise ValueError(message)
        self.rooms[room_id].set_session_status(session_id, UserStatus.UNKNOWN)

    def remove_rooms_with_inactive_hosts(self, timeout_seconds: int) -> None:
        inactive_room_ids = [
            room_id
            for room_id, room in self.rooms.items()
            if room.is_host_inactive(timeout_seconds)
        ]
        for room_id in inactive_room_ids:
            del self.rooms[room_id]
