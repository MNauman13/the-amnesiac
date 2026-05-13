import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agent.memory import MemoryScroll, WriteResult


class TestBasicReadWrite:
    def test_initial_scroll_is_empty(self):
        m = MemoryScroll()
        assert m.read() == ""
        assert m.is_empty()

    def test_write_and_read_back(self):
        m = MemoryScroll()
        m.write("[GOAL] find key")
        assert m.read() == "[GOAL] find key"

    def test_write_overwrites_previous(self):
        m = MemoryScroll()
        m.write("first content")
        m.write("second content")
        assert m.read() == "second content"

    def test_byte_usage_accurate(self):
        m = MemoryScroll()
        content = "hello"
        m.write(content)
        assert m.byte_usage() == len(content.encode("utf-8"))

    def test_byte_usage_zero_initially(self):
        m = MemoryScroll()
        assert m.byte_usage() == 0


class TestByteBudget:
    def test_write_within_budget_succeeds(self):
        m = MemoryScroll()
        content = "x" * 500
        result = m.write(content)
        assert result.success
        assert not result.truncated
        assert result.bytes_used == 500

    def test_write_at_exact_limit_succeeds(self):
        m = MemoryScroll()
        content = "a" * MemoryScroll.MAX_BYTES
        result = m.write(content)
        assert result.success
        assert not result.truncated

    def test_write_over_budget_truncates(self):
        m = MemoryScroll()
        content = "b" * (MemoryScroll.MAX_BYTES + 100)
        result = m.write(content)
        assert result.success
        assert result.truncated
        assert result.bytes_used <= MemoryScroll.MAX_BYTES
        assert len(m.read().encode("utf-8")) <= MemoryScroll.MAX_BYTES

    def test_truncated_content_still_readable(self):
        m = MemoryScroll()
        content = "c" * (MemoryScroll.MAX_BYTES + 500)
        m.write(content)
        assert len(m.read()) > 0

    def test_write_result_contains_correct_max(self):
        m = MemoryScroll()
        result = m.write("test")
        assert result.bytes_max == MemoryScroll.MAX_BYTES


class TestHistory:
    def test_history_empty_initially(self):
        m = MemoryScroll()
        assert m.history() == []

    def test_history_records_previous_scrolls(self):
        m = MemoryScroll()
        m.write("v1")
        m.write("v2")
        hist = m.history()
        assert "v1" in hist

    def test_history_depth_limited_to_three(self):
        m = MemoryScroll()
        for i in range(6):
            m.write(f"version {i}")
        assert len(m.history()) <= MemoryScroll.HISTORY_DEPTH

    def test_history_returns_oldest_first(self):
        m = MemoryScroll()
        m.write("a")
        m.write("b")
        m.write("c")
        hist = m.history()
        assert hist[0] == "a" or hist[-1] != "a"

    def test_history_n_param_limits_output(self):
        m = MemoryScroll()
        for i in range(5):
            m.write(f"v{i}")
        assert len(m.history(1)) == 1
        assert len(m.history(2)) == 2

    def test_current_scroll_not_in_history_until_overwritten(self):
        m = MemoryScroll()
        m.write("current")
        assert "current" not in m.history()
        m.write("next")
        assert "current" in m.history()


class TestUnicodeHandling:
    def test_unicode_content_measured_in_bytes(self):
        m = MemoryScroll()
        content = "→ Hallway B ← Storage"
        m.write(content)
        assert m.byte_usage() == len(content.encode("utf-8"))

    def test_unicode_near_limit_truncated_cleanly(self):
        m = MemoryScroll()
        multibyte = "→" * 1000
        result = m.write(multibyte)
        if result.truncated:
            assert len(m.read().encode("utf-8")) <= MemoryScroll.MAX_BYTES
            assert m.read().encode("utf-8").decode("utf-8", errors="ignore") == m.read()
