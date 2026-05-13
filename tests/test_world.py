import json
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from world.engine import WorldEngine, ActionResult
from world.rooms import Door, Room, WorldObject, ObjectType
from world.tasks import check_goal, GoalSpec


MINIMAL_CONFIG = {
    "rooms": [
        {
            "id": "room_a",
            "name": "Room A",
            "width": 5,
            "height": 5,
            "grid": [
                ["wall", "wall", "wall", "wall", "wall"],
                ["wall", "floor", "floor", "floor", "wall"],
                ["wall", "floor", "floor", "floor", "wall"],
                ["wall", "floor", "floor", "floor", "wall"],
                ["wall", "wall", "wall", "floor", "wall"],
            ],
        },
        {
            "id": "room_b",
            "name": "Room B",
            "width": 5,
            "height": 5,
            "grid": [
                ["wall", "wall", "wall", "floor", "wall"],
                ["wall", "floor", "floor", "floor", "wall"],
                ["wall", "floor", "floor", "floor", "wall"],
                ["wall", "floor", "floor", "floor", "wall"],
                ["wall", "wall", "wall", "wall", "wall"],
            ],
        },
    ],
    "doors": [
        {
            "id": "DOOR_AB",
            "room_a": "room_a",
            "room_b": "room_b",
            "pos_a": [3, 4],
            "pos_b": [3, 0],
            "locked": True,
            "required_key_type": "KEY_A",
        }
    ],
    "objects": [
        {"id": "KEY_A", "type": "key", "x": 3, "y": 2, "room": "room_a", "weight": 0}
    ],
    "agent": {"start_room": "room_a", "start_x": 1, "start_y": 1, "facing": "EAST"},
    "goal": {"type": "reach_room", "target_room": "room_b", "description": "Get to Room B"},
    "max_steps": 50,
    "dynamics": {},
}


def make_engine(config=None):
    return WorldEngine(config or MINIMAL_CONFIG, seed=0)


class TestMovement:
    def test_move_onto_floor(self):
        engine = make_engine()
        result = engine.execute_action(_act("MOVE EAST"))
        assert result.success
        assert engine.get_state().agent_x == 2

    def test_move_blocked_by_wall(self):
        engine = make_engine()
        result = engine.execute_action(_act("MOVE NORTH"))
        assert not result.success

    def test_move_invalid_direction(self):
        engine = make_engine()
        result = engine.execute_action(_act("MOVE UP"))
        assert not result.success

    def test_move_through_locked_door_fails(self):
        engine = make_engine()
        _move_agent_to(engine, 3, 3)
        result = engine.execute_action(_act("MOVE SOUTH"))
        assert not result.success
        assert "locked" in result.message.lower()

    def test_move_through_unlocked_door_transitions_room(self):
        engine = make_engine()
        engine.get_state().doors["DOOR_AB"].locked = False
        _move_agent_to(engine, 3, 3)
        result = engine.execute_action(_act("MOVE SOUTH"))
        assert result.success
        assert engine.get_state().agent_room == "room_b"

    def test_turn_changes_facing(self):
        engine = make_engine()
        engine.execute_action(_act("TURN SOUTH"))
        assert engine.get_state().agent_facing == "SOUTH"

    def test_wait_always_succeeds(self):
        engine = make_engine()
        result = engine.execute_action(_act("WAIT"))
        assert result.success


class TestPickupDrop:
    def test_pickup_nearby_object(self):
        engine = make_engine()
        _move_agent_to(engine, 3, 2)
        result = engine.execute_action(_act("PICKUP KEY_A"))
        assert result.success
        assert "KEY_A" in engine.get_state().inventory
        assert "KEY_A" not in engine.get_state().objects

    def test_pickup_out_of_range_fails(self):
        engine = make_engine()
        # KEY_A is at (3,2); agent starts at (1,1) — move to the opposite corner first
        _move_agent_to(engine, 1, 3)
        result = engine.execute_action(_act("PICKUP KEY_A"))
        # Manhattan distance from (1,3) to (3,2) = 2+1 = 3, still in range.
        # Use a manually placed object far away.
        from world.rooms import WorldObject, ObjectType
        engine.get_state().objects["FAR_OBJ"] = WorldObject(
            obj_id="FAR_OBJ", obj_type=ObjectType.TOKEN, x=6, y=1,
            room_id="room_a", weight=1
        )
        _move_agent_to(engine, 1, 3)
        result = engine.execute_action(_act("PICKUP FAR_OBJ"))
        assert not result.success

    def test_pickup_nonexistent_object_fails(self):
        engine = make_engine()
        result = engine.execute_action(_act("PICKUP GHOST"))
        assert not result.success

    def test_drop_places_object_in_room(self):
        engine = make_engine()
        _move_agent_to(engine, 3, 2)
        engine.execute_action(_act("PICKUP KEY_A"))
        engine.execute_action(_act("DROP KEY_A"))
        assert "KEY_A" not in engine.get_state().inventory
        assert "KEY_A" in engine.get_state().objects

    def test_drop_item_not_in_inventory_fails(self):
        engine = make_engine()
        result = engine.execute_action(_act("DROP GHOST"))
        assert not result.success


class TestUseAction:
    def test_use_key_on_locked_door_unlocks(self):
        engine = make_engine()
        _move_agent_to(engine, 3, 2)
        engine.execute_action(_act("PICKUP KEY_A"))
        _move_agent_to(engine, 3, 3)
        result = engine.execute_action(_act("USE KEY_A ON DOOR_AB"))
        assert result.success
        assert not engine.get_state().doors["DOOR_AB"].locked

    def test_use_wrong_key_fails(self):
        engine = make_engine()
        cfg = dict(MINIMAL_CONFIG)
        cfg["objects"] = [
            {"id": "KEY_WRONG", "type": "key", "x": 2, "y": 2, "room": "room_a", "weight": 0}
        ]
        e2 = WorldEngine(cfg, seed=0)
        e2.get_state().inventory.append("KEY_WRONG")
        del e2.get_state().objects["KEY_WRONG"]
        _move_agent_to(e2, 3, 3)
        result = e2.execute_action(_act("USE KEY_WRONG ON DOOR_AB"))
        assert not result.success

    def test_use_key_too_far_fails(self):
        engine = make_engine()
        _move_agent_to(engine, 3, 2)
        engine.execute_action(_act("PICKUP KEY_A"))
        _move_agent_to(engine, 1, 1)
        result = engine.execute_action(_act("USE KEY_A ON DOOR_AB"))
        assert not result.success


class TestDynamics:
    def test_tick_increments_step(self):
        engine = make_engine()
        assert engine.get_state().step == 0
        engine.tick()
        assert engine.get_state().step == 1

    def test_door_relock_on_interval(self):
        cfg = dict(MINIMAL_CONFIG)
        cfg["doors"] = [
            {
                "id": "DOOR_AB",
                "room_a": "room_a",
                "room_b": "room_b",
                "pos_a": [3, 4],
                "pos_b": [3, 0],
                "locked": False,
                "required_key_type": "KEY_A",
            }
        ]
        cfg["dynamics"] = {
            "door_relock": {"enabled": True, "interval": 3, "door_ids": ["DOOR_AB"]}
        }
        engine = WorldEngine(cfg, seed=1)
        for _ in range(3):
            engine.tick()
        assert engine.get_state().doors["DOOR_AB"].locked


class TestGoalChecking:
    def test_reach_room_goal_false_initially(self):
        engine = make_engine()
        assert not engine.is_goal_complete()

    def test_reach_room_goal_true_after_transition(self):
        engine = make_engine()
        engine.get_state().doors["DOOR_AB"].locked = False
        _move_agent_to(engine, 3, 3)
        engine.execute_action(_act("MOVE SOUTH"))
        assert engine.is_goal_complete()

    def test_goal_progress_increases(self):
        engine = make_engine()
        assert engine.goal_progress() == 0.0
        engine.get_state().doors["DOOR_AB"].locked = False
        _move_agent_to(engine, 3, 3)
        engine.execute_action(_act("MOVE SOUTH"))
        assert engine.goal_progress() == 1.0


class TestTaskConfigs:
    @pytest.mark.parametrize("filename", [
        "t1_key_and_lock.json",
        "t2_fragment_assembly.json",
        "t3_moving_target.json",
        "t4_cartographer.json",
        "t5_relay_race.json",
    ])
    def test_task_config_loads(self, filename):
        tasks_dir = os.path.join(os.path.dirname(__file__), "..", "tasks")
        path = os.path.join(tasks_dir, filename)
        with open(path, encoding="utf-8") as f:
            cfg = json.load(f)
        engine = WorldEngine(cfg, seed=0)
        assert engine.get_state().step == 0
        assert engine.goal_description()


def _act(text: str):
    from agent.parser import parse_response, Action
    result = parse_response(f"ACTION: {text}\n\nMEMORY_UPDATE:\ntest")
    if result.action:
        return result.action
    parts = text.upper().split()
    return Action(parts[0], parts[1:], text.upper())


def _move_agent_to(engine: WorldEngine, x: int, y: int) -> None:
    engine.get_state().agent_x = x
    engine.get_state().agent_y = y
