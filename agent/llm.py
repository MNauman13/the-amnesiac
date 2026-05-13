from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMResponse:
    content: str
    input_tokens: int
    output_tokens: int
    model: str
    latency_ms: float


class LLMClient:
    def __init__(
        self,
        provider: str = "anthropic",
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 800,
        api_key: str | None = None,
    ) -> None:
        self.provider = provider.lower()
        self.temperature = temperature
        self.max_tokens = max_tokens

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
            return self._call_anthropic(system_prompt, user_message, start)
        return self._call_openai(system_prompt, user_message, start)

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
You have NO memory of previous steps. Your only memory is the SCROLL shown in the observation.

Each step you MUST output exactly two things in this exact format:

ACTION: <one action from the action space>

MEMORY_UPDATE:
<your updated scroll — max 2048 bytes>

Available actions:
  MOVE NORTH/SOUTH/EAST/WEST   — move one cell
  TURN <direction>             — change facing without moving
  PICKUP <object_id>           — pick up nearby object
  DROP <object_id>             — drop item in current cell
  USE <object_id> ON <target>  — use item on target (e.g. key on door)
  INSPECT <object_id>          — examine object in range
  WAIT                         — skip turn

Rules:
- Your scroll is overwritten every step. There is no undo. Curate wisely.
- Think: what does your future self NEED to know? What can be discarded?
- If you skip MEMORY_UPDATE you will be penalised.
- Doors require their matching key to unlock (USE KEY ON DOOR).
- You can only pick up objects within 3 cells of your position.
- Output the ACTION line first, then MEMORY_UPDATE. Nothing else."""
