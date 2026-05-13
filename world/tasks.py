from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from world.engine import WorldState


@dataclass
class GoalSpec:
    goal_type: str
    description: str
    params: dict = field(default_factory=dict)


def check_goal(state: "WorldState", spec: GoalSpec) -> tuple[bool, float]:
    """Returns (complete, progress_ratio in [0,1])."""
    match spec.goal_type:
        case "reach_room":
            complete = state.agent_room == spec.params["target_room"]
            return complete, 1.0 if complete else 0.0

        case "reach_room_with_items":
            target_room = spec.params["target_room"]
            required_items: list[str] = spec.params.get("items", [])
            in_room = state.agent_room == target_room
            has_items = all(item in state.inventory for item in required_items)
            if in_room and has_items:
                return True, 1.0
            collected = sum(1 for item in required_items if item in state.inventory)
            progress = (collected / max(len(required_items), 1)) * 0.9
            if in_room:
                progress += 0.1
            return False, min(progress, 0.99)

        case "collect_fragments_at_zone":
            fragments: list[str] = spec.params["fragments"]
            zone_room: str = spec.params["zone_room"]
            zone_pos: Optional[list[int]] = spec.params.get("zone_pos")

            collected = [f for f in fragments if f in state.inventory]
            if len(collected) == len(fragments):
                in_zone = state.agent_room == zone_room
                if zone_pos:
                    in_zone = in_zone and (state.agent_x, state.agent_y) == tuple(zone_pos)
                if in_zone:
                    return True, 1.0
                return False, 0.9 + (0.1 * len(collected) / len(fragments))
            return False, len(collected) / len(fragments) * 0.9

        case "pickup_item":
            target = spec.params["item_id"]
            complete = target in state.inventory
            return complete, 1.0 if complete else 0.0

        case "visit_all_rooms":
            required = set(spec.params.get("room_ids", list(state.rooms.keys())))
            visited = state.visited_rooms
            progress = len(visited & required) / len(required)
            return visited >= required, progress

        case "reach_with_item_timed":
            target_room = spec.params["target_room"]
            item_id = spec.params["item_id"]
            max_steps = spec.params.get("max_steps", state.max_steps)
            if state.step > max_steps:
                return False, 0.0
            in_room = state.agent_room == target_room
            has_item = item_id in state.inventory
            if in_room and has_item:
                return True, 1.0
            progress = 0.5 if has_item else 0.0
            return False, progress

        case _:
            return False, 0.0


def parse_goal_spec(raw: dict) -> GoalSpec:
    return GoalSpec(
        goal_type=raw["type"],
        description=raw.get("description", ""),
        params={k: v for k, v in raw.items() if k not in ("type", "description")},
    )
