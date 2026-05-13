from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent.harness import RunResult
    from evaluation.scorer import TaskScore
    from evaluation.analyser import AnalysisReport


def print_report(run: "RunResult", score: "TaskScore", analysis: "AnalysisReport") -> None:
    bar = "=" * 60
    print(f"\n{bar}")
    print(f"  RUN REPORT — Task: {run.task_id.upper()}")
    print(bar)

    print(f"\n  Outcome:      {'✓ GOAL COMPLETE' if run.goal_complete else '✗ GOAL INCOMPLETE'}")
    print(f"  Steps taken:  {run.total_steps}")
    print(f"  Parse errors: {run.parse_errors}")
    print(f"  Act. failures:{run.action_failures}")
    print(f"  Tokens used:  {run.total_tokens_in} in / {run.total_tokens_out} out")

    print(f"\n  --- SCORES ---")
    print(f"  Task completion:   {score.task_completion:.3f}  (× 0.60 = {score.task_completion * 0.60:.3f})")
    print(f"  Memory efficiency: {score.memory_efficiency:.3f}  (× 0.25 = {score.memory_efficiency * 0.25:.3f})")
    print(f"  Step efficiency:   {score.step_efficiency:.3f}  (× 0.15 = {score.step_efficiency * 0.15:.3f})")
    print(f"  ─────────────────────────────")
    print(f"  TOTAL SCORE:       {score.total:.3f}")

    m = score.memory_metrics
    print(f"\n  --- MEMORY METRICS ---")
    print(f"  Recall accuracy:      {m.recall_accuracy:.3f}")
    print(f"  Compression efficiency:{m.compression_efficiency:.3f}")
    print(f"  Schema stability:     {1.0 - m.schema_stability:.3f}  (instability={m.schema_stability:.3f})")
    print(f"  Memory score:         {m.memory_score:.3f}")

    print(f"\n  --- MEMORY ANALYSIS ---")
    print(f"  Avg scroll size: {analysis.avg_scroll_bytes:.0f} bytes")
    print(f"  Max scroll size: {analysis.max_scroll_bytes} bytes")
    if analysis.dominant_headers:
        top = ", ".join(f"[{h}]×{n}" for h, n in analysis.dominant_headers[:5])
        print(f"  Top headers:     {top}")
    if analysis.schema_mutation_steps:
        print(f"  Schema mutations at steps: {analysis.schema_mutation_steps}")
    if analysis.emergent_patterns:
        print(f"\n  Emergent strategies detected:")
        for p in analysis.emergent_patterns:
            print(f"    • {p}")

    print(f"\n{bar}\n")


def write_report(
    run: "RunResult",
    score: "TaskScore",
    analysis: "AnalysisReport",
    path: str,
) -> None:
    from pathlib import Path

    lines = [
        f"# Run Report — {run.task_id.upper()}",
        "",
        f"**Outcome:** {'GOAL COMPLETE' if run.goal_complete else 'GOAL INCOMPLETE'}",
        f"**Total steps:** {run.total_steps}",
        f"**Total score:** {score.total:.4f}",
        "",
        "## Scores",
        f"| Metric | Score | Weight | Contribution |",
        f"|---|---|---|---|",
        f"| Task completion | {score.task_completion:.3f} | 0.60 | {score.task_completion * 0.60:.3f} |",
        f"| Memory efficiency | {score.memory_efficiency:.3f} | 0.25 | {score.memory_efficiency * 0.25:.3f} |",
        f"| Step efficiency | {score.step_efficiency:.3f} | 0.15 | {score.step_efficiency * 0.15:.3f} |",
        f"| **Total** | **{score.total:.3f}** | | |",
        "",
        "## Memory Metrics",
        f"- Recall accuracy: {score.memory_metrics.recall_accuracy:.3f}",
        f"- Compression efficiency: {score.memory_metrics.compression_efficiency:.3f}",
        f"- Schema stability: {1.0 - score.memory_metrics.schema_stability:.3f}",
        f"- Avg scroll size: {analysis.avg_scroll_bytes:.0f} bytes",
        "",
    ]

    if analysis.emergent_patterns:
        lines += ["## Emergent Strategies"] + [f"- {p}" for p in analysis.emergent_patterns] + [""]

    lines += [
        "## Step Log",
        "| Step | Action | Success | Progress | Scroll (B) |",
        "|---|---|---|---|---|",
    ]
    for s in run.steps:
        act = str(s.parse_result.action) if s.parse_result.action else "WAIT"
        ok = "✓" if s.action_result.success else "✗"
        scroll_b = s.memory_write.bytes_used if s.memory_write else 0
        lines.append(f"| {s.step} | {act} | {ok} | {s.goal_progress:.2f} | {scroll_b} |")

    Path(path).write_text("\n".join(lines), encoding="utf-8")
