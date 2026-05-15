from __future__ import annotations

import argparse
import json
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def load_task(task_id: str) -> dict:
    mapping = {
        "t1": "t1_key_and_lock.json",
        "t2": "t2_fragment_assembly.json",
        "t3": "t3_moving_target.json",
        "t4": "t4_cartographer.json",
        "t5": "t5_relay_race.json",
        "t6": "t6_labyrinth.json",
    }
    path = Path(__file__).parent / "tasks" / mapping[task_id.lower()]
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def run_mode(config: dict, seed: int, llm, use_memory: bool, verbose: bool):
    from world.engine import WorldEngine
    from agent.memory import MemoryScroll
    from agent.null_memory import NullMemoryScroll
    from agent.harness import AgentHarness
    from evaluation.scorer import score_run

    engine = WorldEngine(config, seed=seed)
    memory = MemoryScroll() if use_memory else NullMemoryScroll()
    label = config["id"].lower() + ("_mem" if use_memory else "_nomem")
    harness = AgentHarness(
        engine=engine,
        llm=llm,
        memory=memory,
        log_dir=Path("logs"),
        task_id=label,
        verbose=verbose,
    )
    run_result = harness.run()
    score = score_run(run_result, engine)
    return run_result, score


def print_comparison(
    task_id: str,
    run_mem, score_mem,
    run_nomem, score_nomem,
) -> None:
    bar = "=" * 65
    print(f"\n{bar}")
    print(f"  COMPARATIVE MODE — Task: {task_id.upper()}")
    print(f"  Memory-Enabled  vs  Memory-Wiped (scroll always blank)")
    print(bar)

    def fmt(run, score):
        out = run.goal_complete
        return (
            f"  Complete:  {'✓' if out else '✗'}\n"
            f"  Score:     {score.total:.3f}  "
            f"(task={score.task_completion:.3f}, "
            f"mem={score.memory_efficiency:.3f}, "
            f"step={score.step_efficiency:.3f})\n"
            f"  Steps:     {run.total_steps}\n"
            f"  Tokens:    {run.total_tokens_in}in / {run.total_tokens_out}out"
        )

    print(f"\n  ── WITH MEMORY ──────────────────────────")
    print(fmt(run_mem, score_mem))
    print(f"\n  ── WITHOUT MEMORY ───────────────────────")
    print(fmt(run_nomem, score_nomem))

    delta_score = score_mem.total - score_nomem.total
    delta_steps = run_nomem.total_steps - run_mem.total_steps
    print(f"\n  ── DELTA (memory contribution) ──────────")
    print(f"  Score delta:  {delta_score:+.3f}  ({'memory helps' if delta_score > 0 else 'memory hurts or neutral'})")
    print(f"  Step delta:   {delta_steps:+d}  ({'fewer steps with memory' if delta_steps > 0 else 'more steps with memory'})")
    print(f"{bar}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="THE AMNESIAC — comparative mode: memory-enabled vs memory-wiped"
    )
    parser.add_argument("task", help="Task ID (t1–t6)")
    parser.add_argument("--model", default=None, help="Model override (default: claude-sonnet-4-6)")
    parser.add_argument("--temperature", type=float, default=0.3)
    parser.add_argument("--max-tokens", type=int, default=800, dest="max_tokens")
    parser.add_argument("--api-key", default=None, dest="api_key")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    from agent.llm import LLMClient
    llm = LLMClient(
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        api_key=args.api_key,
    )

    config = load_task(args.task)
    print(f"\nRunning WITH memory (seed={args.seed})...")
    run_mem, score_mem = run_mode(config, args.seed, llm, use_memory=True, verbose=args.verbose)

    print(f"\nRunning WITHOUT memory (seed={args.seed})...")
    run_nomem, score_nomem = run_mode(config, args.seed, llm, use_memory=False, verbose=args.verbose)

    print_comparison(args.task, run_mem, score_mem, run_nomem, score_nomem)


if __name__ == "__main__":
    main()
