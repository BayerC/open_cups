import time
from collections.abc import Iterable
from dataclasses import dataclass

from open_cups.types import StatusSnapshot, UserSession, UserStatus


@dataclass
class Config:
    dense_snapshot_interval_seconds: int = 1
    sparse_snapshot_interval_seconds: int = 60
    dense_interval_window_seconds: int = 60
    max_snapshot_count: int = 1000

    def __post_init__(self) -> None:
        msgs = []

        if self.dense_snapshot_interval_seconds <= 0:
            msgs.append("dense_snapshot_interval must be > 0")
        if self.sparse_snapshot_interval_seconds <= 0:
            msgs.append("sparse_snapshot_interval must be > 0")
        if self.dense_interval_window_seconds < 0:
            msgs.append("dense_interval_window must be >= 0")
        if self.max_snapshot_count <= 0:
            msgs.append("max_snapshot_count must be > 0")
        if self.dense_interval_window_seconds < self.dense_snapshot_interval_seconds:
            msgs.append("dense_interval_window must be >= dense_snapshot_interval")
        if self.dense_snapshot_interval_seconds > self.sparse_snapshot_interval_seconds:
            msgs.append("dense_snapshot_interval must be <= sparse_snapshot_interval")

        if msgs:
            raise ValueError(", ".join(msgs))


class StatsTracker:
    def __init__(
        self,
        config: Config,
    ) -> None:
        self._status_history: list[StatusSnapshot] = []
        self._config = config

    def record_status_snapshot(self, user_sessions: Iterable[UserSession]) -> None:
        current_time = time.time()

        if self._status_history:
            last_snapshot_time = self._status_history[-1].timestamp
            if (
                current_time - last_snapshot_time
                < self._config.dense_snapshot_interval_seconds
            ):
                return

        self._status_history.append(create_snapshot(user_sessions))

        dense_cutoff_time = current_time - self._config.dense_interval_window_seconds

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
                    >= self._config.sparse_snapshot_interval_seconds
                ):
                    sparse_snapshots.append(snapshot)
                    last_kept_time = snapshot.timestamp

        self._status_history = sparse_snapshots + dense_snapshots

        if len(self._status_history) > self._config.max_snapshot_count:
            excess_count = len(self._status_history) - self._config.max_snapshot_count
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
