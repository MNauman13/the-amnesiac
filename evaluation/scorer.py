from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent.harness import RunResult, StepResult
    from world.engine import WorldEngine


@dataclass
class MemoryMetrics:
    recall_accuracy: float
    compression_efficiency: float
    schema_stability: float
    memory_score: float


@dataclass
class TaskScore:
    task_completion: float
    memory_efficiency: float
    step_efficiency: float
    total: float
    memory_metrics: MemoryMetrics


def score_run(run: "RunResult", engine: "WorldEngine") -> TaskScore:
    task_completion = _task_completion_score(run)
    memory_metrics = _memory_metrics(run)
    step_eff = _step_efficiency(run, engine)

    memory_efficiency = memory_metrics.memory_score
    total = (
        0.60 * task_completion
        + 0.25 * memory_efficiency
        + 0.15 * step_eff
    )

    return TaskScore(
        task_completion=round(task_completion, 4),
        memory_efficiency=round(memory_efficiency, 4),
        step_efficiency=round(step_eff, 4),
        total=round(total, 4),
        memory_metrics=memory_metrics,
    )


def _task_completion_score(run: "RunResult") -> float:
    if run.goal_complete:
        return 1.0
    return run.final_progress


def _step_efficiency(run: "RunResult", engine: "WorldEngine") -> float:
    optimal = engine.optimal_steps()
    if optimal <= 0 or run.total_steps <= 0:
        return 1.0 if run.goal_complete else 0.0
    ratio = optimal / run.total_steps
    return min(ratio, 1.0)


def _memory_metrics(run: "RunResult") -> MemoryMetrics:
    recall = _recall_accuracy(run.steps)
    compression = _compression_efficiency(run.steps)
    stability = _schema_stability(run.steps)

    memory_score = 0.5 * recall + 0.3 * compression + 0.2 * (1.0 - stability)
    return MemoryMetrics(
        recall_accuracy=round(recall, 4),
        compression_efficiency=round(compression, 4),
        schema_stability=round(stability, 4),
        memory_score=round(memory_score, 4),
    )


def _recall_accuracy(steps: list["StepResult"]) -> float:
    if not steps:
        return 0.0
    recall_count = 0
    for step in steps:
        scroll = step.scroll_before
        if not scroll.strip():
            if step.step <= 1:
                recall_count += 1
            continue
        if step.action_result.success:
            recall_count += 1
        elif step.parse_result.parse_error:
            pass
        else:
            recall_count += 0.5
    return recall_count / len(steps)


def _compression_efficiency(steps: list["StepResult"]) -> float:
    if not steps:
        return 0.0

    written = [s for s in steps if s.memory_write and s.memory_write.bytes_used > 0]
    if not written:
        return 0.0

    ratios = []
    for step in written:
        used = step.memory_write.bytes_used
        max_b = step.memory_write.bytes_max
        if used == 0:
            continue
        scroll = step.scroll_after
        lines = [l.strip() for l in scroll.split("\n") if l.strip()]
        filled_ratio = len(lines) / max(1, used / 20)
        utilization = used / max_b
        eff = min(1.0, (utilization * 0.5) + (min(filled_ratio, 1.0) * 0.5))
        ratios.append(eff)

    return sum(ratios) / len(ratios) if ratios else 0.0


def _schema_stability(steps: list["StepResult"]) -> float:
    scrolls = [s.scroll_after for s in steps if s.scroll_after.strip()]
    if len(scrolls) < 2:
        return 0.0

    mutations = 0
    prev_headers = _extract_headers(scrolls[0])
    for scroll in scrolls[1:]:
        curr_headers = _extract_headers(scroll)
        if curr_headers != prev_headers:
            mutations += 1
        prev_headers = curr_headers

    return mutations / (len(scrolls) - 1)


def _extract_headers(scroll: str) -> frozenset[str]:
    import re
    return frozenset(re.findall(r"^\[([^\]]+)\]", scroll, re.MULTILINE))
