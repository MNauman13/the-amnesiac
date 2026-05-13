from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def load_task(task_id: str) -> dict:
    tasks_dir = Path(__file__).parent / "tasks"
    mapping = {
        "t1": "t1_key_and_lock.json",
        "t2": "t2_fragment_assembly.json",
        "t3": "t3_moving_target.json",
        "t4": "t4_cartographer.json",
        "t5": "t5_relay_race.json",
        "t6": "t6_labyrinth.json",
    }
    key = task_id.lower()
    if key not in mapping:
        print(f"Unknown task '{task_id}'. Available: {', '.join(mapping)}")
        sys.exit(1)
    path = tasks_dir / mapping[key]
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def run(args: argparse.Namespace) -> None:
    from world.engine import WorldEngine
    from agent.memory import MemoryScroll
    from agent.llm import LLMClient
    from agent.harness import AgentHarness
    from evaluation.scorer import score_run
    from evaluation.analyser import analyse_run
    from evaluation.report import print_report, write_report

    config = load_task(args.task)
    task_id = config["id"].lower()

    if getattr(args, "adversarial", False):
        config.setdefault("dynamics", {})["adversarial"] = {
            "enabled": True, "interval": 3, "false_event_rate": 0.6
        }
        task_id += "_adversarial"

    engine = WorldEngine(config, seed=args.seed)
    memory = MemoryScroll()
    llm = LLMClient(
        provider=args.provider,
        model=args.model or None,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        api_key=args.api_key or None,
    )

    log_dir = Path("logs") if not args.no_log else None
    harness = AgentHarness(
        engine=engine,
        llm=llm,
        memory=memory,
        log_dir=log_dir,
        task_id=task_id,
        verbose=not args.quiet,
    )

    if not args.quiet:
        print(f"\nStarting Task {config['id']}: {config['name']}")
        print(f"Goal: {config['goal']['description']}")
        print(f"Max steps: {config.get('max_steps', 200)}\n")
        print(f"{'Step':<6} {'Action':<32} {'OK':<4} {'Scroll':<8} {'Progress'}")
        print("-" * 65)

    run_result = harness.run(max_steps=args.max_steps or None)

    score = score_run(run_result, engine)
    analysis = analyse_run(run_result)

    print_report(run_result, score, analysis)

    if args.report:
        write_report(run_result, score, analysis, args.report)
        print(f"Report written to: {args.report}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="THE AMNESIAC — LLM agent with self-designed memory"
    )
    parser.add_argument(
        "task",
        help="Task ID to run (t1–t6)",
    )
    parser.add_argument(
        "--adversarial", action="store_true",
        help="Enable adversarial mode: inject false events to test memory robustness",
    )
    parser.add_argument(
        "--provider",
        default="anthropic",
        choices=["anthropic", "openai"],
        help="LLM provider (default: anthropic)",
    )
    parser.add_argument("--model", default=None, help="Model override")
    parser.add_argument(
        "--temperature", type=float, default=0.3, help="LLM temperature (default: 0.3)"
    )
    parser.add_argument(
        "--max-tokens", type=int, default=800, dest="max_tokens", help="Max output tokens"
    )
    parser.add_argument("--api-key", default=None, dest="api_key", help="API key override")
    parser.add_argument(
        "--max-steps", type=int, default=None, dest="max_steps", help="Override max steps"
    )
    parser.add_argument("--seed", type=int, default=42, help="World RNG seed (default: 42)")
    parser.add_argument("--report", default=None, help="Write markdown report to this path")
    parser.add_argument("--no-log", action="store_true", dest="no_log", help="Disable JSONL logging")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress step-by-step output")

    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
