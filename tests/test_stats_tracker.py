import pytest

from open_cups.stats_tracker import StatsTracker
from open_cups.types import UserSession, UserStatus


def test_status_history_snapshot_interval(monkeypatch: pytest.MonkeyPatch) -> None:
    current_time = 10.0

    def fake_time() -> float:
        return current_time

    monkeypatch.setattr("open_cups.stats_tracker.time.time", fake_time)

    unit = StatsTracker(
        dense_snapshot_interval_seconds=1,
        sparse_snapshot_interval_seconds=10,
        dense_interval_window_seconds=100,
        max_snapshot_count=10,
    )

    unit.record_status_snapshot(
        [UserSession(UserStatus.GREEN, 0.0), UserSession(UserStatus.YELLOW, 0.0)],
    )
    history = unit.status_history
    assert len(history) == 1
    assert history[0].counts[UserStatus.GREEN] == 1
    assert history[0].counts[UserStatus.YELLOW] == 1
    assert history[0].counts[UserStatus.RED] == 0
    assert history[0].counts[UserStatus.UNKNOWN] == 0

    current_time = 11.0
    unit.record_status_snapshot(
        [UserSession(UserStatus.GREEN, 0.0), UserSession(UserStatus.YELLOW, 0.0)],
    )
    history = unit.status_history
    assert len(history) == 2
    assert history[-1].counts[UserStatus.GREEN] == 1
    assert history[-1].counts[UserStatus.YELLOW] == 1


def test_status_history_trims_old_snapshots(monkeypatch: pytest.MonkeyPatch) -> None:
    current_time = 0.0

    def fake_time() -> float:
        return current_time

    monkeypatch.setattr("open_cups.stats_tracker.time.time", fake_time)

    unit = StatsTracker(
        dense_snapshot_interval_seconds=0,
        sparse_snapshot_interval_seconds=10,
        dense_interval_window_seconds=100,
        max_snapshot_count=2,
    )

    current_time = 1.0
    unit.record_status_snapshot([UserSession(UserStatus.GREEN, 0.0)])
    current_time = 2.0
    unit.record_status_snapshot([UserSession(UserStatus.YELLOW, 0.0)])
    current_time = 3.0
    unit.record_status_snapshot([UserSession(UserStatus.RED, 0.0)])

    history = unit.status_history
    assert len(history) == 2
    assert history[0].timestamp == 2.0
    assert history[1].timestamp == 3.0


def test_sparse_sampling_outside_dense_window(monkeypatch: pytest.MonkeyPatch) -> None:
    current_time = 0.0

    def fake_time() -> float:
        return current_time

    monkeypatch.setattr("open_cups.stats_tracker.time.time", fake_time)

    unit = StatsTracker(
        dense_snapshot_interval_seconds=1,
        sparse_snapshot_interval_seconds=5,
        dense_interval_window_seconds=10,
        max_snapshot_count=1000,
    )

    for i in range(30):
        current_time = float(i)
        unit.record_status_snapshot([UserSession(UserStatus.GREEN, 0.0)])

    history = unit.status_history
    last_time = 29.0
    dense_cutoff = last_time - 10.0

    dense_snapshots = [s for s in history if s.timestamp >= dense_cutoff]
    assert len(dense_snapshots) == 11
    assert dense_snapshots[0].timestamp == 19.0
    assert dense_snapshots[1].timestamp == 20.0
    assert dense_snapshots[-1].timestamp == 29.0

    sparse_snapshots = [s for s in history if s.timestamp < dense_cutoff]
    assert len(sparse_snapshots) == 4
    assert sparse_snapshots[0].timestamp == 0.0
    assert sparse_snapshots[1].timestamp == 5.0
    assert sparse_snapshots[2].timestamp == 10.0
    assert sparse_snapshots[3].timestamp == 15.0


def test_throw_away_samples_called_with_higher_frequency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current_time = 0.0

    def fake_time() -> float:
        return current_time

    monkeypatch.setattr("open_cups.stats_tracker.time.time", fake_time)

    unit = StatsTracker(
        dense_snapshot_interval_seconds=5,
        sparse_snapshot_interval_seconds=30,
        dense_interval_window_seconds=30,
        max_snapshot_count=1000,
    )

    for i in range(10):
        current_time = float(i)
        unit.record_status_snapshot([UserSession(UserStatus.GREEN, 0.0)])

    history = unit.status_history
    assert len(history) == 2
    assert history[0].timestamp == 0.0
    assert history[1].timestamp == 5.0
