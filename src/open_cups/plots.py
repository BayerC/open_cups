import math

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

MAX_NUMBER_OF_TICKS = 10

GREY_COLOR = "#9CA3AF"
RED_COLOR = "#EF4444"
YELLOW_COLOR = "#FBBF24"
GREEN_COLOR = "#10B981"

ORDERED_STATUS_COLOR_MAP = [
    (UserStatus.UNKNOWN, GREY_COLOR),
    (UserStatus.RED, RED_COLOR),
    (UserStatus.YELLOW, YELLOW_COLOR),
    (UserStatus.GREEN, GREEN_COLOR),
]

STREAMLIT_DISABLE_INTERACTIONS_CONFIG = {
    "displayModeBar": False,
    "staticPlot": True,
}


def get_statistics_data_frame(room: RoomState) -> pd.DataFrame:
    participants = room.get_room_participants()
    counts = {
        status.value: sum(1 for _, s in participants if s == status)
        for status in UserStatus
    }
    df = pd.DataFrame([counts])
    column_order = [status.value for status, _ in ORDERED_STATUS_COLOR_MAP]
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
        color_discrete_sequence=[color for _, color in ORDERED_STATUS_COLOR_MAP],
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

    left_col, _ = st.columns([3, 2])
    with left_col:
        st.plotly_chart(
            fig,
            config=STREAMLIT_DISABLE_INTERACTIONS_CONFIG,
            key="room_statistics_chart",
        )
        participant_count = df.sum().sum()
        st.markdown(
            f"<p style='text-align: center;'>"
            f"Number of participants: {participant_count}"
            f"</p>",
            unsafe_allow_html=True,
        )


def add_future_timestamp(
    timestamps: list[float], relative_extension: float
) -> list[float]:
    total_range = timestamps[-1] - timestamps[0] if len(timestamps) > 1 else 1
    absolute_extension = total_range * relative_extension

    phantom_time = timestamps[-1] + absolute_extension
    return [*timestamps, phantom_time]


def show_status_history_chart(host_state: HostState) -> None:
    status_history = host_state.get_status_history()

    if not status_history:
        st.info("No status history yet. Waiting for participants to join...")
        return

    latest_snapshot_time = status_history[-1].timestamp

    timestamps = [
        (snapshot.timestamp - latest_snapshot_time) / 60 for snapshot in status_history
    ]

    timestamps_extended = add_future_timestamp(timestamps, relative_extension=0.1)

    data = {"Time (minutes)": timestamps_extended}
    for user_status in UserStatus:
        counts = [snapshot.counts[user_status] for snapshot in status_history]
        data[user_status.value] = [
            *counts,
            counts[-1],
        ]  # repeat last value in future timestamp

    df = pd.DataFrame(data)

    fig = go.Figure()

    for user_status, color in ORDERED_STATUS_COLOR_MAP:
        fig.add_trace(
            go.Scatter(
                x=df["Time (minutes)"],
                y=df[user_status.value],
                name=user_status.value,
                mode="lines",
                line={"color": color, "width": 2},
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

    x_range_size = timestamps_extended[-1] - timestamps_extended[0]
    x_dtick = max(1, math.ceil(x_range_size / MAX_NUMBER_OF_TICKS))

    fig.update_layout(
        xaxis={
            "title": "Time (minutes)",
            "dtick": x_dtick,
            "tickformat": "d",
            "range": [timestamps_extended[0], timestamps_extended[-1]],
        },
        yaxis={"title": "Number of participants", "dtick": 1},
        hovermode="x unified",
        showlegend=False,
        margin={"l": 0, "r": 0, "t": 40, "b": 0},
        height=400,
    )

    st.plotly_chart(
        fig,
        width="stretch",
        config=STREAMLIT_DISABLE_INTERACTIONS_CONFIG,
        key="status_history_chart",
    )
