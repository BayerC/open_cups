import time
from collections.abc import Iterable

from lecture_feedback.types import StatusSnapshot, UserSession, UserStatus


class StatsTracker:
    def __init__(self, snapshot_interval_seconds: int, max_snapshot_count: int) -> None:
        self._status_history: list[StatusSnapshot] = []
        self._snapshot_interval_seconds = snapshot_interval_seconds
        self._max_snapshot_count = max_snapshot_count
        self._session_start_time = time.time()

    def record_status_snapshot(self, user_sessions: Iterable[UserSession]) -> None:
        if self._status_history:
            last_snapshot_time = self._status_history[-1].timestamp
            if time.time() - last_snapshot_time < self._snapshot_interval_seconds:
                return

        snapshot = StatusSnapshot(
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

        self._status_history.append(snapshot)
        if len(self._status_history) > self._max_snapshot_count:
            excess_count = len(self._status_history) - self._max_snapshot_count
            del self._status_history[:excess_count]

    @property
    def status_history(self) -> list[StatusSnapshot]:
        return self._status_history

    @property
    def session_start_time(self) -> float:
        return self._session_start_time
