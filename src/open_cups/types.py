import time
from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum


class UserStatus(Enum):
    UNKNOWN = "Unknown"
    GREEN = "🟢 Green"
    YELLOW = "🟡 Yellow"
    RED = "🔴 Red"

    def caption(self) -> str:
        captions = {
            UserStatus.UNKNOWN: "Not decided yet",
            UserStatus.GREEN: "Following easily",
            UserStatus.YELLOW: "Need more explanation",
            UserStatus.RED: "Cannot follow",
        }
        return captions[self]


@dataclass
class UserSession:
    status: UserStatus
    last_seen: float


@dataclass
class Question:
    id: str
    text: str
    voter_ids: set[str]

    @property
    def vote_count(self) -> int:
        return len(self.voter_ids)


@dataclass
class StatusSnapshot:
    timestamp: float
    counts: dict[UserStatus, int]

    @classmethod
    def from_user_sessions(
        cls,
        user_sessions: Iterable[UserSession],
    ) -> "StatusSnapshot":
        snapshot = cls(
            timestamp=time.time(),
            counts={
                UserStatus.GREEN: 0,
                UserStatus.YELLOW: 0,
                UserStatus.RED: 0,
                UserStatus.UNKNOWN: 0,
            },
        )

        for user_session in user_sessions:
            snapshot.counts[user_session.status] += 1

        return snapshot
