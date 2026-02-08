import uuid

import streamlit as st

from open_cups.application_state import ApplicationState
from open_cups.room import Question, Room
from open_cups.session_state import SessionState
from open_cups.user_status import UserStatus


class LobbyState:
    def __init__(
        self,
        application_state: ApplicationState,
        session_state: SessionState,
    ) -> None:
        self._application_state = application_state
        self._session_state = session_state

    def create_room(self) -> None:
        room_id = str(uuid.uuid4())
        self._application_state.create_room(room_id, self._session_state.session_id)

    def join_room(self, room_id: str) -> None:
        self._application_state.join_room(room_id, self._session_state.session_id)


class RoomState:
    def __init__(
        self,
        room: Room,
        session_id: str,
    ) -> None:
        self._room = room
        self._session_id = session_id

    @property
    def room_id(self) -> str:
        return self._room.room_id

    def get_room_participants(self) -> list[tuple[str, UserStatus]]:
        return list(self._room)

    def get_open_questions(self) -> list[Question]:
        return self._room.get_open_questions()


class HostState(RoomState):
    def __init__(self, room: Room, session_id: str) -> None:
        super().__init__(room, session_id)
        self._room.update_host_last_seen()

    def close_question(self, question_id: str) -> None:
        self._room.close_question(question_id)


class ClientState(RoomState):
    def __init__(self, room: Room, session_id: str) -> None:
        super().__init__(room, session_id)
        self._room.update_session(session_id)

    def get_user_status(self) -> UserStatus:
        return self._room.get_session_status(self._session_id)

    def set_user_status(self, status: UserStatus) -> None:
        self._room.set_session_status(self._session_id, status)

    def submit_question(self, text: str) -> None:
        self._room.add_question(self._session_id, text)

    def upvote_question(self, question_id: str) -> None:
        self._room.upvote_question(self._session_id, question_id)

    def has_voted(self, question: Question) -> bool:
        return self._session_id in question.voter_ids


class CleanupState:
    def __init__(
        self,
        application_state: ApplicationState,
        timeout_seconds: int,
    ) -> None:
        self._application_state = application_state
        self._timeout_seconds = timeout_seconds

    def cleanup_all(self) -> None:
        for room in self._application_state.rooms.values():
            room.remove_inactive_sessions(self._timeout_seconds)

        self._application_state.remove_rooms_with_inactive_hosts(
            self._timeout_seconds,
        )


class Context:
    def __init__(self) -> None:
        self.application_state: ApplicationState = self._get_application_state()
        self.session_state = SessionState()

    @staticmethod
    @st.cache_resource
    def _get_application_state() -> ApplicationState:
        return ApplicationState()


class StateProvider:
    def __init__(self) -> None:
        self.context = Context()

    def get_cleanup(self, timeout_seconds: int) -> CleanupState:
        return CleanupState(self.context.application_state, timeout_seconds)

    def get_current(self) -> LobbyState | HostState | ClientState:
        room = self.context.application_state.get_session_room(
            self.context.session_state.session_id,
        )
        if room is None:
            return LobbyState(
                self.context.application_state,
                self.context.session_state,
            )
        if room.is_host(self.context.session_state.session_id):
            return HostState(room, self.context.session_state.session_id)
        return ClientState(room, self.context.session_state.session_id)
