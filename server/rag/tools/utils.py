from datetime import date
from langchain_core.tools import tool


@tool
def get_current_date() -> str:
    """Return today's date in YYYY-MM-DD format.
    Call this whenever the user refers to 'today', 'now', or an unspecified date."""
    return date.today().isoformat()