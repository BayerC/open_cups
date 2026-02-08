from typing import TYPE_CHECKING

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from open_cups.app import get_statistics_data_frame
from open_cups.state_provider import Context, RoomState

if TYPE_CHECKING:
    from open_cups.application_state import ApplicationState


def run_wrapper() -> None:
    from open_cups.app import run  # noqa: PLC0415

    run()


@pytest.fixture
def context() -> dict[str, AppTest]:
    application = AppTest.from_function(run_wrapper)
    application.run()
    return {"me": application}


class CapturedData:
    def __init__(self) -> None:
        self.room_data: dict[str, pd.DataFrame] = {}
        self.application_state: None | ApplicationState = None


captured = CapturedData()


@pytest.fixture(autouse=True)
def capture_stats(monkeypatch: pytest.MonkeyPatch) -> None:
    captured.room_data.clear()
    original_func = get_statistics_data_frame

    def capture_wrapper(room: RoomState) -> pd.DataFrame:
        df = original_func(room)
        captured.room_data[room.room_id] = df
        return df

    monkeypatch.setattr(
        "open_cups.app.get_statistics_data_frame",
        capture_wrapper,
    )


@pytest.fixture(autouse=True)
def capture_application_state(monkeypatch: pytest.MonkeyPatch) -> None:
    original_init = Context.__init__

    def wrapped_init(context: Context) -> None:
        original_init(context)
        captured.application_state = context.application_state

    monkeypatch.setattr(Context, "__init__", wrapped_init)
