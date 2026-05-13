import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from world.engine import WorldEngine
from agent.observation import render_observation


SIMPLE_CONFIG = {
    "rooms": [
        {
            "id": "room_a", "name": "Room A", "width": 7, "height": 5,
            "grid": [
                ["wall","wall","wall","wall","wall","wall","wall"],
                ["wall","floor","floor","floor","floor","floor","wall"],
                ["wall","floor","floor","floor","floor","floor","wall"],
                ["wall","floor","floor","floor","floor","floor","wall"],
                ["wall","wall","wall","floor","wall","wall","wall"],
            ],
        },
        {
            "id": "room_b", "name": "Room B", "width": 7, "height": 4,
            "grid": [
                ["wall","wall","wall","floor","wall","wall","wall"],
                ["wall","floor","floor","floor","floor","floor","wall"],
                ["wall","floor","floor","floor","floor","floor","wall"],
                ["wall","wall","wall","wall","wall","wall","wall"],
            ],
        },
    ],
    "doors": [
        {"id": "DOOR_1", "room_a": "room_a", "room_b": "room_b",
         "pos_a": [3, 4], "pos_b": [3, 0], "locked": True, "required_key_type": "KEY_1"}
    ],
    "objects": [
        {"id": "KEY_1", "type": "key", "x": 4, "y": 2, "room": "room_a", "weight": 0}
    ],
    "agent": {"start_room": "room_a", "start_x": 2, "start_y": 2, "facing": "NORTH"},
    "goal": {"type": "reach_room", "target_room": "room_b", "description": "Reach Room B"},
    "max_steps": 50,
    "dynamics": {},
}


def make_engine():
    return WorldEngine(SIMPLE_CONFIG, seed=0)


class TestObservationFormat:
    def test_observation_has_required_sections(self):
        engine = make_engine()
        obs = render_observation(engine)
        assert "[POSITION]" in obs
        assert "[SURROUNDINGS" in obs
        assert "[INVENTORY]" in obs
        assert "[WORLD EVENTS SINCE LAST STEP]" in obs
        assert "[GOAL REMINDER]" in obs
        assert "=== OBSERVATION" in obs
        assert "=== END OBSERVATION ===" in obs

    def test_position_shows_room_and_cell(self):
        engine = make_engine()
        obs = render_observation(engine)
        assert "Room A" in obs
        assert "(2,2)" in obs

    def test_surroundings_shows_all_8_directions(self):
        engine = make_engine()
        obs = render_observation(engine)
        for direction in ["NORTH", "NE", "EAST", "SE", "SOUTH", "SW", "WEST", "NW"]:
            assert f"{direction}:" in obs

    def test_surroundings_shows_adjacent_wall(self):
        engine = make_engine()
        engine.get_state().agent_x = 1
        engine.get_state().agent_y = 1
        obs = render_observation(engine)
        assert "wall" in obs

    def test_surroundings_detects_object_within_3_cells(self):
        engine = make_engine()
        # KEY_1 at (4,2), agent at (2,2) — 2 cells east
        obs = render_observation(engine)
        assert "KEY_1" in obs

    def test_surroundings_shows_door_as_corridor(self):
        engine = make_engine()
        engine.get_state().agent_x = 3
        engine.get_state().agent_y = 2
        obs = render_observation(engine)
        assert "corridor" in obs.lower() or "Room B" in obs

    def test_empty_inventory_shown(self):
        engine = make_engine()
        obs = render_observation(engine)
        assert "(empty)" in obs

    def test_inventory_shows_items(self):
        engine = make_engine()
        s = engine.get_state()
        s.inventory.append("KEY_1")
        obs = render_observation(engine)
        assert "KEY_1" in obs

    def test_step_counter_shown(self):
        engine = make_engine()
        engine.tick()
        obs = render_observation(engine)
        assert "Step 1" in obs

    def test_system_messages_shown(self):
        engine = make_engine()
        obs = render_observation(engine, system_messages=["PARSE_ERROR: test"])
        assert "[SYSTEM]" in obs
        assert "PARSE_ERROR" in obs

    def test_goal_reminder_is_dynamic(self):
        import json
        path = os.path.join(os.path.dirname(__file__), "..", "tasks", "t2_fragment_assembly.json")
        with open(path) as f:
            cfg = json.load(f)
        engine = WorldEngine(cfg, seed=0)
        obs = render_observation(engine)
        assert "FRAGMENT" in obs or "fragment" in obs.lower()
        assert "Assembly Zone" in obs or "zone" in obs.lower()


class TestNullMemoryScroll:
    def test_null_scroll_always_empty(self):
        from agent.null_memory import NullMemoryScroll
        m = NullMemoryScroll()
        m.write("some content")
        assert m.read() == ""
        assert m.byte_usage() == 0
        assert m.is_empty()

    def test_null_scroll_write_returns_ok(self):
        from agent.null_memory import NullMemoryScroll
        m = NullMemoryScroll()
        result = m.write("test")
        assert result.success
        assert result.bytes_used == 0

    def test_null_scroll_history_always_empty(self):
        from agent.null_memory import NullMemoryScroll
        m = NullMemoryScroll()
        for _ in range(5):
            m.write("content")
        assert m.history() == []
