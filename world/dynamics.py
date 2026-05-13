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


def tick_dynamics(state: "WorldState", config: DynamicsConfig, rng: random.Random) -> list[str]:
    events: list[str] = []
    step = state.step

    if config.object_drift_enabled and step % config.object_drift_interval == 0:
        events.extend(apply_object_drift(state, config, rng))

    if config.door_relock_enabled and step % config.door_relock_interval == 0:
        events.extend(apply_door_relock(state, config, rng))

    return events


def parse_dynamics_config(raw: dict) -> DynamicsConfig:
    drift = raw.get("object_drift", {})
    relock = raw.get("door_relock", {})
    shuffle = raw.get("room_shuffle", {})
    return DynamicsConfig(
        object_drift_enabled=drift.get("enabled", False),
        object_drift_interval=drift.get("interval", 3),
        object_drift_ids=drift.get("object_ids", []),
        door_relock_enabled=relock.get("enabled", False),
        door_relock_interval=relock.get("interval", 5),
        door_relock_ids=relock.get("door_ids", []),
        room_shuffle_enabled=shuffle.get("enabled", False),
        room_shuffle_interval=shuffle.get("interval", 10),
    )
