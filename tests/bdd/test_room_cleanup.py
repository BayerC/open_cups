import pytest
from pytest_bdd import parsers, scenario, then, when
from streamlit.testing.v1 import AppTest

from tests.bdd.test_helper import get_info_content, get_page_content


@pytest.fixture(autouse=True)
def freeze_time_to_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("open_cups.room.time.time", lambda: 0)


@scenario(
    "features/room_cleanup.feature",
    "Disconnected user is removed from user status after timeout",
)
def test_disconnected_user_is_removed_from_user_status_after_timeout() -> None:
    pass


@scenario(
    "features/room_cleanup.feature",
    "Room host disconnects",
)
def test_room_host_disconnects() -> None:
    pass


@then("there should be 1 participant in my room")
def there_should_be_1_participant_in_my_room(
    context: dict[str, AppTest],
) -> None:
    content = get_page_content(context["me"])
    assert "Number of participants: 1" in content


@when("the second user closes their session")
def second_user_closes_their_session(context: dict[str, AppTest]) -> None:
    del context["second_user"]  # prevent running second user further


@when("I close my session")
def i_close_my_session(context: dict[str, AppTest]) -> None:
    del context["me"]  # prevent running me further


@then("the second user should be on the room selection screen")
def second_user_should_be_on_room_selection_screen(context: dict[str, AppTest]) -> None:
    assert len(context["second_user"].title) == 1
    assert context["second_user"].title[0].value == "Welcome to OpenCups"


@when("a given timeout has passed")
def given_timeout_has_passed(
    context: dict[str, AppTest],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    time_to_pass = 5
    step_time = 2
    # patch this in any case to be independent of the production value
    monkeypatch.setattr("open_cups.app.USER_REMOVAL_TIMEOUT_SECONDS", 3)

    for current_time in range(0, time_to_pass, step_time):
        for user in context.values():
            monkeypatch.setattr(
                "open_cups.room.time.time",
                lambda current_time=current_time: current_time,
            )
            user.run()


@then(parsers.parse('I should see info message "{info_message}"'))
def i_should_see_info_message(
    context: dict[str, AppTest],
    info_message: str,
) -> None:
    content = get_info_content(context["me"])
    assert info_message in content
