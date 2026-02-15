import bisect
import time
from collections.abc import Iterable
from dataclasses import dataclass

from open_cups.types import StatusSnapshot, UserSession, UserStatus


@dataclass
class Config:
    dense_snapshot_interval_seconds: int = 1
    dense_sampling_window_seconds: int = 60
    sparse_snapshot_interval_seconds: int = 60
    max_sparse_snapshot_count: int = 1000

    def __post_init__(self) -> None:
        msgs = []

        if self.dense_snapshot_interval_seconds <= 0:
            msgs.append("dense_snapshot_interval must be > 0")
        if self.sparse_snapshot_interval_seconds <= 0:
            msgs.append("sparse_snapshot_interval must be > 0")
        if self.dense_sampling_window_seconds < 0:
            msgs.append("dense_interval_window must be >= 0")
        if self.max_sparse_snapshot_count <= 0:
            msgs.append("max_sparse_snapshot_count must be > 0")
        if self.dense_sampling_window_seconds < self.dense_snapshot_interval_seconds:
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
        self._dense_status_history: list[StatusSnapshot] = []
        self._sparse_status_history: list[StatusSnapshot] = []
        self._config = config

    def record_status_snapshot(self, user_sessions: Iterable[UserSession]) -> None:
        current_time = time.time()

        if not self._want_to_record_snapshot(current_time):
            return

        self._dense_status_history.append(create_snapshot(user_sessions))

        snapshots_to_move = self._extract_old_snapshots_from_dense_history(current_time)
        self._append_to_sparse_history(snapshots_to_move)
        self._prune_sparse_history_if_needed()

    def _want_to_record_snapshot(self, current_time: float) -> bool:
        if not self._dense_status_history:
            return True

        last_snapshot_time = self._dense_status_history[-1].timestamp
        return (
            current_time - last_snapshot_time
            >= self._config.dense_snapshot_interval_seconds
        )

    def _extract_old_snapshots_from_dense_history(
        self,
        current_time: float,
    ) -> list[StatusSnapshot]:
        dense_cutoff_time = current_time - self._config.dense_sampling_window_seconds

        split_index = bisect.bisect_left(
            self._dense_status_history,
            dense_cutoff_time,
            key=lambda s: s.timestamp,
        )
        old_snapshots = self._dense_status_history[:split_index]
        self._dense_status_history = self._dense_status_history[split_index:]
        return old_snapshots

    def _append_to_sparse_history(self, snapshots: list[StatusSnapshot]) -> None:
        for snapshot in snapshots:
            if not self._sparse_status_history:
                self._sparse_status_history.append(snapshot)
            else:
                last_sparse_time = self._sparse_status_history[-1].timestamp
                if (
                    snapshot.timestamp - last_sparse_time
                    >= self._config.sparse_snapshot_interval_seconds
                ):
                    self._sparse_status_history.append(snapshot)

    def _prune_sparse_history_if_needed(self) -> None:
        excess_count = (
            len(self._sparse_status_history) - self._config.max_sparse_snapshot_count
        )
        if excess_count <= 0:
            return

        del self._sparse_status_history[:excess_count]

    @property
    def status_history(self) -> list[StatusSnapshot]:
        return self._sparse_status_history + self._dense_status_history


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
