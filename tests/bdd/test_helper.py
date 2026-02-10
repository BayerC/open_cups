from streamlit.testing.v1 import AppTest


def refresh_all_apps(context: dict[str, AppTest]) -> None:
    for app in context.values():
        app.run()


def get_page_content(app: AppTest) -> str:
    markdown_content = "\n".join(element.value for element in app.markdown)
    text_content = "\n".join(element.value for element in app.text)
    info_content = "\n".join(element.value for element in app.info)
    return f"{markdown_content}\n{text_content}\n{info_content}"


def get_info_content(app: AppTest) -> str:
    return "\n".join(element.value for element in app.info)


def check_page_contents(
    app: AppTest,
    expected: tuple[str, ...],
    forbidden: tuple[str, ...] = (),
) -> None:
    page_content = get_page_content(app)
    for string in expected:
        assert string in page_content
    for string in forbidden:
        assert string not in page_content


def get_room_id(app: AppTest) -> str:
    for markdown_element in app.markdown:
        value = markdown_element.value
        if value.startswith("**") and value.endswith("**"):
            return value[2:-2]
    msg = "Room ID not found"
    raise AssertionError(msg)
