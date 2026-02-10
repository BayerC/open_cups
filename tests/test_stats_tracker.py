import pytest

from open_cups.stats_tracker import StatsTracker
from open_cups.types import UserSession, UserStatus


def test_status_history_snapshot_interval(monkeypatch: pytest.MonkeyPatch) -> None:
    current_time = 10.0

    def fake_time() -> float:
        return current_time

    monkeypatch.setattr("open_cups.stats_tracker.time.time", fake_time)

    unit = StatsTracker(snapshot_interval_seconds=1, max_snapshot_count=10)

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

    assert unit.session_start_time <= current_time


def test_status_history_trims_old_snapshots(monkeypatch: pytest.MonkeyPatch) -> None:
    current_time = 0.0

    def fake_time() -> float:
        return current_time

    monkeypatch.setattr("open_cups.stats_tracker.time.time", fake_time)

    unit = StatsTracker(snapshot_interval_seconds=0, max_snapshot_count=2)

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
