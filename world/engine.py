from __future__ import annotations

import copy
import random
from dataclasses import dataclass, field
from typing import Optional

from world.rooms import Direction, DIR_DELTA, ObjectType, Room, Door, WorldObject
from world.dynamics import DynamicsConfig, parse_dynamics_config, tick_dynamics
from world.tasks import GoalSpec, parse_goal_spec, check_goal


@dataclass
class WorldEvent:
    description: str


@dataclass
class ActionResult:
    success: bool
    message: str


@dataclass
class WorldState:
    rooms: dict[str, Room]
    objects: dict[str, WorldObject]
    doors: dict[str, Door]
    inventory: list[str]
    carried: dict[str, WorldObject] = field(default_factory=dict)
    agent_room: str = ""
    agent_x: int = 0
    agent_y: int = 0
    agent_facing: str = "NORTH"
    step: int = 0
    max_steps: int = 200
    visited_rooms: set[str] = field(default_factory=set)
    pending_inspect: Optional[str] = None


class WorldEngine:
    def __init__(self, task_config: dict, seed: int = 42):
        self._rng = random.Random(seed)
        self.state, self._dynamics, self._goal = self._load(task_config)
        self._events: list[WorldEvent] = []
        self.state.visited_rooms.add(self.state.agent_room)
        self._optimal_steps: int = task_config.get("optimal_steps", 0)

    def _load(self, cfg: dict) -> tuple[WorldState, DynamicsConfig, GoalSpec]:
        rooms: dict[str, Room] = {}
        for r in cfg["rooms"]:
            rooms[r["id"]] = Room(
                room_id=r["id"],
                name=r["name"],
                width=r["width"],
                height=r["height"],
                grid=r["grid"],
            )

        doors: dict[str, Door] = {}
        for d in cfg.get("doors", []):
            door = Door(
                door_id=d["id"],
                room_a=d["room_a"],
                room_b=d["room_b"],
                pos_a=tuple(d["pos_a"]),
                pos_b=tuple(d["pos_b"]),
                locked=d.get("locked", False),
                required_key_type=d.get("required_key_type"),
            )
            doors[d["id"]] = door
            rooms[d["room_a"]].connected_doors.append(d["id"])
            rooms[d["room_b"]].connected_doors.append(d["id"])

        objects: dict[str, WorldObject] = {}
        for o in cfg.get("objects", []):
            objects[o["id"]] = WorldObject(
                obj_id=o["id"],
                obj_type=ObjectType(o["type"]),
                x=o["x"],
                y=o["y"],
                room_id=o["room"],
                weight=o.get("weight", 1),
                fragile=o.get("fragile", False),
                properties=o.get("properties", {}),
            )

        agent = cfg["agent"]
        state = WorldState(
            rooms=rooms,
            objects=objects,
            doors=doors,
            inventory=[],
            carried={},
            agent_room=agent["start_room"],
            agent_x=agent["start_x"],
            agent_y=agent["start_y"],
            agent_facing=agent.get("facing", "NORTH"),
            step=0,
            max_steps=cfg.get("max_steps", 200),
        )

        dynamics = parse_dynamics_config(cfg.get("dynamics", {}))
        goal = parse_goal_spec(cfg["goal"])
        return state, dynamics, goal

    def get_state(self) -> WorldState:
        return self.state

    def get_events(self) -> list[WorldEvent]:
        return list(self._events)

    def clear_events(self) -> None:
        self._events = []

    def is_goal_complete(self) -> bool:
        complete, _ = check_goal(self.state, self._goal)
        return complete

    def goal_progress(self) -> float:
        _, progress = check_goal(self.state, self._goal)
        return progress

    def goal_description(self) -> str:
        return self._goal.description

    def optimal_steps(self) -> int:
        return self._optimal_steps

    def _door_at(self, room_id: str, x: int, y: int) -> Optional[Door]:
        for door in self.state.doors.values():
            if door.position_in(room_id) == (x, y):
                return door
        return None

    def _object_at(self, room_id: str, x: int, y: int) -> Optional[WorldObject]:
        for obj in self.state.objects.values():
            if obj.room_id == room_id and obj.x == x and obj.y == y:
                return obj
        return None

    def execute_action(self, action: "Action") -> ActionResult:
        s = self.state
        result = self._dispatch(action)
        return result

    def _dispatch(self, action: "Action") -> ActionResult:
        verb = action.verb
        args = action.args
        s = self.state

        if verb == "MOVE":
            return self._move(args[0] if args else "")

        if verb == "TURN":
            return self._turn(args[0] if args else "")

        if verb == "PICKUP":
            return self._pickup(args[0] if args else "")

        if verb == "DROP":
            return self._drop(args[0] if args else "")

        if verb == "USE":
            obj_id = args[0] if len(args) > 0 else ""
            target_id = args[1] if len(args) > 1 else ""
            return self._use(obj_id, target_id)

        if verb == "INSPECT":
            return self._inspect(args[0] if args else "")

        if verb == "WAIT":
            return ActionResult(True, "You wait.")

        return ActionResult(False, f"Unknown action: {verb}")

    def _move(self, direction: str) -> ActionResult:
        direction = direction.upper()
        if direction not in DIR_DELTA:
            return ActionResult(False, f"Unknown direction: {direction}")
        if direction not in ("NORTH", "SOUTH", "EAST", "WEST"):
            return ActionResult(False, "MOVE only accepts cardinal directions (NORTH/SOUTH/EAST/WEST).")

        s = self.state
        dx, dy = DIR_DELTA[direction]
        nx, ny = s.agent_x + dx, s.agent_y + dy
        room = s.rooms[s.agent_room]

        if room.is_wall(nx, ny):
            door = self._door_at(s.agent_room, nx, ny)
            if door is None:
                return ActionResult(False, f"Blocked: wall to the {direction}.")
        else:
            door = self._door_at(s.agent_room, nx, ny)

        if door is not None:
            if door.locked:
                return ActionResult(
                    False,
                    f"{door.door_id} is locked. Use {door.required_key_type or 'the key'} to unlock it first.",
                )
            other = door.other_room(s.agent_room)
            dest_pos = door.position_in(other)
            s.agent_room = other
            s.agent_x, s.agent_y = dest_pos
            s.agent_facing = direction
            s.visited_rooms.add(other)
            return ActionResult(True, f"Passed through {door.door_id} into {s.rooms[other].name}.")

        if room.is_wall(nx, ny):
            return ActionResult(False, f"Blocked: wall to the {direction}.")

        s.agent_x, s.agent_y = nx, ny
        s.agent_facing = direction
        return ActionResult(True, f"Moved {direction} to ({nx},{ny}).")

    def _turn(self, direction: str) -> ActionResult:
        direction = direction.upper()
        if direction not in DIR_DELTA:
            return ActionResult(False, f"Unknown direction: {direction}")
        self.state.agent_facing = direction
        return ActionResult(True, f"Now facing {direction}.")

    def _pickup(self, obj_id: str) -> ActionResult:
        s = self.state
        if obj_id not in s.objects:
            return ActionResult(False, f"{obj_id} is not in the world or already picked up.")
        obj = s.objects[obj_id]
        if obj.room_id != s.agent_room:
            return ActionResult(False, f"{obj_id} is not in this room.")
        dist = abs(obj.x - s.agent_x) + abs(obj.y - s.agent_y)
        if dist > 3:
            return ActionResult(False, f"{obj_id} is too far away (need to be within 3 cells).")
        if len(s.inventory) >= 6:
            return ActionResult(False, "Inventory is full (max 6 items).")
        s.inventory.append(obj_id)
        s.carried[obj_id] = obj
        del s.objects[obj_id]
        return ActionResult(True, f"Picked up {obj_id}.")

    def _drop(self, obj_id: str) -> ActionResult:
        s = self.state
        if obj_id not in s.inventory:
            return ActionResult(False, f"{obj_id} is not in your inventory.")
        s.inventory.remove(obj_id)
        original = s.carried.pop(obj_id, None)
        if original is not None:
            original.x = s.agent_x
            original.y = s.agent_y
            original.room_id = s.agent_room
            s.objects[obj_id] = original
        else:
            s.objects[obj_id] = WorldObject(
                obj_id=obj_id,
                obj_type=ObjectType.TOKEN,
                x=s.agent_x,
                y=s.agent_y,
                room_id=s.agent_room,
            )
        return ActionResult(True, f"Dropped {obj_id} at ({s.agent_x},{s.agent_y}) in {s.rooms[s.agent_room].name}.")

    def _use(self, obj_id: str, target_id: str) -> ActionResult:
        s = self.state
        if obj_id not in s.inventory:
            return ActionResult(False, f"{obj_id} is not in your inventory.")

        if target_id in s.doors:
            door = s.doors[target_id]
            if not door.locked:
                return ActionResult(False, f"{target_id} is already unlocked.")
            if door.required_key_type and door.required_key_type != obj_id:
                return ActionResult(
                    False, f"{obj_id} does not unlock {target_id}. Need {door.required_key_type}."
                )
            door_pos = door.position_in(s.agent_room)
            dist = abs(door_pos[0] - s.agent_x) + abs(door_pos[1] - s.agent_y)
            if dist > 1:
                return ActionResult(False, f"You must be adjacent to {target_id} to use a key on it.")
            door.locked = False
            return ActionResult(True, f"{target_id} unlocked with {obj_id}.")

        return ActionResult(False, f"Cannot use {obj_id} on {target_id}.")

    def _inspect(self, obj_id: str) -> ActionResult:
        s = self.state
        in_inv = obj_id in s.inventory
        in_room = obj_id in s.objects and s.objects[obj_id].room_id == s.agent_room

        if not in_inv and not in_room:
            return ActionResult(False, f"{obj_id} is not visible from here.")

        if in_inv:
            desc = f"{obj_id} (in inventory)"
        else:
            obj = s.objects[obj_id]
            dist = abs(obj.x - s.agent_x) + abs(obj.y - s.agent_y)
            if dist > 3:
                return ActionResult(False, f"{obj_id} is out of inspect range.")
            desc = f"{obj_id} at ({obj.x},{obj.y}) — type: {obj.obj_type.value}"
            if obj.properties:
                props = ", ".join(f"{k}={v}" for k, v in obj.properties.items())
                desc += f" [{props}]"
            if obj.fragile:
                desc += " [FRAGILE — do not drop]"

        s.pending_inspect = desc
        return ActionResult(True, f"Inspecting {obj_id}...")

    def tick(self) -> list[WorldEvent]:
        self.state.step += 1
        new_events = tick_dynamics(self.state, self._dynamics, self._rng)
        events = [WorldEvent(e) for e in new_events]
        self._events.extend(events)
        return events
