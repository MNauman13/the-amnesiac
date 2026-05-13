from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Direction(str, Enum):
    NORTH = "NORTH"
    SOUTH = "SOUTH"
    EAST = "EAST"
    WEST = "WEST"


DIR_DELTA: dict[str, tuple[int, int]] = {
    "NORTH": (0, -1),
    "SOUTH": (0, 1),
    "EAST": (1, 0),
    "WEST": (-1, 0),
    "NE": (1, -1),
    "NW": (-1, -1),
    "SE": (1, 1),
    "SW": (-1, 1),
}

COMPASS_8 = ["NORTH", "NE", "EAST", "SE", "SOUTH", "SW", "WEST", "NW"]


class ObjectType(str, Enum):
    KEY = "key"
    FRAGMENT = "fragment"
    TOKEN = "token"
    LEVER = "lever"
    BOX = "box"
    RELIC = "relic"


@dataclass
class WorldObject:
    obj_id: str
    obj_type: ObjectType
    x: int
    y: int
    room_id: str
    weight: int = 1
    fragile: bool = False
    properties: dict = field(default_factory=dict)

    def position(self) -> tuple[int, int]:
        return (self.x, self.y)


@dataclass
class Door:
    door_id: str
    room_a: str
    room_b: str
    pos_a: tuple[int, int]
    pos_b: tuple[int, int]
    locked: bool = False
    required_key_type: Optional[str] = None

    def other_room(self, room_id: str) -> str:
        return self.room_b if room_id == self.room_a else self.room_a

    def position_in(self, room_id: str) -> tuple[int, int]:
        return self.pos_a if room_id == self.room_a else self.pos_b


@dataclass
class Room:
    room_id: str
    name: str
    width: int
    height: int
    grid: list[list[str]]
    connected_doors: list[str] = field(default_factory=list)

    def is_wall(self, x: int, y: int) -> bool:
        if not self.in_bounds(x, y):
            return True
        return self.grid[y][x] == "wall"

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height
