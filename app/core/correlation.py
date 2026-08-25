import re
from uuid import uuid4

CORRELATION_HEADER = "X-Correlation-ID"
_VALID_CORRELATION_ID = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


def get_or_create_correlation_id(value: str | None) -> str:
    if value and _VALID_CORRELATION_ID.fullmatch(value):
        return value
    return str(uuid4())