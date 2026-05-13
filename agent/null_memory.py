from __future__ import annotations

from agent.memory import MemoryScroll, WriteResult


class NullMemoryScroll(MemoryScroll):
    """Always returns empty scroll; discards every write. Used for comparative mode."""

    def read(self) -> str:
        return ""

    def write(self, content: str) -> WriteResult:
        return WriteResult(True, 0, self.MAX_BYTES, False, "NullMemory: discarded")

    def byte_usage(self) -> int:
        return 0

    def is_empty(self) -> bool:
        return True

    def history(self, n: int = MemoryScroll.HISTORY_DEPTH) -> list[str]:
        return []
