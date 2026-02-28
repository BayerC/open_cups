import pytest
from pytest_bdd import parsers, scenario, then, when
from streamlit.testing.v1 import AppTest

from tests.bdd.fixture import captured
from tests.bdd.test_helper import get_page_content, get_room_id


@pytest.fixture(autouse=True)
def freeze_time_to_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("time.time", lambda: 0)


def assert_session_count_in_room(
    context: dict[str, AppTest],
    expected_count: int,
) -> None:
    room_id = get_room_id(context["me"])
    assert captured.application_state is not None
    room = captured.application_state.rooms[room_id]
    session_count = len(list(room))
    assert session_count == expected_count


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


@then(parsers.parse('I should see info message "{info_message}"'))
def i_should_see_info_message(
    context: dict[str, AppTest],
    info_message: str,
) -> None:
    content = get_page_content(context["me"])
    assert info_message in content


@then("there should be more than zero participants in my room")
def there_should_be_more_than_zero_participants_in_my_room(
    context: dict[str, AppTest],
) -> None:
    content = get_page_content(context["me"])
    assert "No participants yet" not in content


@then("one user should be in the room")
def one_user_should_be_in_the_room(context: dict[str, AppTest]) -> None:
    assert_session_count_in_room(context, expected_count=1)


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


@when("the user removal timeout has passed")
def given_timeout_has_passed(
    context: dict[str, AppTest],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    time_to_pass = 5
    step_time = 2
    # patch this in any case to be independent of the production value
    monkeypatch.setattr("open_cups.app.USER_REMOVAL_TIMEOUT_SECONDS", 3)

    for current_time in range(0, time_to_pass, step_time):
        monkeypatch.setattr(
            "time.time",
            lambda current_time=current_time: current_time,
        )
        for user in context.values():
            user.run()


@then("no more users should be in the room")
def no_more_users_should_be_in_the_room(context: dict[str, AppTest]) -> None:
    assert_session_count_in_room(context, expected_count=0)
