from __future__ import annotations

from typing import TYPE_CHECKING

from world.rooms import DIR_DELTA, COMPASS_8

if TYPE_CHECKING:
    from world.engine import WorldEngine


_OPPOSITE = {
    "NORTH": "SOUTH", "SOUTH": "NORTH",
    "EAST": "WEST", "WEST": "EAST",
    "NE": "SW", "SW": "NE", "NW": "SE", "SE": "NW",
}


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
        dx, dy = DIR_DELTA[label]
        nx, ny = s.agent_x + dx, s.agent_y + dy
        cell_desc = _describe_cell(engine, s.agent_room, nx, ny, s.agent_x, s.agent_y)
        lines.append(f"{label}: {cell_desc}")
    lines.append(f"CELL: {_current_cell_desc(engine, s.agent_room, s.agent_x, s.agent_y)}")

    nearby = _nearby_objects(engine, s.agent_room, s.agent_x, s.agent_y, radius=3)
    if nearby:
        lines.append("")
        lines.append("[NEARBY OBJECTS]")
        for desc in nearby:
            lines.append(f"  {desc}")

    lines.append("")
    lines.append("[INVENTORY]")
    if s.inventory:
        for item_id in s.inventory:
            weight = "?"
            fragile_tag = ""
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
    goal_text = engine.goal_description()
    lines.append(f"  {goal_text}")

    lines.append("")
    lines.append("=== END OBSERVATION ===")

    return "\n".join(lines)


def _describe_cell(engine: "WorldEngine", room_id: str, x: int, y: int, from_x: int, from_y: int) -> str:
    s = engine.get_state()
    room = s.rooms[room_id]

    if not room.in_bounds(x, y):
        return "out of bounds"

    door = _door_at_pos(engine, room_id, x, y)
    if door is not None:
        other = door.other_room(room_id)
        other_name = s.rooms[other].name
        state_tag = "LOCKED" if door.locked else "open"
        return f"door → {other_name} [{state_tag}] ({door.door_id})"

    if room.is_wall(x, y):
        return "wall"

    obj = _object_at_pos(engine, room_id, x, y)
    if obj is not None:
        return f"{obj.obj_id} at ({x},{y})"

    return "floor"


def _current_cell_desc(engine: "WorldEngine", room_id: str, x: int, y: int) -> str:
    door = _door_at_pos(engine, room_id, x, y)
    if door is not None:
        return "door threshold"
    return "floor"


def _nearby_objects(engine: "WorldEngine", room_id: str, ax: int, ay: int, radius: int) -> list[str]:
    s = engine.get_state()
    result = []
    for obj in s.objects.values():
        if obj.room_id != room_id:
            continue
        dist = max(abs(obj.x - ax), abs(obj.y - ay))
        if 1 < dist <= radius:
            result.append(f"{obj.obj_id} at ({obj.x},{obj.y})")
    return result


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
