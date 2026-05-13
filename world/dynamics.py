from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from world.engine import WorldState


@dataclass
class DynamicsConfig:
    object_drift_enabled: bool = False
    object_drift_interval: int = 3
    object_drift_ids: list[str] = field(default_factory=list)

    door_relock_enabled: bool = False
    door_relock_interval: int = 5
    door_relock_ids: list[str] = field(default_factory=list)

    room_shuffle_enabled: bool = False
    room_shuffle_interval: int = 10
    room_shuffle_door_ids: list[str] = field(default_factory=list)

    adversarial_enabled: bool = False
    adversarial_interval: int = 4
    adversarial_false_event_rate: float = 0.5


def _adjacent_floor_cells(state: "WorldState", room_id: str, x: int, y: int) -> list[tuple[int, int]]:
    from world.rooms import DIR_DELTA
    room = state.rooms[room_id]
    candidates = []
    for dx, dy in [DIR_DELTA[d] for d in ["NORTH", "SOUTH", "EAST", "WEST"]]:
        nx, ny = x + dx, y + dy
        if room.in_bounds(nx, ny) and not room.is_wall(nx, ny):
            occupied = any(
                o.room_id == room_id and o.x == nx and o.y == ny
                for o in state.objects.values()
            )
            if not occupied:
                candidates.append((nx, ny))
    return candidates


def apply_object_drift(state: "WorldState", config: DynamicsConfig, rng: random.Random) -> list[str]:
    events: list[str] = []
    for obj_id in config.object_drift_ids:
        if obj_id not in state.objects:
            continue
        obj = state.objects[obj_id]
        neighbors = _adjacent_floor_cells(state, obj.room_id, obj.x, obj.y)
        if not neighbors:
            continue
        old_x, old_y = obj.x, obj.y
        nx, ny = rng.choice(neighbors)
        obj.x, obj.y = nx, ny
        events.append(f"{obj_id} drifted from ({old_x},{old_y}) to ({nx},{ny})")
    return events


def apply_door_relock(state: "WorldState", config: DynamicsConfig, rng: random.Random) -> list[str]:
    events: list[str] = []
    for door_id in config.door_relock_ids:
        if door_id not in state.doors:
            continue
        door = state.doors[door_id]
        if not door.locked:
            door.locked = True
            key_room = rng.choice(list(state.rooms.keys()))
            room = state.rooms[key_room]
            floor_cells = [
                (x, y)
                for y in range(room.height)
                for x in range(room.width)
                if not room.is_wall(x, y)
                and not any(o.room_id == key_room and o.x == x and o.y == y for o in state.objects.values())
            ]
            if floor_cells and door.required_key_type:
                kx, ky = rng.choice(floor_cells)
                from world.rooms import WorldObject, ObjectType
                key_obj = WorldObject(
                    obj_id=door.required_key_type,
                    obj_type=ObjectType.KEY,
                    x=kx,
                    y=ky,
                    room_id=key_room,
                    weight=0,
                    properties={"unlocks": door_id},
                )
                state.objects[door.required_key_type] = key_obj
                events.append(
                    f"{door_id} has RE-LOCKED; {door.required_key_type} respawned in {state.rooms[key_room].name} at ({kx},{ky})"
                )
            else:
                events.append(f"{door_id} has RE-LOCKED")
    return events


def apply_room_shuffle(state: "WorldState", config: DynamicsConfig, rng: random.Random) -> list[str]:
    """Reroute connecting corridors by swapping door destinations between two random doors."""
    events: list[str] = []
    candidate_ids = config.room_shuffle_door_ids or list(state.doors.keys())
    if len(candidate_ids) < 2:
        return events

    door_a_id, door_b_id = rng.sample(candidate_ids, 2)
    door_a = state.doors[door_a_id]
    door_b = state.doors[door_b_id]

    old_a_desc = f"{state.rooms[door_a.room_a].name}↔{state.rooms[door_a.room_b].name}"
    old_b_desc = f"{state.rooms[door_b.room_a].name}↔{state.rooms[door_b.room_b].name}"

    # Swap room_b and pos_b between the two doors (reroutes where each door leads)
    door_a.room_b, door_b.room_b = door_b.room_b, door_a.room_b
    door_a.pos_b, door_b.pos_b = door_b.pos_b, door_a.pos_b

    # Update connected_doors lists in rooms
    for room in state.rooms.values():
        room.connected_doors = [
            d_id for d_id in room.connected_doors
            if d_id in state.doors
        ]

    new_a_desc = f"{state.rooms[door_a.room_a].name}↔{state.rooms[door_a.room_b].name}"
    new_b_desc = f"{state.rooms[door_b.room_a].name}↔{state.rooms[door_b.room_b].name}"

    events.append(
        f"CORRIDOR REROUTED: {door_a_id} now connects {new_a_desc} (was {old_a_desc})"
    )
    events.append(
        f"CORRIDOR REROUTED: {door_b_id} now connects {new_b_desc} (was {old_b_desc})"
    )

    # If the agent is in a room that no longer makes sense (room_b of one door),
    # teleport them to a sensible floor position in their current room
    if state.agent_room in state.rooms:
        room = state.rooms[state.agent_room]
        if not room.in_bounds(state.agent_x, state.agent_y) or room.is_wall(state.agent_x, state.agent_y):
            for y in range(room.height):
                for x in range(room.width):
                    if not room.is_wall(x, y):
                        state.agent_x, state.agent_y = x, y
                        events.append(f"You were displaced by the shuffle to ({x},{y}) in {room.name}.")
                        break

    return events


def apply_adversarial_events(state: "WorldState", config: DynamicsConfig, rng: random.Random) -> list[str]:
    """Inject plausible-sounding false world events to test memory robustness."""
    events: list[str] = []
    if rng.random() > config.adversarial_false_event_rate:
        return events

    false_event_templates = [
        lambda: f"[UNVERIFIED] {rng.choice(list(state.objects.keys()) or ['OBJ'])} may have moved",
        lambda: (f"[UNVERIFIED] DOOR_{rng.randint(1,3)} reported unlocked by passing entity"
                 if state.doors else "[UNVERIFIED] Distant sound heard"),
        lambda: f"[UNVERIFIED] Fragment spotted in {rng.choice(list(state.rooms.values())).name}",
        lambda: "[UNVERIFIED] Key glint detected — direction uncertain",
    ]

    template = rng.choice(false_event_templates)
    try:
        events.append(template())
    except Exception:
        events.append("[UNVERIFIED] Anomalous sensor reading — verify before trusting")

    return events


def tick_dynamics(state: "WorldState", config: DynamicsConfig, rng: random.Random) -> list[str]:
    events: list[str] = []
    step = state.step

    if config.object_drift_enabled and step % config.object_drift_interval == 0:
        events.extend(apply_object_drift(state, config, rng))

    if config.door_relock_enabled and step % config.door_relock_interval == 0:
        events.extend(apply_door_relock(state, config, rng))

    if config.room_shuffle_enabled and step % config.room_shuffle_interval == 0:
        events.extend(apply_room_shuffle(state, config, rng))

    if config.adversarial_enabled and step % config.adversarial_interval == 0:
        events.extend(apply_adversarial_events(state, config, rng))

    return events


def parse_dynamics_config(raw: dict) -> DynamicsConfig:
    drift = raw.get("object_drift", {})
    relock = raw.get("door_relock", {})
    shuffle = raw.get("room_shuffle", {})
    adversarial = raw.get("adversarial", {})
    return DynamicsConfig(
        object_drift_enabled=drift.get("enabled", False),
        object_drift_interval=drift.get("interval", 3),
        object_drift_ids=drift.get("object_ids", []),
        door_relock_enabled=relock.get("enabled", False),
        door_relock_interval=relock.get("interval", 5),
        door_relock_ids=relock.get("door_ids", []),
        room_shuffle_enabled=shuffle.get("enabled", False),
        room_shuffle_interval=shuffle.get("interval", 10),
        room_shuffle_door_ids=shuffle.get("door_ids", []),
        adversarial_enabled=adversarial.get("enabled", False),
        adversarial_interval=adversarial.get("interval", 4),
        adversarial_false_event_rate=adversarial.get("false_event_rate", 0.5),
    )
