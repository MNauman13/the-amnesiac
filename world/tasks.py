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


def goal_status_lines(state: "WorldState", spec: GoalSpec) -> list[str]:
    """Generate dynamic goal-reminder lines with current progress."""
    lines = [spec.description]

    match spec.goal_type:
        case "collect_fragments_at_zone":
            fragments: list[str] = spec.params["fragments"]
            zone_room = spec.params["zone_room"]
            zone_pos = spec.params.get("zone_pos")
            collected = [f for f in fragments if f in state.inventory]
            remaining = [f for f in fragments if f not in state.inventory]
            lines.append(
                f"Fragments collected: {len(collected)}/{len(fragments)}"
                + (f" ({', '.join(collected)})" if collected else " (none yet)")
            )
            if remaining:
                lines.append(f"Still needed: {', '.join(remaining)}")
            zone_name = state.rooms[zone_room].name if zone_room in state.rooms else zone_room
            pos_str = f" Cell: {tuple(zone_pos)}" if zone_pos else ""
            lines.append(f"Assembly Zone: {zone_name}{pos_str}")

        case "reach_room":
            target = spec.params["target_room"]
            room_name = state.rooms[target].name if target in state.rooms else target
            if state.agent_room == target:
                lines.append("✓ You have reached the target room!")
            else:
                lines.append(f"Target room: {room_name} (not yet reached)")

        case "visit_all_rooms":
            required = set(spec.params.get("room_ids", list(state.rooms.keys())))
            visited = state.visited_rooms & required
            unvisited = required - visited
            lines.append(f"Rooms visited: {len(visited)}/{len(required)}")
            if unvisited:
                names = [state.rooms[r].name for r in unvisited if r in state.rooms]
                lines.append(f"Unvisited: {', '.join(names)}")

        case "pickup_item":
            item_id = spec.params["item_id"]
            if item_id in state.inventory:
                lines.append(f"✓ {item_id} picked up!")
            elif item_id in state.objects:
                obj = state.objects[item_id]
                loc = f"({obj.x},{obj.y}) in {state.rooms[obj.room_id].name}"
                lines.append(f"{item_id} last seen at {loc}")
            else:
                lines.append(f"{item_id} location unknown — check surroundings")

        case "reach_with_item_timed":
            item_id = spec.params["item_id"]
            target_room = spec.params["target_room"]
            max_steps = spec.params.get("max_steps", state.max_steps)
            steps_left = max_steps - state.step
            target_name = state.rooms[target_room].name if target_room in state.rooms else target_room
            lines.append(f"Steps remaining: {steps_left}/{max_steps}")
            has_item = item_id in state.inventory
            lines.append(f"{item_id}: {'✓ in inventory' if has_item else '✗ not picked up yet'}")
            if not has_item:
                lines.append(f"Target room: {target_name}")

    return lines


def parse_goal_spec(raw: dict) -> GoalSpec:
    return GoalSpec(
        goal_type=raw["type"],
        description=raw.get("description", ""),
        params={k: v for k, v in raw.items() if k not in ("type", "description")},
    )
