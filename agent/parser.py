from __future__ import annotations

import re
from dataclasses import dataclass


VALID_DIRECTIONS = {"NORTH", "SOUTH", "EAST", "WEST"}
VALID_TURN_DIRS = {"NORTH", "SOUTH", "EAST", "WEST", "NE", "NW", "SE", "SW"}


@dataclass
class Action:
    verb: str
    args: list[str]
    raw: str

    def __str__(self) -> str:
        return self.raw


@dataclass
class ParseResult:
    action: Action | None
    memory_update: str | None
    parse_error: str | None

    @property
    def ok(self) -> bool:
        return self.parse_error is None and self.action is not None


_ACTION_RE = re.compile(
    r"ACTION\s*:\s*(.+?)(?=\nMEMORY_UPDATE|\Z)",
    re.DOTALL | re.IGNORECASE,
)
_MEMORY_RE = re.compile(
    r"MEMORY_UPDATE\s*:\s*(.*)",
    re.DOTALL | re.IGNORECASE,
)


def parse_response(raw: str) -> ParseResult:
    action_match = _ACTION_RE.search(raw)
    memory_match = _MEMORY_RE.search(raw)

    if not action_match:
        return ParseResult(None, None, "Missing ACTION field in response.")

    action_raw = action_match.group(1).strip().split("\n")[0].strip()
    action = _parse_action(action_raw)
    if action is None:
        return ParseResult(None, None, f"Could not parse action: '{action_raw}'")

    validation_error = _validate_action(action)
    if validation_error:
        return ParseResult(None, None, validation_error)

    memory_content = None
    if memory_match:
        memory_content = memory_match.group(1).strip()

    if not memory_content:
        return ParseResult(action, "", "Missing or empty MEMORY_UPDATE field.")

    return ParseResult(action, memory_content, None)


def _parse_action(text: str) -> Action | None:
    text = text.strip().upper()
    if not text:
        return None

    parts = text.split()
    verb = parts[0]
    args = parts[1:]

    if verb == "WAIT":
        return Action("WAIT", [], "WAIT")

    if verb in ("MOVE", "TURN"):
        return Action(verb, args, text)

    if verb == "PICKUP":
        return Action("PICKUP", args, text)

    if verb == "DROP":
        return Action("DROP", args, text)

    if verb == "USE":
        on_idx = args.index("ON") if "ON" in args else -1
        if on_idx == -1:
            return None
        obj = " ".join(args[:on_idx])
        target = " ".join(args[on_idx + 1 :])
        return Action("USE", [obj, target], text)

    if verb == "INSPECT":
        return Action("INSPECT", args, text)

    return None


def _validate_action(action: Action) -> str | None:
    verb = action.verb
    args = action.args

    if verb == "MOVE":
        if not args or args[0] not in VALID_DIRECTIONS:
            return f"MOVE requires a cardinal direction (NORTH/SOUTH/EAST/WEST), got: {' '.join(args) or 'nothing'}"

    elif verb == "TURN":
        if not args or args[0] not in VALID_TURN_DIRS:
            return f"TURN requires a direction, got: {' '.join(args) or 'nothing'}"

    elif verb == "PICKUP":
        if not args:
            return "PICKUP requires an object ID."

    elif verb == "DROP":
        if not args:
            return "DROP requires an object ID."

    elif verb == "USE":
        if len(args) < 2 or not args[0] or not args[1]:
            return "USE requires: USE <object_id> ON <target_id>"

    elif verb == "INSPECT":
        if not args:
            return "INSPECT requires an object ID."

    return None
