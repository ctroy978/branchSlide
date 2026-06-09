import markdown


def render_markdown(content_md: str) -> str:
    return markdown.markdown(
        content_md,
        extensions=["fenced_code", "tables", "nl2br"],
    )