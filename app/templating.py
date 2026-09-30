from datetime import date, datetime
from pathlib import Path

from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory=Path(__file__).with_name("templates"))


def number(value: float, digits: int = 0) -> str:
    return f"{value:,.{digits}f}"


def status_label(status: str) -> str:
    return status.replace("_", " ").capitalize()


def days_since(value: str | date) -> int:
    return (date.today() - date.fromisoformat(str(value))).days


def log_time(value: str) -> str:
    return datetime.fromisoformat(value).strftime("%a %d %b · %H:%M")


def shift_label() -> str:
    now = datetime.now()
    shift = "Day shift" if 6 <= now.hour < 18 else "Night shift"
    return f"{now:%A %d %B} · {shift}"


templates.env.filters.update(
    number=number, status_label=status_label, days_since=days_since, log_time=log_time
)
templates.env.globals["shift_label"] = shift_label
