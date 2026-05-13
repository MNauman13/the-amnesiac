from __future__ import annotations

from typing import TYPE_CHECKING

from world.rooms import DIR_DELTA, COMPASS_8

if TYPE_CHECKING:
    from world.engine import WorldEngine


def render_observation(engine: "WorldEngine", system_messages: list[str] | None = None) -> str:
    s = engine.get_state()
    events = engine.get_events()
    room = s.rooms[s.agent_room]
    lines: list[str] = []

    lines.append(f"=== OBSERVATION [Step {s.step} / Max {s.max_steps}] ===")
    lines.append("")

    lines.append("[POSITION]")
    lines.append(f"Room: {room.name} | Cell: ({s.agent_x},{s.agent_y}) | Facing: {s.agent_facing}")
    lines.append("")

    lines.append("[SURROUNDINGS — 3-cell radius]")
    for label in COMPASS_8:
        cell_desc = _scan_direction(engine, s.agent_room, s.agent_x, s.agent_y, label)
        lines.append(f"{label}: {cell_desc}")
    lines.append(f"CELL: {_current_cell_desc(engine, s.agent_room, s.agent_x, s.agent_y)}")

    lines.append("")
    lines.append("[INVENTORY]")
    if s.inventory:
        for item_id in s.inventory:
            obj = s.carried.get(item_id)
            weight = obj.weight if obj else "?"
            fragile_tag = " [FRAGILE — do not drop]" if obj and obj.fragile else ""
            lines.append(f"  - {item_id} (weight: {weight}){fragile_tag}")
    else:
        lines.append("  (empty)")

    lines.append("")
    lines.append("[WORLD EVENTS SINCE LAST STEP]")
    if events:
        for ev in events:
            lines.append(f"  - {ev.description}")
    else:
        lines.append("  (none)")

    if s.pending_inspect:
        lines.append("")
        lines.append("[INSPECT RESULT]")
        lines.append(f"  {s.pending_inspect}")
        s.pending_inspect = None

    if system_messages:
        lines.append("")
        lines.append("[SYSTEM]")
        for msg in system_messages:
            lines.append(f"  {msg}")

    lines.append("")
    lines.append("[GOAL REMINDER]")
    for goal_line in engine.goal_status_lines():
        lines.append(f"  {goal_line}")

    lines.append("")
    lines.append("=== END OBSERVATION ===")

    return "\n".join(lines)


def _scan_direction(engine: "WorldEngine", room_id: str, ax: int, ay: int, label: str) -> str:
    """Scan up to 3 cells in direction label; return description of first notable thing."""
    dx, dy = DIR_DELTA[label]
    s = engine.get_state()
    room = s.rooms[room_id]

    for dist in range(1, 4):
        nx, ny = ax + dx * dist, ay + dy * dist

        if not room.in_bounds(nx, ny):
            return "wall" if dist == 1 else "open space"

        door = _door_at_pos(engine, room_id, nx, ny)
        if door is not None:
            other = s.rooms[door.other_room(room_id)].name
            state_tag = "LOCKED" if door.locked else "open"
            dist_tag = f" (dist {dist})" if dist > 1 else ""
            return f"corridor → {other} [{state_tag}] ({door.door_id}){dist_tag}"

        if room.is_wall(nx, ny):
            dist_tag = f" (dist {dist})" if dist > 1 else ""
            return f"wall{dist_tag}"

        obj = _object_at_pos(engine, room_id, nx, ny)
        if obj is not None:
            dist_tag = f" (dist {dist})" if dist > 1 else ""
            return f"{obj.obj_id} at ({nx},{ny}){dist_tag}"

    return "floor"


def _current_cell_desc(engine: "WorldEngine", room_id: str, x: int, y: int) -> str:
    door = _door_at_pos(engine, room_id, x, y)
    if door is not None:
        return "door threshold"
    return "floor (standing on)"


def _door_at_pos(engine: "WorldEngine", room_id: str, x: int, y: int):
    for door in engine.get_state().doors.values():
        if door.position_in(room_id) == (x, y):
            return door
    return None


def _object_at_pos(engine: "WorldEngine", room_id: str, x: int, y: int):
    for obj in engine.get_state().objects.values():
        if obj.room_id == room_id and obj.x == x and obj.y == y:
            return obj
    return None
