import io

import pandas as pd
import plotly.express as px
import qrcode
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from open_cups.state_provider import (
    ClientState,
    HostState,
    LobbyState,
    RoomState,
    StateProvider,
)
from open_cups.user_status import UserStatus

AUTOREFRESH_INTERVAL_MS = 2000
USER_REMOVAL_TIMEOUT_SECONDS = (
    60  # if we go lower, chrome's background tab throttling causes faulty user removal
)

GREY_COLOR = "#9CA3AF"
RED_COLOR = "#EF4444"
YELLOW_COLOR = "#FBBF24"
GREEN_COLOR = "#10B981"


def show_room_selection_screen(lobby: LobbyState) -> None:
    if "room_id" in st.query_params:
        try:
            lobby.join_room(st.query_params["room_id"])
            st.rerun()
        except ValueError:
            st.error("Room ID from URL not found")

    st.title("Welcome to OpenCups")
    st.write("Host or join a room to share feedback.")

    col_left, col_right = st.columns(2, gap="medium")

    with col_left:
        st.subheader("Start New Room")
        if st.button("Create Room", width="stretch", key="start_room"):
            lobby.create_room()
            st.rerun()

    with col_right:
        st.subheader("Join Existing Room")
        room_id = st.text_input(
            "Room ID",
            key="join_room_id",
            placeholder="Insert room ID",
            label_visibility="collapsed",
        )
        if st.button("Join Room", width="stretch", key="join_room"):
            if not room_id:
                st.warning("Please enter a Room ID to join.")
            else:
                try:
                    lobby.join_room(room_id)
                    st.rerun()
                except ValueError:
                    st.error("Room ID not found")

    st.divider()

    st.subheader("How to Use This App")
    step_col_1, step_col_2, step_col_3 = st.columns(3)

    with step_col_1:
        st.info(
            "**1. Create a Room**\n\n"
            "The presenter starts a new session, which generates a unique room.",
        )

    with step_col_2:
        st.info(
            "**2. Share the Access Link**\n\n"
            "The presenter shares the room ID, a direct link, "
            "or a QR code with the audience.",
        )

    with step_col_3:
        st.info(
            "**3. Gather Live Feedback**\n\n"
            "Participants join to share their status "
            "and ask/vote on questions.",
        )


def show_user_status_selection(room: ClientState) -> None:
    st.subheader("Your Status")
    current_user_status = room.get_user_status()
    status_options = [
        UserStatus.GREEN,
        UserStatus.YELLOW,
        UserStatus.RED,
    ]
    if current_user_status == UserStatus.UNKNOWN:
        status_options.append(UserStatus.UNKNOWN)

    index = status_options.index(current_user_status)
    selected_user_status = st.radio(
        "How well can you follow the lecture?",
        status_options,
        index=index,
        format_func=lambda s: s.value,
        captions=[status.caption() for status in status_options],
        key="user_status_selection",
    )
    room.set_user_status(selected_user_status)

    has_user_transitioned_away_from_unknown_status = (
        current_user_status == UserStatus.UNKNOWN
        and selected_user_status != UserStatus.UNKNOWN
    )
    if has_user_transitioned_away_from_unknown_status:
        st.rerun()


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


def generate_qr_code_image(room_id: str) -> bytes:
    base_url = st.context.url
    join_url = f"{base_url}?room_id={room_id}"

    url_qr_code = qrcode.QRCode(
        border=0,
        box_size=3,
    )
    url_qr_code.add_data(join_url)
    url_qr_code.make(fit=True)

    img = url_qr_code.make_image(fill_color="black", back_color="white")
    img_bytes = io.BytesIO()
    img.save(img_bytes)
    return img_bytes.getvalue()


def show_active_room_header(room_id: str) -> None:
    st.query_params["room_id"] = room_id
    st.title("Active Room")
    left_col, right_col = st.columns([2, 1], gap="large")

    with left_col:
        st.subheader("Room ID")
        st.markdown(f"**{room_id}**")
        st.caption("Share this ID with participants to let them join")
    with right_col:
        st.image(generate_qr_code_image(room_id), width="content")

    st.divider()


def show_open_questions(state: HostState | ClientState) -> None:
    st.subheader("Open Questions")
    open_questions = state.get_open_questions()
    if not open_questions:
        st.info("No questions yet.")
    else:
        left_col, right_col = st.columns([8, 1], vertical_alignment="center")
        for question in open_questions:
            with left_col:
                st.info(question.text)
            with right_col:
                if isinstance(state, HostState):
                    if st.button(
                        f"{question.vote_count} ✅",
                        key=f"close_{question.id}",
                        help="Close question",
                        width="stretch",
                    ):
                        state.close_question(question.id)
                        st.rerun()
                elif isinstance(state, ClientState):
                    has_voted = state.has_voted(question)
                    if st.button(
                        f"{question.vote_count} ⬆️",
                        key=f"upvote_{question.id}",
                        disabled=has_voted,
                        help="Vote for question",
                        width="stretch",
                    ):
                        state.upvote_question(question.id)
                        st.rerun()


def show_active_room_host(host_state: HostState) -> None:
    show_active_room_header(host_state.room_id)
    show_room_statistics(host_state)

    st.divider()

    show_open_questions(host_state)


def show_active_room_client(client_state: ClientState) -> None:
    show_active_room_header(client_state.room_id)

    col_left, col_right = st.columns(2, gap="medium")
    with col_left:
        show_user_status_selection(client_state)
    with col_right:
        show_room_statistics(client_state)

    def handle_question_submit() -> None:
        question = st.session_state.question_input
        if question and question.strip():
            client_state.submit_question(question.strip())
            st.session_state.question_input = ""

    with st.form("question_form"):
        st.text_area(
            "Ask a Question",
            key="question_input",
            placeholder="Type your question here...",
        )

        st.form_submit_button(
            "Submit Question",
            key="submit_question",
            on_click=handle_question_submit,
        )

    show_open_questions(client_state)


def run() -> None:
    st_autorefresh(interval=AUTOREFRESH_INTERVAL_MS, key="data_refresh")

    state_provider = StateProvider()
    cleanup = state_provider.get_cleanup(USER_REMOVAL_TIMEOUT_SECONDS)
    cleanup.cleanup_all()

    match state_provider.get_current():
        case HostState() as host:
            show_active_room_host(host)
        case ClientState() as client:
            show_active_room_client(client)
        case LobbyState() as lobby:
            show_room_selection_screen(lobby)
