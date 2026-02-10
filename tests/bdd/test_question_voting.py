from pytest_bdd import parsers, scenario, then, when
from streamlit.testing.v1 import AppTest

from tests.bdd.fixture import run_wrapper
from tests.bdd.test_helper import check_page_contents, get_room_id, refresh_all_apps


@scenario("features/question_voting.feature", "Client submits a question")
def test_client_submits_a_question() -> None:
    pass


@when(parsers.parse('the second user submits a question "{question}"'))
def second_user_submits_question(context: dict[str, AppTest], question: str) -> None:
    context["second_user"].text_area(key="question_input").set_value(question).run()
    context["second_user"].button(key="submit_question").click().run()
    refresh_all_apps(context)


@when("a third user joins the room")
def third_user_joins_room(context: dict[str, AppTest]) -> None:
    context["third_user"] = AppTest.from_function(run_wrapper)
    context["third_user"].run()
    context["third_user"].text_input(key="join_room_id").set_value(
        get_room_id(context["me"]),
    ).run()
    context["third_user"].button(key="join_room").click().run()
    refresh_all_apps(context)


@then(
    parsers.parse(
        '"{users}" should see question "{question}" with {vote_count:d} vote',
    ),
)
@then(
    parsers.parse(
        '"{users}" should see question "{question}" with {vote_count:d} votes',
    ),
)
def users_should_see_question(
    context: dict[str, AppTest],
    users: str,
    question: str,
    vote_count: int,
) -> None:
    user_keys = [u.strip() for u in users.split(",")]

    for user in user_keys:
        app = context[user]

        check_page_contents(app, expected=(question,))

        button_labels = [btn.label for btn in app.button]
        vote_buttons = [
            label for label in button_labels if label.startswith(str(vote_count))
        ]

        assert len(vote_buttons) > 0, (
            f"No button with vote count {vote_count} found for {user}"
        )


@when(parsers.parse("the third user upvotes the question"))
def third_user_upvotes_question(context: dict[str, AppTest]) -> None:
    app = context["third_user"]
    upvote_buttons = [
        btn for btn in app.button if btn.key and btn.key.startswith("upvote_")
    ]
    assert len(upvote_buttons) == 1, (
        "Expected exactly one upvote button available for third user"
    )

    upvote_buttons[0].click().run()
    refresh_all_apps(context)


@when("I close the question")
def i_close_the_question(context: dict[str, AppTest]) -> None:
    app = context["me"]
    close_buttons = [
        btn for btn in app.button if btn.key and btn.key.startswith("close_")
    ]
    assert len(close_buttons) == 1, (
        "Expected exactly one close button available for host"
    )

    close_buttons[0].click().run()
    refresh_all_apps(context)


@then(parsers.parse('"{users}" should see no questions'))
def users_should_see_no_questions(context: dict[str, AppTest], users: str) -> None:
    user_keys = [u.strip() for u in users.split(",")]

    for user in user_keys:
        app = context[user]

        upvote_buttons = [
            btn for btn in app.button if btn.key and btn.key.startswith("upvote_")
        ]
        close_buttons = [
            btn for btn in app.button if btn.key and btn.key.startswith("close_")
        ]

        assert len(upvote_buttons) == 0, f"{user} still sees upvote buttons"
        assert len(close_buttons) == 0, f"{user} still sees close buttons"

        check_page_contents(app, expected=("No questions yet.",))
