from __future__ import annotations

from dataclasses import dataclass


@dataclass
class WriteResult:
    success: bool
    bytes_used: int
    bytes_max: int
    truncated: bool
    message: str


class MemoryScroll:
    MAX_BYTES = 2048
    HISTORY_DEPTH = 3

    def __init__(self) -> None:
        self._scroll: str = ""
        self._history: list[str] = []

    def read(self) -> str:
        return self._scroll

    def write(self, content: str) -> WriteResult:
        encoded = content.encode("utf-8")
        truncated = False

        if len(encoded) > self.MAX_BYTES:
            truncated = True
            encoded = encoded[: self.MAX_BYTES]
            content = encoded.decode("utf-8", errors="ignore")

        self._history.append(self._scroll)
        if len(self._history) > self.HISTORY_DEPTH:
            self._history.pop(0)

        self._scroll = content
        used = len(content.encode("utf-8"))
        msg = "OK" if not truncated else f"Truncated to {self.MAX_BYTES} bytes."
        return WriteResult(True, used, self.MAX_BYTES, truncated, msg)

    def history(self, n: int = HISTORY_DEPTH) -> list[str]:
        return list(self._history[-n:])

    def byte_usage(self) -> int:
        return len(self._scroll.encode("utf-8"))

    def is_empty(self) -> bool:
        return self._scroll.strip() == ""
