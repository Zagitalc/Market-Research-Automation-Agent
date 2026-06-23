from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class FetchResult:
    requested_url: str
    final_url: str
    status_code: int
    content_type: str
    body: bytes
    headers: dict[str, str]
    fetched_at: datetime
    provider: str


class WebFetchProvider(Protocol):
    def fetch(self, url: str) -> FetchResult:
        ...
