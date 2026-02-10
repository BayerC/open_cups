import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from open_cups.state_provider import (
    ClientState,
    HostState,
    RoomState,
)
from open_cups.types import UserStatus

GREY_COLOR = "#9CA3AF"
RED_COLOR = "#EF4444"
YELLOW_COLOR = "#FBBF24"
GREEN_COLOR = "#10B981"


def get_statistics_data_frame(room: RoomState) -> pd.DataFrame:
    participants = room.get_room_participants()
    counts = {
        status.value: sum(1 for _, s in participants if s == status)
        for status in UserStatus
    }
    df = pd.DataFrame([counts])
    # Reorder columns: UNKNOWN (bottom), RED, YELLOW, GREEN (top)
    column_order = [
        UserStatus.UNKNOWN.value,
        UserStatus.RED.value,
        UserStatus.YELLOW.value,
        UserStatus.GREEN.value,
    ]
    return df[[col for col in column_order if col in df.columns]]


def show_room_statistics(room: HostState | ClientState) -> None:
    st.subheader("Room Overview")
    df = get_statistics_data_frame(room)

    if df.sum().sum() == 0:
        st.info("No participants yet. Share the Room ID to get started!")
        return

    fig = px.bar(
        df,
        x=df.index,
        y=df.columns,
        color_discrete_sequence=[
            GREY_COLOR,
            RED_COLOR,
            YELLOW_COLOR,
            GREEN_COLOR,
        ],
    )

    fig.update_layout(
        showlegend=False,
        xaxis={"visible": False},
        yaxis={"visible": False},
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        height=250,
    )

    fig.update_traces(
        marker_cornerradius=8,
    )

    disable_interactions_config = {
        "displayModeBar": False,
        "staticPlot": True,
    }

    left_col, _ = st.columns([3, 2])
    with left_col:
        st.plotly_chart(fig, config=disable_interactions_config)
        participant_count = df.sum().sum()
        st.markdown(
            f"<p style='text-align: center;'>"
            f"Number of participants: {participant_count}"
            f"</p>",
            unsafe_allow_html=True,
        )


def show_status_history_chart(host_state: HostState) -> None:
    status_history = host_state.get_status_history()

    if not status_history:
        st.info("No status history yet. Waiting for participants to join...")
        return

    latest_snapshot_time = status_history[-1].timestamp

    data = {
        "Time (minutes)": [
            (snapshot.timestamp - latest_snapshot_time) / 60
            for snapshot in status_history
        ],
        UserStatus.GREEN.value: [
            snapshot.counts[UserStatus.GREEN] for snapshot in status_history
        ],
        UserStatus.YELLOW.value: [
            snapshot.counts[UserStatus.YELLOW] for snapshot in status_history
        ],
        UserStatus.RED.value: [
            snapshot.counts[UserStatus.RED] for snapshot in status_history
        ],
        UserStatus.UNKNOWN.value: [
            snapshot.counts[UserStatus.UNKNOWN] for snapshot in status_history
        ],
    }

    df = pd.DataFrame(data)

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["Time (minutes)"],
            y=df[UserStatus.UNKNOWN.value],
            name=UserStatus.UNKNOWN.value,
            mode="lines",
            line={"color": GREY_COLOR, "width": 2},
            stackgroup="one",
        ),
    )

    fig.add_trace(
        go.Scatter(
            x=df["Time (minutes)"],
            y=df[UserStatus.RED.value],
            name=UserStatus.RED.value,
            mode="lines",
            line={"color": RED_COLOR, "width": 2},
            stackgroup="one",
        ),
    )

    fig.add_trace(
        go.Scatter(
            x=df["Time (minutes)"],
            y=df[UserStatus.YELLOW.value],
            name=UserStatus.YELLOW.value,
            mode="lines",
            line={"color": YELLOW_COLOR, "width": 2},
            stackgroup="one",
        ),
    )

    fig.add_trace(
        go.Scatter(
            x=df["Time (minutes)"],
            y=df[UserStatus.GREEN.value],
            name=UserStatus.GREEN.value,
            mode="lines",
            line={"color": GREEN_COLOR, "width": 2},
            stackgroup="one",
        ),
    )

    fig.add_vline(
        x=0,
        line_width=1,
        line_dash="dot",
        line_color=GREY_COLOR,
        annotation_text="Present",
        annotation_position="top right",
    )

    fig.update_layout(
        xaxis={"title": "Time (minutes)", "dtick": 1, "tickformat": "d"},
        yaxis={"title": "Number of participants", "dtick": 1},
        hovermode="x unified",
        showlegend=False,
        margin={"l": 0, "r": 0, "t": 40, "b": 0},
        height=400,
    )

    disable_interactions_config = {
        "displayModeBar": False,
        "staticPlot": True,
    }

    # This flickers in many refreshes, even though we do basically the same as for
    # the bar chart. Is this acceptable?
    st.plotly_chart(
        fig,
        width="stretch",
        config=disable_interactions_config,
        key="status_history_chart",
    )
