def escape_colons(text: str) -> str:
    return text.replace(":", r"\:")


def unescape_colons(text: str) -> str:
    return text.replace(r"\:", ":")
