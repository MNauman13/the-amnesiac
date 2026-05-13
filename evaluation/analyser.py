from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent.harness import RunResult, StepResult


@dataclass
class SchemaEvolution:
    step: int
    headers: list[str]
    byte_count: int


@dataclass
class AnalysisReport:
    schema_timeline: list[SchemaEvolution]
    dominant_headers: list[tuple[str, int]]
    avg_scroll_bytes: float
    max_scroll_bytes: int
    schema_mutation_steps: list[int]
    emergent_patterns: list[str]


def analyse_run(run: "RunResult") -> AnalysisReport:
    steps = run.steps
    timeline = _build_schema_timeline(steps)
    dominant = _dominant_headers(timeline)
    avg_bytes = _avg_bytes(steps)
    max_bytes = _max_bytes(steps)
    mutations = _mutation_steps(timeline)
    patterns = _detect_emergent_patterns(steps)

    return AnalysisReport(
        schema_timeline=timeline,
        dominant_headers=dominant,
        avg_scroll_bytes=round(avg_bytes, 1),
        max_scroll_bytes=max_bytes,
        schema_mutation_steps=mutations,
        emergent_patterns=patterns,
    )


def _build_schema_timeline(steps: list["StepResult"]) -> list[SchemaEvolution]:
    result = []
    for s in steps:
        scroll = s.scroll_after
        headers = re.findall(r"^\[([^\]]+)\]", scroll, re.MULTILINE)
        result.append(SchemaEvolution(
            step=s.step,
            headers=headers,
            byte_count=len(scroll.encode("utf-8")),
        ))
    return result


def _dominant_headers(timeline: list[SchemaEvolution]) -> list[tuple[str, int]]:
    counter: Counter = Counter()
    for evo in timeline:
        for h in evo.headers:
            counter[h] += 1
    return counter.most_common(10)


def _avg_bytes(steps: list["StepResult"]) -> float:
    written = [s.memory_write.bytes_used for s in steps if s.memory_write and s.memory_write.bytes_used > 0]
    return sum(written) / len(written) if written else 0.0


def _max_bytes(steps: list["StepResult"]) -> int:
    written = [s.memory_write.bytes_used for s in steps if s.memory_write]
    return max(written) if written else 0


def _mutation_steps(timeline: list[SchemaEvolution]) -> list[int]:
    mutations = []
    if len(timeline) < 2:
        return mutations
    prev = frozenset(timeline[0].headers)
    for evo in timeline[1:]:
        curr = frozenset(evo.headers)
        if curr != prev:
            mutations.append(evo.step)
        prev = curr
    return mutations


def _detect_emergent_patterns(steps: list["StepResult"]) -> list[str]:
    patterns = []
    scrolls = [s.scroll_after for s in steps if s.scroll_after.strip()]

    has_landmarks = any(
        re.search(r"(→|->|--|room\s*:)", scroll, re.IGNORECASE)
        for scroll in scrolls[len(scrolls) // 2 :]
    )
    if has_landmarks:
        patterns.append("Landmark Navigation — agent uses named rooms/paths instead of raw coordinates")

    has_priority = any(
        re.search(r"(priority|urgent|first|next|todo)", scroll, re.IGNORECASE)
        for scroll in scrolls
    )
    if has_priority:
        patterns.append("Priority Queuing — agent ranks goals by urgency")

    has_temporal = any(
        re.search(r"step\s*\d+|every\s*\d+|re-lock", scroll, re.IGNORECASE)
        for scroll in scrolls
    )
    if has_temporal:
        patterns.append("Temporal Tagging — agent tracks time-sensitive info by step number")

    has_hypothesis = any(
        re.search(r"\?|unknown|maybe|possibly|rumou?red", scroll, re.IGNORECASE)
        for scroll in scrolls
    )
    if has_hypothesis:
        patterns.append("Hypothesis Tracking — agent flags uncertain info with '?' markers")

    return patterns
