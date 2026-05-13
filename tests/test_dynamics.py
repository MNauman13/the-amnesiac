import os
import sys
import random
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from world.engine import WorldEngine
from world.dynamics import (
    DynamicsConfig,
    apply_object_drift,
    apply_door_relock,
    apply_room_shuffle,
    apply_adversarial_events,
)


FOUR_ROOM_CONFIG = {
    "rooms": [
        {
            "id": "hub", "name": "Hub", "width": 5, "height": 5,
            "grid": [
                ["wall","wall","floor","wall","wall"],
                ["wall","floor","floor","floor","wall"],
                ["floor","floor","floor","floor","floor"],
                ["wall","floor","floor","floor","wall"],
                ["wall","wall","floor","wall","wall"],
            ],
        },
        {
            "id": "north", "name": "North", "width": 5, "height": 3,
            "grid": [
                ["wall","wall","wall","wall","wall"],
                ["wall","floor","floor","floor","wall"],
                ["wall","wall","floor","wall","wall"],
            ],
        },
        {
            "id": "east", "name": "East", "width": 3, "height": 5,
            "grid": [
                ["wall","floor","wall"],
                ["wall","floor","floor"],
                ["wall","floor","wall"],
                ["wall","floor","floor"],
                ["wall","floor","wall"],
            ],
        },
    ],
    "doors": [
        {"id": "D_HN", "room_a": "hub", "room_b": "north", "pos_a": [2,0], "pos_b": [2,2], "locked": False},
        {"id": "D_HE", "room_a": "hub", "room_b": "east", "pos_a": [4,2], "pos_b": [0,2], "locked": False},
    ],
    "objects": [
        {"id": "TOKEN_1", "type": "token", "x": 2, "y": 2, "room": "hub", "weight": 1}
    ],
    "agent": {"start_room": "hub", "start_x": 1, "start_y": 1, "facing": "NORTH"},
    "goal": {"type": "pickup_item", "item_id": "TOKEN_1", "description": "Pick up TOKEN_1"},
    "max_steps": 50,
    "dynamics": {},
}


class TestObjectDrift:
    def test_drift_moves_object(self):
        engine = WorldEngine(FOUR_ROOM_CONFIG, seed=1)
        state = engine.get_state()
        old_x, old_y = state.objects["TOKEN_1"].x, state.objects["TOKEN_1"].y
        cfg = DynamicsConfig(object_drift_enabled=True, object_drift_interval=1, object_drift_ids=["TOKEN_1"])
        events = apply_object_drift(state, cfg, random.Random(1))
        new_x, new_y = state.objects["TOKEN_1"].x, state.objects["TOKEN_1"].y
        assert (new_x, new_y) != (old_x, old_y) or len(events) == 0

    def test_drift_skipped_for_absent_object(self):
        engine = WorldEngine(FOUR_ROOM_CONFIG, seed=1)
        cfg = DynamicsConfig(object_drift_enabled=True, object_drift_ids=["GHOST"])
        events = apply_object_drift(engine.get_state(), cfg, random.Random(1))
        assert events == []

    def test_drift_event_message_format(self):
        engine = WorldEngine(FOUR_ROOM_CONFIG, seed=2)
        state = engine.get_state()
        state.objects["TOKEN_1"].x = 2
        state.objects["TOKEN_1"].y = 2
        cfg = DynamicsConfig(object_drift_enabled=True, object_drift_ids=["TOKEN_1"])
        events = apply_object_drift(state, cfg, random.Random(0))
        if events:
            assert "TOKEN_1" in events[0]
            assert "drifted" in events[0]


class TestDoorRelock:
    def test_relock_locks_open_door(self):
        engine = WorldEngine(FOUR_ROOM_CONFIG, seed=1)
        state = engine.get_state()
        state.doors["D_HN"].locked = False
        cfg = DynamicsConfig(door_relock_enabled=True, door_relock_ids=["D_HN"])
        apply_door_relock(state, cfg, random.Random(1))
        assert state.doors["D_HN"].locked

    def test_relock_does_not_double_lock(self):
        engine = WorldEngine(FOUR_ROOM_CONFIG, seed=1)
        state = engine.get_state()
        state.doors["D_HN"].locked = True
        cfg = DynamicsConfig(door_relock_enabled=True, door_relock_ids=["D_HN"])
        events = apply_door_relock(state, cfg, random.Random(1))
        assert events == []


class TestRoomShuffle:
    def test_shuffle_changes_door_destination(self):
        engine = WorldEngine(FOUR_ROOM_CONFIG, seed=1)
        state = engine.get_state()
        orig_b_1 = state.doors["D_HN"].room_b
        orig_b_2 = state.doors["D_HE"].room_b
        cfg = DynamicsConfig(room_shuffle_enabled=True, room_shuffle_door_ids=["D_HN", "D_HE"])
        events = apply_room_shuffle(state, cfg, random.Random(5))
        new_b_1 = state.doors["D_HN"].room_b
        new_b_2 = state.doors["D_HE"].room_b
        assert events
        assert new_b_1 != orig_b_1 or new_b_2 != orig_b_2

    def test_shuffle_event_message_format(self):
        engine = WorldEngine(FOUR_ROOM_CONFIG, seed=1)
        state = engine.get_state()
        cfg = DynamicsConfig(room_shuffle_enabled=True, room_shuffle_door_ids=["D_HN", "D_HE"])
        events = apply_room_shuffle(state, cfg, random.Random(3))
        assert any("CORRIDOR REROUTED" in e for e in events)

    def test_shuffle_needs_two_doors(self):
        engine = WorldEngine(FOUR_ROOM_CONFIG, seed=1)
        cfg = DynamicsConfig(room_shuffle_enabled=True, room_shuffle_door_ids=["D_HN"])
        events = apply_room_shuffle(engine.get_state(), cfg, random.Random(1))
        assert events == []


class TestAdversarialEvents:
    def test_adversarial_produces_events_at_high_rate(self):
        engine = WorldEngine(FOUR_ROOM_CONFIG, seed=1)
        cfg = DynamicsConfig(adversarial_enabled=True, adversarial_false_event_rate=1.0)
        events = apply_adversarial_events(engine.get_state(), cfg, random.Random(1))
        assert len(events) >= 1

    def test_adversarial_skips_at_zero_rate(self):
        engine = WorldEngine(FOUR_ROOM_CONFIG, seed=1)
        cfg = DynamicsConfig(adversarial_enabled=True, adversarial_false_event_rate=0.0)
        events = apply_adversarial_events(engine.get_state(), cfg, random.Random(1))
        assert events == []

    def test_adversarial_events_tagged_unverified(self):
        engine = WorldEngine(FOUR_ROOM_CONFIG, seed=1)
        cfg = DynamicsConfig(adversarial_enabled=True, adversarial_false_event_rate=1.0)
        for seed in range(10):
            events = apply_adversarial_events(engine.get_state(), cfg, random.Random(seed))
            for ev in events:
                assert "[UNVERIFIED]" in ev


class TestT6Config:
    def test_t6_loads_and_has_shuffle(self):
        import json
        path = os.path.join(os.path.dirname(__file__), "..", "tasks", "t6_labyrinth.json")
        with open(path) as f:
            cfg = json.load(f)
        engine = WorldEngine(cfg, seed=0)
        assert engine.get_state().step == 0
        assert cfg["dynamics"]["room_shuffle"]["enabled"]
        assert len(engine.get_state().rooms) == 4

    def test_t6_shuffle_fires_at_interval(self):
        import json
        path = os.path.join(os.path.dirname(__file__), "..", "tasks", "t6_labyrinth.json")
        with open(path) as f:
            cfg = json.load(f)
        engine = WorldEngine(cfg, seed=7)
        initial_connections = {
            d_id: (d.room_a, d.room_b) for d_id, d in engine.get_state().doors.items()
        }
        for _ in range(10):
            engine.tick()
        final_connections = {
            d_id: (d.room_a, d.room_b) for d_id, d in engine.get_state().doors.items()
        }
        assert initial_connections != final_connections


class TestGoalStatusLines:
    def test_fragment_goal_shows_remaining(self):
        import json
        path = os.path.join(os.path.dirname(__file__), "..", "tasks", "t2_fragment_assembly.json")
        with open(path) as f:
            cfg = json.load(f)
        engine = WorldEngine(cfg, seed=0)
        lines = engine.goal_status_lines()
        combined = " ".join(lines)
        assert "0/4" in combined or "Still needed" in combined

    def test_visit_goal_shows_unvisited(self):
        import json
        path = os.path.join(os.path.dirname(__file__), "..", "tasks", "t4_cartographer.json")
        with open(path) as f:
            cfg = json.load(f)
        engine = WorldEngine(cfg, seed=0)
        lines = engine.goal_status_lines()
        combined = " ".join(lines)
        assert "Unvisited" in combined or "visited" in combined.lower()
