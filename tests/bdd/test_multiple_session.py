from pytest_bdd import parsers, scenario, then, when
from streamlit.testing.v1 import AppTest

from open_cups.user_status import UserStatus
from tests.bdd.fixture import captured, run_wrapper
from tests.bdd.test_helper import get_room_id

STATUS_MAP = {status.name.lower(): status.value for status in UserStatus}


@scenario("features/multiple_session.feature", "Second user joins with room URL")
def test_second_user_joins_with_room_url() -> None:
    pass


@scenario("features/multiple_session.feature", "Two users in one room share statistics")
def test_two_users_share_statistics() -> None:
    pass


@scenario(
    "features/multiple_session.feature",
    "Three users in two separate rooms maintain independent statistics",
)
def test_three_users_in_two_separate_rooms_maintain_independent_statistics() -> None:
    pass


@when("a second user wants to join with invalid URL")
def second_user_wants_to_join_with_invalid_url(context: dict[str, AppTest]) -> None:
    context["second_user"] = AppTest.from_function(run_wrapper)
    context["second_user"].query_params["room_id"] = "INVALID"
    context["second_user"].run()


@then(parsers.parse('the second user should see warning message "{error_message}"'))
def second_user_should_see_warning_message(
    context: dict[str, AppTest],
    error_message: str,
) -> None:
    assert len(context["second_user"].error) == 1
    assert context["second_user"].error[0].value == error_message


@when("a third user wants to join with my room URL")
def third_user_wants_to_join_with_my_room_url(context: dict[str, AppTest]) -> None:
    context["third_user"] = AppTest.from_function(run_wrapper)
    assert "room_id" in context["me"].query_params
    context["third_user"].query_params["room_id"] = context["me"].query_params[
        "room_id"
    ]
    context["third_user"].run()


@when("a third user creates another room")
def third_user_creates_another_room(context: dict[str, AppTest]) -> None:
    context["third_user"] = AppTest.from_function(run_wrapper)
    context["third_user"].run()
    context["third_user"].button(key="start_room").click().run()


@then(parsers.parse('"{users}" should see status "{status}"'))
def users_should_see_status(
    context: dict[str, AppTest],
    users: str,
    status: str,
) -> None:
    user_keys = [u.strip() for u in users.split(",")]

    for user in user_keys:
        room_id = get_room_id(context[user])
        df = captured.room_data[room_id]
        actual_count = df[status].iloc[0]
        assert actual_count == 1, f"{user}, {status}, actual_count: {actual_count}"
