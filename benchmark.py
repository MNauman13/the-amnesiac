from __future__ import annotations

import argparse
import json
import statistics
from dataclasses import dataclass
from pathlib import Path

from world.engine import WorldEngine
from agent.memory import MemoryScroll
from agent.llm import LLMClient
from agent.harness import AgentHarness, RunResult
from evaluation.scorer import score_run, TaskScore
from evaluation.analyser import analyse_run


TASK_IDS = ["t1", "t2", "t3", "t4", "t5"]
TASK_FILES = {
    "t1": "t1_key_and_lock.json",
    "t2": "t2_fragment_assembly.json",
    "t3": "t3_moving_target.json",
    "t4": "t4_cartographer.json",
    "t5": "t5_relay_race.json",
}
DEFAULT_SEEDS = [42, 7, 137]


@dataclass
class TaskBenchmark:
    task_id: str
    seeds: list[int]
    scores: list[float]
    completions: list[bool]
    mean: float
    std: float
    completion_rate: float


@dataclass
class BenchmarkResult:
    tasks: list[TaskBenchmark]
    overall_mean: float
    overall_std: float
    pass_threshold: float


def load_task(task_id: str) -> dict:
    path = Path(__file__).parent / "tasks" / TASK_FILES[task_id]
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def run_single(task_id: str, seed: int, llm: LLMClient, verbose: bool = False) -> tuple[RunResult, TaskScore]:
    config = load_task(task_id)
    engine = WorldEngine(config, seed=seed)
    memory = MemoryScroll()
    harness = AgentHarness(
        engine=engine,
        llm=llm,
        memory=memory,
        log_dir=Path("logs"),
        task_id=f"{task_id}_seed{seed}",
        verbose=verbose,
    )
    run_result = harness.run()
    score = score_run(run_result, engine)
    return run_result, score


def run_benchmark(
    task_ids: list[str],
    seeds: list[int],
    llm: LLMClient,
    pass_threshold: float = 0.75,
    verbose: bool = False,
) -> BenchmarkResult:
    task_results: list[TaskBenchmark] = []
    all_scores: list[float] = []

    for task_id in task_ids:
        print(f"\n{'─' * 50}")
        print(f"  Benchmarking {task_id.upper()} ({len(seeds)} seeds)")
        print(f"{'─' * 50}")

        scores: list[float] = []
        completions: list[bool] = []

        for seed in seeds:
            print(f"  → seed={seed} ...", end="", flush=True)
            try:
                _, score = run_single(task_id, seed, llm, verbose=verbose)
                scores.append(score.total)
                completions.append(score.task_completion == 1.0)
                print(f" score={score.total:.3f} {'✓' if score.task_completion == 1.0 else '✗'}")
            except Exception as e:
                print(f" ERROR: {e}")
                scores.append(0.0)
                completions.append(False)

        mean = statistics.mean(scores)
        std = statistics.stdev(scores) if len(scores) > 1 else 0.0
        completion_rate = sum(completions) / len(completions)
        all_scores.extend(scores)

        task_results.append(TaskBenchmark(
            task_id=task_id,
            seeds=seeds,
            scores=scores,
            completions=completions,
            mean=round(mean, 4),
            std=round(std, 4),
            completion_rate=round(completion_rate, 4),
        ))

    overall_mean = statistics.mean(all_scores) if all_scores else 0.0
    overall_std = statistics.stdev(all_scores) if len(all_scores) > 1 else 0.0

    return BenchmarkResult(
        tasks=task_results,
        overall_mean=round(overall_mean, 4),
        overall_std=round(overall_std, 4),
        pass_threshold=pass_threshold,
    )


def print_benchmark_report(result: BenchmarkResult) -> None:
    bar = "=" * 60
    print(f"\n{bar}")
    print(f"  BENCHMARK REPORT")
    print(bar)
    print(f"\n  {'Task':<8} {'Mean':>8} {'±Std':>8} {'Complete':>10}  Seeds")
    print(f"  {'─'*8} {'─'*8} {'─'*8} {'─'*10}  {'─'*20}")

    for t in result.tasks:
        seed_scores = "  ".join(f"{s:.3f}" for s in t.scores)
        print(
            f"  {t.task_id.upper():<8} {t.mean:>8.3f} {t.std:>8.3f}"
            f" {t.completion_rate:>9.0%}  [{seed_scores}]"
        )

    print(f"  {'─'*50}")
    print(f"  {'OVERALL':<8} {result.overall_mean:>8.3f} {result.overall_std:>8.3f}")
    threshold_met = result.overall_mean >= result.pass_threshold
    status = "✓ PASS" if threshold_met else "✗ FAIL"
    print(f"\n  Threshold: {result.pass_threshold:.2f}  →  {status}")
    print(f"{bar}\n")


def write_benchmark_report(result: BenchmarkResult, path: str) -> None:
    lines = [
        "# Benchmark Report",
        "",
        f"| Task | Mean | ±Std | Completion | Scores |",
        "|---|---|---|---|---|",
    ]
    for t in result.tasks:
        seed_scores = " / ".join(f"{s:.3f}" for s in t.scores)
        lines.append(
            f"| {t.task_id.upper()} | {t.mean:.3f} | {t.std:.3f}"
            f" | {t.completion_rate:.0%} | {seed_scores} |"
        )
    lines += [
        "",
        f"**Overall mean:** {result.overall_mean:.3f} ± {result.overall_std:.3f}",
        f"**Pass threshold:** {result.pass_threshold:.2f}",
        f"**Status:** {'PASS' if result.overall_mean >= result.pass_threshold else 'FAIL'}",
    ]
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="THE AMNESIAC benchmark runner")
    parser.add_argument(
        "--tasks", nargs="+", default=TASK_IDS,
        choices=TASK_IDS, help="Tasks to benchmark (default: all)"
    )
    parser.add_argument(
        "--seeds", nargs="+", type=int, default=DEFAULT_SEEDS,
        help="RNG seeds (default: 42 7 137)"
    )
    parser.add_argument("--provider", default="anthropic", choices=["anthropic", "openai"])
    parser.add_argument("--model", default=None)
    parser.add_argument("--temperature", type=float, default=0.3)
    parser.add_argument("--api-key", default=None, dest="api_key")
    parser.add_argument("--threshold", type=float, default=0.75)
    parser.add_argument("--report", default=None, help="Write markdown report to this path")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    from dotenv import load_dotenv
    load_dotenv()

    llm = LLMClient(
        provider=args.provider,
        model=args.model,
        temperature=args.temperature,
        api_key=args.api_key,
    )

    result = run_benchmark(args.tasks, args.seeds, llm, args.threshold, args.verbose)
    print_benchmark_report(result)

    if args.report:
        write_benchmark_report(result, args.report)
        print(f"Report written to: {args.report}")


if __name__ == "__main__":
    main()
