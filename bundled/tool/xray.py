def annotate(filepath: str, lineno: int):
    """Annotate the function defined in `filepath` on line `lineno` (0-based indexed)."""
    return f"{filepath}:{lineno+1}"
