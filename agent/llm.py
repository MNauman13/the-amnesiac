from __future__ import annotations

import os
import time
import threading
from dataclasses import dataclass
from typing import Callable


@dataclass
class LLMResponse:
    content: str
    input_tokens: int
    output_tokens: int
    model: str
    latency_ms: float


class TimeoutError(Exception):
    pass


def _call_with_timeout(fn: Callable, timeout_sec: float):
    result: list = [None]
    error: list = [None]

    def target():
        try:
            result[0] = fn()
        except Exception as e:
            error[0] = e

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(timeout_sec)

    if thread.is_alive():
        raise TimeoutError(f"LLM call timed out after {timeout_sec}s")
    if error[0] is not None:
        raise error[0]
    return result[0]


class LLMClient:
    def __init__(
        self,
        provider: str = "anthropic",
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 800,
        timeout_sec: float = 30.0,
        api_key: str | None = None,
    ) -> None:
        self.provider = provider.lower()
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout_sec = timeout_sec

        if self.provider == "anthropic":
            self.model = model or "claude-sonnet-4-6"
            self._client = self._init_anthropic(api_key)
        elif self.provider == "openai":
            self.model = model or "gpt-4o"
            self._client = self._init_openai(api_key)
        else:
            raise ValueError(f"Unsupported provider: {provider}. Use 'anthropic' or 'openai'.")

    def _init_anthropic(self, api_key: str | None):
        try:
            import anthropic
        except ImportError as e:
            raise ImportError("anthropic package not installed. Run: pip install anthropic") from e
        key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        return anthropic.Anthropic(api_key=key)

    def _init_openai(self, api_key: str | None):
        try:
            import openai
        except ImportError as e:
            raise ImportError("openai package not installed. Run: pip install openai") from e
        key = api_key or os.environ.get("OPENAI_API_KEY", "")
        return openai.OpenAI(api_key=key)

    def call(self, system_prompt: str, user_message: str) -> LLMResponse:
        start = time.monotonic()
        if self.provider == "anthropic":
            fn = lambda: self._call_anthropic(system_prompt, user_message, start)
        else:
            fn = lambda: self._call_openai(system_prompt, user_message, start)

        return _call_with_timeout(fn, self.timeout_sec)

    def _call_anthropic(self, system_prompt: str, user_message: str, start: float) -> LLMResponse:
        import anthropic
        response = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": user_message}],
        )
        latency = (time.monotonic() - start) * 1000
        return LLMResponse(
            content=response.content[0].text,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            model=self.model,
            latency_ms=latency,
        )

    def _call_openai(self, system_prompt: str, user_message: str, start: float) -> LLMResponse:
        response = self._client.chat.completions.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )
        latency = (time.monotonic() - start) * 1000
        choice = response.choices[0]
        usage = response.usage
        return LLMResponse(
            content=choice.message.content or "",
            input_tokens=usage.prompt_tokens,
            output_tokens=usage.completion_tokens,
            model=self.model,
            latency_ms=latency,
        )


SYSTEM_PROMPT = """You are an agent operating in a virtual world.
You have NO memory of previous steps. Your only memory is the SCROLL shown before the observation.

Each step you MUST output exactly two things in this exact format:

ACTION: <one action from the action space>

MEMORY_UPDATE:
<your updated scroll — max 2048 bytes>

Available actions:
  MOVE NORTH/SOUTH/EAST/WEST   — move one cell in a cardinal direction
  TURN <direction>             — change facing without moving
  PICKUP <object_id>           — pick up object within 3 cells
  DROP <object_id>             — drop item in current cell
  USE <object_id> ON <target>  — use item on target (e.g. USE KEY_BLUE ON DOOR_1)
  INSPECT <object_id>          — examine object in range
  WAIT                         — skip turn (world dynamics still tick)

Memory rules:
  - Your scroll is COMPLETELY OVERWRITTEN every step. No undo.
  - Think: what does your future amnesiac self NEED to know?
  - Drop outdated facts. Keep landmarks, goals, dynamic warnings.
  - Doors need their matching key: USE KEY_ID ON DOOR_ID when adjacent.
  - You can only PICKUP objects within 3 cells (Manhattan distance).

--- EXAMPLE (Task: find key, unlock door) ---

Step 1 response:
ACTION: MOVE EAST

MEMORY_UPDATE:
[GOAL] Find KEY_BLUE → use on DOOR_1 → enter Hallway A
[MAP] Library: starting room. Unexplored. Sweeping E then N.
[STATE] No key yet. Door location unknown.

Step 8 response (after spotting KEY_BLUE):
ACTION: PICKUP KEY_BLUE

MEMORY_UPDATE:
[GOAL] Have KEY_BLUE ✓ → find DOOR_1 → unlock → enter Hallway A
[MAP] Library(1,1)=start. Corridor SOUTH(3,5)→DOOR_1→HallwayA
[STATE] KEY_BLUE in hand. DOOR_1 re-locks every ~8 steps — act fast.
[STEP] 8 — picked up key

--- END EXAMPLE ---

Output the ACTION line first, then MEMORY_UPDATE. Nothing else."""
