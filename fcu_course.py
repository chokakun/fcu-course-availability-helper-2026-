"""Pure validation and message parsing for the FCU course helper."""

from dataclasses import dataclass
import re
from typing import Iterable, Mapping, Optional, Tuple


DEFAULT_POLL_INTERVAL_SECONDS = 3


@dataclass(frozen=True)
class CourseConfig:
    course_code: str
    poll_interval_seconds: int = DEFAULT_POLL_INTERVAL_SECONDS

    def __post_init__(self) -> None:
        if not re.fullmatch(r"\d{4}", self.course_code):
            raise ValueError("course code must contain exactly 4 digits")
        if self.poll_interval_seconds < 0:
            raise ValueError("poll interval must be non-negative")


def parse_seat_status(message: str) -> Optional[Tuple[int, int]]:
    """Return (remaining_seats, open_seats) from a labeled FCU alert message."""

    slash_separated = re.search(
        r"剩餘名額\s*[／/]\s*開放名額\s*[：:]?\s*(\d+)\s*[／/]\s*(\d+)",
        message,
    )
    if slash_separated:
        return int(slash_separated.group(1)), int(slash_separated.group(2))

    remaining = re.search(r"(?:目前)?剩餘名額\s*[：:]?\s*(\d+)", message)
    open_seats = re.search(r"開放名額\s*[：:]?\s*(\d+)", message)
    if not remaining or not open_seats:
        return None
    return int(remaining.group(1)), int(open_seats.group(1))


def unrecognized_status_message(course_code: str, message: str) -> str:
    """Preserve an unknown FCU response so it can be inspected safely."""

    return f"{course_code}: unrecognized status message: {message}"


def normalize_course_codes(course_codes: Iterable[str]) -> Tuple[str, ...]:
    """Validate course codes and preserve first-occurrence priority order."""

    normalized = []
    seen = set()
    for course_code in course_codes:
        CourseConfig(course_code=course_code)
        if course_code not in seen:
            normalized.append(course_code)
            seen.add(course_code)
    if not normalized:
        raise ValueError("at least one course code is required")
    return tuple(normalized)


def is_successful_enrollment_response(message: str) -> bool:
    """Recognize only explicit add-course success text, never an ambiguous response."""

    compact_message = re.sub(r"\s+", "", message)
    success_markers = (
        "加選成功",
        "選課成功",
        "加選完成",
        "選課完成",
        "成功加選",
        "成功選課",
    )
    return any(marker in compact_message for marker in success_markers)


def split_enrollment_responses(
    submitted_responses: Mapping[str, str],
) -> Tuple[Tuple[str, ...], Tuple[str, ...]]:
    """Return course codes with explicit success and codes needing manual verification."""

    confirmed = []
    unconfirmed = []
    for course_code, response in submitted_responses.items():
        if is_successful_enrollment_response(response):
            confirmed.append(course_code)
        else:
            unconfirmed.append(course_code)
    return tuple(confirmed), tuple(unconfirmed)
