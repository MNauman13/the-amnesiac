from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from world.engine import WorldEngine, ActionResult
from agent.memory import MemoryScroll, WriteResult
from agent.observation import render_observation
from agent.parser import parse_response, ParseResult, Action
from agent.llm import LLMClient, LLMResponse, SYSTEM_PROMPT


@dataclass
class StepResult:
    step: int
    observation: str
    llm_response: str
    parse_result: ParseResult
    action_result: ActionResult
    memory_write: WriteResult | None
    scroll_before: str
    scroll_after: str
    goal_progress: float
    goal_complete: bool
    tokens_in: int
    tokens_out: int
    latency_ms: float
    system_messages: list[str] = field(default_factory=list)


@dataclass
class RunResult:
    task_id: str
    steps: list[StepResult]
    goal_complete: bool
    final_progress: float
    total_steps: int
    total_tokens_in: int
    total_tokens_out: int
    parse_errors: int
    action_failures: int


class AgentHarness:
    MAX_CONSECUTIVE_PARSE_ERRORS = 3

    def __init__(
        self,
        engine: WorldEngine,
        llm: LLMClient,
        memory: MemoryScroll,
        log_dir: Path | None = None,
        task_id: str = "unknown",
        verbose: bool = True,
    ) -> None:
        self._engine = engine
        self._llm = llm
        self._memory = memory
        self._log_dir = log_dir
        self._task_id = task_id
        self._verbose = verbose
        self._pending_system: list[str] = []
        self._consecutive_parse_errors = 0
        self._step_results: list[StepResult] = []

    def step(self) -> StepResult:
        s = self._engine.get_state()
        self._engine.clear_events()

        obs = render_observation(self._engine, self._pending_system)
        self._pending_system = []

        scroll_before = self._memory.read()
        user_message = self._build_user_message(obs, scroll_before)

        llm_resp: LLMResponse = self._llm.call(SYSTEM_PROMPT, user_message)
        parse_result: ParseResult = parse_response(llm_resp.content)

        if not parse_result.ok:
            self._consecutive_parse_errors += 1
            action = Action("WAIT", [], "WAIT")
            err = parse_result.parse_error or "Parse error"
            self._pending_system.append(f"PARSE_ERROR: {err} — WAIT substituted.")
            if self._verbose:
                print(f"  [parse error] {err}")
        else:
            self._consecutive_parse_errors = 0
            action = parse_result.action

        action_result: ActionResult = self._engine.execute_action(action)
        if not action_result.success:
            self._pending_system.append(f"ACTION_FAILED: {action_result.message}")
            if self._verbose:
                print(f"  [action failed] {action_result.message}")

        memory_write: WriteResult | None = None
        if parse_result.memory_update is not None and parse_result.memory_update.strip():
            memory_write = self._memory.write(parse_result.memory_update)
            if memory_write.truncated:
                self._pending_system.append(
                    f"MEMORY_TRUNCATED: scroll exceeded {MemoryScroll.MAX_BYTES} bytes and was cut."
                )

        tick_events = self._engine.tick()

        scroll_after = self._memory.read()
        progress = self._engine.goal_progress()
        complete = self._engine.is_goal_complete()

        result = StepResult(
            step=self._engine.get_state().step,
            observation=obs,
            llm_response=llm_resp.content,
            parse_result=parse_result,
            action_result=action_result,
            memory_write=memory_write,
            scroll_before=scroll_before,
            scroll_after=scroll_after,
            goal_progress=progress,
            goal_complete=complete,
            tokens_in=llm_resp.input_tokens,
            tokens_out=llm_resp.output_tokens,
            latency_ms=llm_resp.latency_ms,
            system_messages=list(self._pending_system),
        )

        self._step_results.append(result)
        self._log_step(result)

        if self._verbose:
            self._print_step(result)

        return result

    def run(self, max_steps: int | None = None) -> RunResult:
        limit = max_steps or self._engine.get_state().max_steps
        total_in = total_out = parse_errors = action_failures = 0

        while self._engine.get_state().step < limit:
            if self._consecutive_parse_errors >= self.MAX_CONSECUTIVE_PARSE_ERRORS:
                self._pending_system.append("TASK_FAILED: too many consecutive parse errors.")
                break

            result = self.step()
            total_in += result.tokens_in
            total_out += result.tokens_out
            if result.parse_result.parse_error:
                parse_errors += 1
            if not result.action_result.success:
                action_failures += 1

            if result.goal_complete:
                if self._verbose:
                    print(f"\n✓ Goal complete on step {result.step}!")
                break

        return RunResult(
            task_id=self._task_id,
            steps=list(self._step_results),
            goal_complete=self._engine.is_goal_complete(),
            final_progress=self._engine.goal_progress(),
            total_steps=self._engine.get_state().step,
            total_tokens_in=total_in,
            total_tokens_out=total_out,
            parse_errors=parse_errors,
            action_failures=action_failures,
        )

    def _build_user_message(self, observation: str, scroll: str) -> str:
        scroll_block = scroll if scroll.strip() else "(empty — first step)"
        return (
            f"=== YOUR MEMORY SCROLL ===\n{scroll_block}\n=== END SCROLL ===\n\n"
            f"{observation}"
        )

    def _print_step(self, r: StepResult) -> None:
        action_str = str(r.parse_result.action) if r.parse_result.action else "WAIT (parse error)"
        status = "✓" if r.action_result.success else "✗"
        mem_bytes = r.memory_write.bytes_used if r.memory_write else self._memory.byte_usage()
        print(
            f"Step {r.step:3d} | {action_str:<30} | {status} | "
            f"scroll={mem_bytes}B | progress={r.goal_progress:.2f} | "
            f"tok={r.tokens_in}+{r.tokens_out}"
        )

    def _log_step(self, r: StepResult) -> None:
        if not self._log_dir:
            return
        self._log_dir.mkdir(parents=True, exist_ok=True)
        log_file = self._log_dir / f"run_{self._task_id}.jsonl"
        record = {
            "step": r.step,
            "observation": r.observation,
            "scroll_before": r.scroll_before,
            "llm_response": r.llm_response,
            "action": str(r.parse_result.action) if r.parse_result.action else None,
            "parse_error": r.parse_result.parse_error,
            "action_result": {"success": r.action_result.success, "message": r.action_result.message},
            "scroll_after": r.scroll_after,
            "goal_progress": r.goal_progress,
            "goal_complete": r.goal_complete,
            "tokens": {"input": r.tokens_in, "output": r.tokens_out},
            "latency_ms": round(r.latency_ms, 1),
        }
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
