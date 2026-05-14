# THE AMNESIAC — Claude Session Context

## Project Overview
An LLM agent harness where the agent forgets everything between steps and must design/maintain its own external memory to survive long-horizon tasks in a dynamic 2D grid world.

**Humanoid Internship Challenge Submission — Summer 2026**

## Current Status
- **Phase**: MVP complete (Phases 1–5 of 6)
- **Tests**: 65/65 passing
- **What's done**: Full world engine, agent harness, memory API, parser, LLM integration (Anthropic + OpenAI), 5 task configs (T1–T5), evaluation framework

## Architecture (5 Layers)
```
L1  world/engine.py        WorldEngine — ground truth state, action processing, physics
L2  agent/observation.py   ObservationRenderer — world state → structured text
L3  agent/memory.py        MemoryScroll — 2048-byte scroll, history tracking, byte enforcement
L4  agent/harness.py       AgentHarness — main loop, LLM orchestration, error handling, logging
L5  evaluation/scorer.py   Scorer — task completion + memory efficiency + step efficiency
```

## Key Design Decisions

### Coordinate System
- (0,0) = top-left, x→east, y→south
- Grid: `room.grid[y][x]` = "floor" | "wall"
- Directions: NORTH=(0,-1), SOUTH=(0,1), EAST=(1,0), WEST=(-1,0)

### Door Mechanics
- Doors are portal cells — `Door.pos_a` in room_a, `Door.pos_b` in room_b
- MOVE into door position → if unlocked, agent teleports to other side
- USE KEY ON DOOR to unlock. Keys stay in inventory (not consumed).

### Memory Scroll
- 2048 bytes hard limit (UTF-8 encoded)
- Overwritten each step — agent must curate
- History: last 3 versions stored for evaluation only
- Agent picks its own schema — free-form text

### Response Format
```
ACTION: <verb> [args]

MEMORY_UPDATE:
<scroll content>
```
Parse errors → WAIT substituted. 3 consecutive errors = task failure.

### LLM Integration
- Default: `claude-sonnet-4-6` via Anthropic SDK with prompt caching (ephemeral)
- Alt: any OpenAI model via `--provider openai`
- Temperature: 0.3, max_tokens: 800

### Scoring Formula
```
total = 0.60 * task_completion + 0.25 * memory_efficiency + 0.15 * step_efficiency
memory_efficiency = 0.5*recall + 0.3*compression + 0.2*(1-instability)
```

## File Structure
```
the-amnesiac/
├── main.py                     # Entry point: python main.py t1 [--options]
├── requirements.txt
├── .env.example                # ANTHROPIC_API_KEY / OPENAI_API_KEY
├── world/
│   ├── rooms.py                # Room, Door, WorldObject, Direction, DIR_DELTA
│   ├── engine.py               # WorldEngine, WorldState, ActionResult, WorldEvent
│   ├── dynamics.py             # DynamicsConfig, tick_dynamics (drift/relock)
│   └── tasks.py                # GoalSpec, check_goal, parse_goal_spec
├── agent/
│   ├── memory.py               # MemoryScroll (2048B limit, 3-version history)
│   ├── observation.py          # render_observation() → structured text block
│   ├── parser.py               # parse_response() → ParseResult, Action
│   ├── llm.py                  # LLMClient (Anthropic/OpenAI), SYSTEM_PROMPT
│   └── harness.py              # AgentHarness.step() / .run(), StepResult, RunResult
├── evaluation/
│   ├── scorer.py               # score_run() → TaskScore
│   ├── analyser.py             # analyse_run() → AnalysisReport (emergent patterns)
│   └── report.py               # print_report(), write_report()
├── tasks/
│   ├── t1_key_and_lock.json    # Easy: find key, unlock door
│   ├── t2_fragment_assembly.json # Medium: collect 4 fragments across 3 rooms
│   ├── t3_moving_target.json   # Medium: pick up drifting token
│   ├── t4_cartographer.json    # Hard: visit 5 rooms (hub + 4 wings)
│   └── t5_relay_race.json      # Hard: carry fragile relic through 4 rooms in 50 steps
├── logs/                       # Auto-generated JSONL step logs per run
└── tests/
    ├── test_world.py           # 40 tests: movement, pickup/drop, use, dynamics, goals, task loading
    ├── test_parser.py          # 19 tests: well-formed/malformed/edge-case responses
    └── test_memory.py          # 14 tests: read/write, byte budget, history, unicode
```

## Running
```bash
pip install -r requirements.txt
cp .env.example .env  # add API key

python main.py t1                        # Task T1, Claude default
python main.py t2 --provider openai      # Task T2, GPT-4o
python main.py t3 --max-steps 50 --seed 7
python main.py t1 --report report.md     # Write markdown report
python -m pytest tests/ -v               # Run all 65 unit tests
```

## Task Configs Schema
```json
{
  "id": "T1", "name": "...", "difficulty": "easy",
  "max_steps": 100, "optimal_steps": 14,
  "rooms": [{"id": "...", "name": "...", "width": 8, "height": 6, "grid": [[...]]}],
  "doors": [{"id": "DOOR_1", "room_a": "...", "room_b": "...",
             "pos_a": [x,y], "pos_b": [x,y], "locked": true, "required_key_type": "KEY_BLUE"}],
  "objects": [{"id": "KEY_BLUE", "type": "key", "x": 5, "y": 3, "room": "library", "weight": 0}],
  "agent": {"start_room": "...", "start_x": 1, "start_y": 1, "facing": "NORTH"},
  "goal": {"type": "reach_room", "target_room": "hallway_a", "description": "..."},
  "dynamics": {"object_drift": {"enabled": false}, "door_relock": {"enabled": true, "interval": 8, "door_ids": ["DOOR_1"]}}
}
```

## Goal Types
| Type | Params | Description |
|------|--------|-------------|
| `reach_room` | `target_room` | Agent enters target room |
| `reach_room_with_items` | `target_room`, `items[]` | Reach room carrying all items |
| `collect_fragments_at_zone` | `fragments[]`, `zone_room`, `zone_pos` | Collect all + return to zone |
| `pickup_item` | `item_id` | Pick up specific item |
| `visit_all_rooms` | `room_ids[]` | Visit every listed room |
| `reach_with_item_timed` | `item_id`, `target_room`, `max_steps` | Deliver within step limit |

## What's Done (Complete)
- All 6 task configs: T1–T6 (T6 is expert Labyrinth with room shuffle)
- Room shuffle dynamics: swaps door destinations every K steps
- Adversarial world mode: injects [UNVERIFIED] false events (`--adversarial` flag)
- Observation surroundings: 3-cell radius scan in each of 8 directions (inline, no separate section)
- Dynamic goal reminder: shows real-time fragment counts, unvisited rooms, step countdowns
- LLM timeout: 30s hard limit, WAIT substituted on timeout
- Few-shot example in SYSTEM_PROMPT for first-step guidance
- Comparative mode: `python compare.py t1` runs memory-enabled vs memory-wiped side-by-side
- `NullMemoryScroll`: always-empty scroll for comparative runs
- benchmark.py: multi-seed, multi-task sweeps
- Web visualiser: Next.js app in `viz/` with step-by-step replay, scroll/observation side-by-side
- DROP bug fixed: `WorldState.carried` preserves original object metadata
- 95 unit tests (all passing)

## Running Everything
```bash
python main.py t1                          # single task run
python main.py t6 --adversarial            # T6 Labyrinth with false events
python compare.py t2                       # memory-enabled vs memory-wiped comparison
python benchmark.py --tasks t1 t2 t3       # multi-seed benchmark
python -m pytest tests/ -v                 # 95 unit tests

cd viz && npm run dev                      # web visualiser at http://localhost:3000
```

## Known Considerations
- `DROP` in engine.py creates a WorldObject with type KEY as placeholder — the original object type is lost on drop. For MVP this is acceptable since the only items that matter are keys and fragments; a full implementation would preserve type.
- Object drift re-key spawning uses fresh WorldObject with KeyType — works for T3 but would need extension for multi-type worlds.
- The observation renderer shows "3-cell radius" objects in a separate [NEARBY OBJECTS] section, not inline in compass directions for objects beyond 1 cell — minor deviation from PRD format but functionally equivalent.

## GitHub
Repository: https://github.com/MNauman13/the-amnesiac
Commit strategy: one commit per completed phase / bugfix
