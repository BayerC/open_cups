import time
from collections.abc import Iterable

from open_cups.types import StatusSnapshot, UserSession, UserStatus


class StatsTracker:
    def __init__(
        self,
        dense_snapshot_interval_seconds: int,
        sparse_snapshot_interval_seconds: int,
        dense_interval_window_seconds: int,
        max_snapshot_count: int,
    ) -> None:
        self._status_history: list[StatusSnapshot] = []
        self._dense_snapshot_interval_seconds = dense_snapshot_interval_seconds
        self._sparse_snapshot_interval_seconds = sparse_snapshot_interval_seconds
        self._dense_interval_window_seconds = dense_interval_window_seconds
        self._max_snapshot_count = max_snapshot_count

    def record_status_snapshot(self, user_sessions: Iterable[UserSession]) -> None:
        current_time = time.time()

        if self._status_history:
            last_snapshot_time = self._status_history[-1].timestamp
            if (
                current_time - last_snapshot_time
                < self._dense_snapshot_interval_seconds
            ):
                return

        self._status_history.append(create_snapshot(user_sessions))

        dense_cutoff_time = current_time - self._dense_interval_window_seconds

        dense_snapshots = [
            s for s in self._status_history if s.timestamp >= dense_cutoff_time
        ]
        sparse_candidates = [
            s for s in self._status_history if s.timestamp < dense_cutoff_time
        ]

        sparse_snapshots = []
        if sparse_candidates:
            last_kept_time = sparse_candidates[0].timestamp
            sparse_snapshots.append(sparse_candidates[0])

            for snapshot in sparse_candidates[1:]:
                if (
                    snapshot.timestamp - last_kept_time
                    >= self._sparse_snapshot_interval_seconds
                ):
                    sparse_snapshots.append(snapshot)
                    last_kept_time = snapshot.timestamp

        self._status_history = sparse_snapshots + dense_snapshots

        if len(self._status_history) > self._max_snapshot_count:
            excess_count = len(self._status_history) - self._max_snapshot_count
            del self._status_history[:excess_count]

    @property
    def status_history(self) -> list[StatusSnapshot]:
        return self._status_history


def create_snapshot(user_sessions: Iterable[UserSession]) -> StatusSnapshot:
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

    return snapshot
