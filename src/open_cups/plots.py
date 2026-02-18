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


def show_status_history_chart(host_state: HostState) -> None:
    import math
    
    status_history = host_state.get_status_history()

    if not status_history:
        st.info("No status history yet. Waiting for participants to join...")
        return

    latest_snapshot_time = status_history[-1].timestamp

    times_minutes = [
        (snapshot.timestamp - latest_snapshot_time) / 60
        for snapshot in status_history
    ]
    oldest_time = min(times_minutes)

    def transform_time(t: float) -> float:
        """Logarithmic transformation: recent past gets more space than distant past."""
        if oldest_time >= 0:
            return 0
        
        log_range = math.log(1 + abs(oldest_time))
        normalized = (math.log(1 + abs(oldest_time)) - math.log(1 + abs(t))) / log_range
        return normalized * 100

    transformed_times = [transform_time(t) for t in times_minutes]

    data = {"Transformed Time": transformed_times}
    for user_status in UserStatus:
        data[user_status.value] = [
            snapshot.counts[user_status] for snapshot in status_history
        ]

    df = pd.DataFrame(data)

    fig = go.Figure()

    for user_status, color in ORDERED_STATUS_COLOR_MAP:
        fig.add_trace(
            go.Scatter(
                x=df["Transformed Time"],
                y=df[user_status.value],
                name=user_status.value,
                mode="lines",
                line={"color": color, "width": 2},
                stackgroup="one",
            ),
        )

    tickvals = []
    ticktext = []
    
    for minute in range(int(oldest_time), 1):
        transformed = transform_time(float(minute))
        tickvals.append(transformed)
        ticktext.append(str(minute))

    fig.add_vline(
        x=100,
        line_width=1,
        line_dash="dot",
        line_color=GREY_COLOR,
        annotation_text="Present",
        annotation_position="top right",
    )

    fig.update_layout(
        xaxis={
            "title": "Time (minutes)",
            "range": [0, 100],
            "tickvals": tickvals,
            "ticktext": ticktext,
        },
        yaxis={"title": "Number of participants", "dtick": 1},
        hovermode="x unified",
        showlegend=False,
        margin={"l": 0, "r": 0, "t": 40, "b": 0},
        height=400,
    )

    # This flickers in many refreshes, even though we do basically the same as for
    # the bar chart. Is this acceptable?
    st.plotly_chart(
        fig,
        width="stretch",
        config=STREAMLIT_DISABLE_INTERACTIONS_CONFIG,
        key="status_history_chart",
    )
