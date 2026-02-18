import json

from pytest_bdd import parsers, scenario, then, when
from streamlit.testing.v1 import AppTest

from open_cups.types import UserStatus


@scenario(
    "features/distribution_history.feature",
    "Host views distribution history",
)
def test_host_views_distribution_history() -> None:
    pass


@when(parsers.parse('I select the view "{view_name}"'))
def i_select_view(context: dict[str, AppTest], view_name: str) -> None:
    context["me"].radio(key="host_view_choice").set_value(view_name).run()


@then("I should see the distribution history empty state")
def i_should_see_distribution_history_empty_state(
    context: dict[str, AppTest],
) -> None:
    info_messages = [info.value for info in context["me"].info]
    assert "No status history yet. Waiting for participants to join..." in info_messages


@then("I should see the distribution history chart")
def i_should_see_distribution_history_chart(context: dict[str, AppTest]) -> None:
    plotly_charts = context["me"].get("plotly_chart")
    assert len(plotly_charts) == 1, "Expected exactly one plotly chart"

    chart_proto = plotly_charts[0].proto
    spec = json.loads(chart_proto.spec)

    trace_names = {trace["name"] for trace in spec["data"]}
    expected_names = {status.value for status in UserStatus}
    assert trace_names == expected_names
