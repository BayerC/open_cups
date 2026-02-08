from pytest_bdd import given, parsers, then, when
from streamlit.testing.v1 import AppTest

from open_cups.user_status import UserStatus
from tests.bdd.fixture import run_wrapper
from tests.bdd.test_helper import get_room_id, refresh_all_apps

STATUS_VALUES = {status.value: status for status in UserStatus}


@given("I host a room")
def host_room(context: dict[str, AppTest]) -> None:
    click_create_room(context)
    see_active_room_screen(context)


@when('I click the "Create Room" button')
def click_create_room(context: dict[str, AppTest]) -> None:
    context["me"].button(key="start_room").click().run()


@when("a second user joins the room")
def second_user_joins_room(context: dict[str, AppTest]) -> None:
    context["second_user"] = AppTest.from_function(run_wrapper)
    context["second_user"].run()
    context["second_user"].text_input(key="join_room_id").set_value(
        get_room_id(context["me"]),
    ).run()
    context["second_user"].button(key="join_room").click().run()
    refresh_all_apps(context)


def _select_status(app: AppTest, context: dict[str, AppTest], status: str) -> None:
    status_enum = STATUS_VALUES.get(status)
    assert status_enum is not None
    app.radio(key="user_status_selection").set_value(status_enum).run()
    refresh_all_apps(context)


@when(parsers.parse('I select the status "{status}"'))
def i_select_status(context: dict[str, AppTest], status: str) -> None:
    _select_status(context["me"], context, status)


@when(parsers.parse('the second user selects the status "{status}"'))
def second_user_select_status(context: dict[str, AppTest], status: str) -> None:
    _select_status(context["second_user"], context, status)


@then("I should see the active room screen")
def see_active_room_screen(context: dict[str, AppTest]) -> None:
    assert len(context["me"].title) == 1
    assert context["me"].title[0].value == "Active Room"


@given("I am on the room selection screen")
@then("I should still be on the room selection screen")
def on_room_selection_screen(context: dict[str, AppTest]) -> None:
    assert len(context["me"].title) == 1
    assert context["me"].title[0].value == "Welcome to OpenCups"
