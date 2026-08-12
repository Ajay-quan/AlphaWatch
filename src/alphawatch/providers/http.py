from __future__ import annotations

from dataclasses import dataclass
from urllib.request import Request, urlopen


@dataclass(frozen=True, slots=True)
class HttpClient:
    user_agent: str
    timeout_seconds: float = 30.0

    def get(self, url: str) -> bytes:
        if "@" not in self.user_agent:
            raise ValueError("user_agent must include a contact email")
        request = Request(url, headers={"User-Agent": self.user_agent, "Accept-Encoding": "gzip"})
        with urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310
            payload: bytes = response.read()
            return payload
