import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agent.parser import parse_response, ParseResult, Action


class TestWellFormedResponses:
    def test_move_north(self):
        raw = "ACTION: MOVE NORTH\n\nMEMORY_UPDATE:\n[GOAL] go north\n[POS] (1,1)"
        result = parse_response(raw)
        assert result.ok
        assert result.action.verb == "MOVE"
        assert result.action.args == ["NORTH"]

    def test_pickup(self):
        raw = "ACTION: PICKUP KEY_BLUE\n\nMEMORY_UPDATE:\n[INV] key"
        result = parse_response(raw)
        assert result.ok
        assert result.action.verb == "PICKUP"
        assert result.action.args[0] == "KEY_BLUE"

    def test_use_on_syntax(self):
        raw = "ACTION: USE KEY_BLUE ON DOOR_1\n\nMEMORY_UPDATE:\nunlocked"
        result = parse_response(raw)
        assert result.ok
        assert result.action.verb == "USE"
        assert result.action.args[0] == "KEY_BLUE"
        assert result.action.args[1] == "DOOR_1"

    def test_wait(self):
        raw = "ACTION: WAIT\n\nMEMORY_UPDATE:\n[STATE] waiting"
        result = parse_response(raw)
        assert result.ok
        assert result.action.verb == "WAIT"

    def test_inspect(self):
        raw = "ACTION: INSPECT TOKEN_1\n\nMEMORY_UPDATE:\nchecking token"
        result = parse_response(raw)
        assert result.ok
        assert result.action.verb == "INSPECT"

    def test_drop(self):
        raw = "ACTION: DROP RELIC\n\nMEMORY_UPDATE:\ndropped"
        result = parse_response(raw)
        assert result.ok
        assert result.action.verb == "DROP"

    def test_turn(self):
        raw = "ACTION: TURN SOUTH\n\nMEMORY_UPDATE:\nfacing south"
        result = parse_response(raw)
        assert result.ok
        assert result.action.verb == "TURN"

    def test_memory_content_captured(self):
        memory = "[GOAL] Find key\n[MAP] Room A\n[STATE] empty handed"
        raw = f"ACTION: MOVE EAST\n\nMEMORY_UPDATE:\n{memory}"
        result = parse_response(raw)
        assert result.memory_update == memory

    def test_case_insensitive_action(self):
        raw = "action: move south\n\nMEMORY_UPDATE:\nlower case"
        result = parse_response(raw)
        assert result.ok
        assert result.action.verb == "MOVE"

    def test_extra_whitespace_around_action(self):
        raw = "ACTION:   MOVE   EAST  \n\nMEMORY_UPDATE:\nok"
        result = parse_response(raw)
        assert result.ok
        assert result.action.verb == "MOVE"
        assert result.action.args[0] == "EAST"


class TestMalformedResponses:
    def test_missing_action_field(self):
        raw = "MEMORY_UPDATE:\n[GOAL] test"
        result = parse_response(raw)
        assert not result.ok
        assert result.parse_error is not None

    def test_empty_response(self):
        result = parse_response("")
        assert not result.ok

    def test_move_without_direction(self):
        raw = "ACTION: MOVE\n\nMEMORY_UPDATE:\nno dir"
        result = parse_response(raw)
        assert not result.ok
        assert "direction" in result.parse_error.lower()

    def test_move_invalid_direction(self):
        raw = "ACTION: MOVE UP\n\nMEMORY_UPDATE:\nbad dir"
        result = parse_response(raw)
        assert not result.ok

    def test_use_missing_on(self):
        raw = "ACTION: USE KEY_BLUE DOOR_1\n\nMEMORY_UPDATE:\nno on"
        result = parse_response(raw)
        assert not result.ok

    def test_pickup_no_target(self):
        raw = "ACTION: PICKUP\n\nMEMORY_UPDATE:\nempty"
        result = parse_response(raw)
        assert not result.ok

    def test_missing_memory_update_returns_error(self):
        raw = "ACTION: MOVE NORTH"
        result = parse_response(raw)
        assert result.action is not None
        assert result.parse_error is not None

    def test_empty_memory_update_returns_error(self):
        raw = "ACTION: MOVE NORTH\n\nMEMORY_UPDATE:\n"
        result = parse_response(raw)
        assert result.parse_error is not None

    def test_unknown_verb_fails(self):
        raw = "ACTION: FLY NORTH\n\nMEMORY_UPDATE:\nunknown"
        result = parse_response(raw)
        assert not result.ok


class TestEdgeCases:
    def test_multiline_memory_preserved(self):
        lines = "[GOAL] find key\n[MAP] L->H->S\n[NOTES] relock every 5 steps"
        raw = f"ACTION: WAIT\n\nMEMORY_UPDATE:\n{lines}"
        result = parse_response(raw)
        assert result.ok
        assert "[GOAL]" in result.memory_update
        assert "[MAP]" in result.memory_update
        assert "[NOTES]" in result.memory_update

    def test_action_on_separate_line_from_memory(self):
        raw = (
            "ACTION: MOVE WEST\n"
            "\n"
            "MEMORY_UPDATE:\n"
            "[STATE] moving west\n"
        )
        result = parse_response(raw)
        assert result.ok
        assert result.action.verb == "MOVE"
        assert result.action.args[0] == "WEST"

    def test_use_action_preserves_compound_ids(self):
        raw = "ACTION: USE KEY_BLUE ON DOOR_1\n\nMEMORY_UPDATE:\nkeys"
        result = parse_response(raw)
        assert result.ok
        assert result.action.args[0] == "KEY_BLUE"
        assert result.action.args[1] == "DOOR_1"
