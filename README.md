# THE AMNESIAC

> An LLM agent that forgets everything between every single step, and must design its own memory from scratch to survive.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python)
![Tests](https://img.shields.io/badge/tests-95%20passing-brightgreen?style=flat-square)
![Tasks](https://img.shields.io/badge/tasks-T1%20through%20T6-orange?style=flat-square)
![Providers](https://img.shields.io/badge/LLM-Claude%20%7C%20GPT--4o-purple?style=flat-square)

---

## What Is This?

THE AMNESIAC is a harness that puts an LLM agent into a dynamic 2D grid world under one radical constraint: the agent receives **zero conversational history** between steps. At every step, all it gets is:

1. A fresh observation of its current surroundings
2. The contents of a memory scroll it previously wrote (max 2,048 bytes)

That scroll is **completely overwritten every step**. The agent cannot append, it cannot undo, it cannot accumulate. It has to decide what future-it will need to remember, compress it into 2,048 bytes, and trust that future-it reads it correctly.

To complete tasks like collecting scattered fragments, navigating locked doors, or tracking a drifting target, the agent must design its own memory schema, maintain it under pressure, and update it intelligently as the world changes.

> This mirrors a real problem in physical AI deployment. A robot operating an 8-hour factory shift cannot hold the entire shift in memory. It has to manage what it knows, what it discards, and what it risks forgetting.

---

## Quick Start

```bash
git clone https://github.com/MNauman13/the-amnesiac.git
cd the-amnesiac
pip install -r requirements.txt
cp .env.example .env
# Add your ANTHROPIC_API_KEY (or OPENAI_API_KEY) to .env
```

Then run:

```bash
python main.py t1
```

That's it. You'll see the agent navigating a grid world step by step, printing every action it takes, its scroll size, and task progress in real time.

---

## The 6 Tasks

Tasks escalate in difficulty. Each one stresses a different memory skill.

| ID | Name | Difficulty | What the agent has to do |
|---|---|---|---|
| **T1** | Key and Lock | 🟢 Easy | Find KEY_BLUE, use it to unlock DOOR_1, enter Hallway A. Door re-locks every 8 steps. |
| **T2** | Fragment Assembly | 🟡 Medium | Collect 4 fragments scattered across 3 rooms, return all to the assembly zone. |
| **T3** | Moving Target | 🟡 Medium | Track and pick up TOKEN_1 before it drifts away. It relocates every 3 steps. |
| **T4** | Cartographer | 🔴 Hard | Visit all 5 rooms in a hub-and-spoke layout. No items, just navigation memory. |
| **T5** | Relay Race | 🔴 Hard | Carry a fragile RELIC through 4 rooms in 50 steps or less. Drop it and it's gone. |
| **T6** | Labyrinth | 🟣 Expert | Collect 4 fragments while corridor destinations shuffle every 10 steps. The map you wrote last step may already be wrong. |

---

## Running Commands

```bash
# Run a single task (Claude, default settings)
python main.py t1

# Run with GPT-4o instead
python main.py t2 --provider openai

# Run the expert task with adversarial false events injected
python main.py t6 --adversarial

# Run with a specific random seed and save a full markdown report
python main.py t3 --seed 7 --report logs/t3_run.md

# Memory-enabled vs memory-wiped side-by-side comparison
python compare.py t2

# Multi-seed benchmark across all tasks
python benchmark.py --tasks t1 t2 t3 t4 t5

# Run all 95 unit tests
python -m pytest tests/ -v

# Start the web visualiser
cd viz && npm install && npm run dev
# Then open http://localhost:3000 and drag in any logs/*.jsonl file
```

### CLI Options

| Flag | Default | Description |
|---|---|---|
| `task` | required | Task ID: `t1` through `t6` |
| `--provider` | `anthropic` | `anthropic` or `openai` |
| `--model` | auto | Model override (e.g. `claude-haiku-4-5-20251001`) |
| `--temperature` | `0.3` | LLM temperature |
| `--seed` | `42` | World RNG seed |
| `--max-steps` | task default | Override the step limit |
| `--adversarial` | off | Inject false events into world stream to stress-test memory |
| `--report PATH` | none | Write a full markdown report |
| `--quiet` / `-q` | off | Suppress per-step output |
| `--no-log` | off | Disable JSONL logging |

---

## Example Output

```
Starting Task T1: Key & Lock
Goal: Find KEY_BLUE and use it to unlock DOOR_1, then enter Hallway A
Max steps: 100

Step   Action                           OK   Scroll   Progress
-------------------------------------------------------------------
Step   1 | MOVE EAST                    | ✓ | 87B    | 0.00
Step   2 | MOVE EAST                    | ✓ | 134B   | 0.00
Step   5 | MOVE SOUTH                   | ✓ | 198B   | 0.00
Step   8 | PICKUP KEY_BLUE              | ✓ | 256B   | 0.00
Step  12 | USE KEY_BLUE ON DOOR_1       | ✓ | 298B   | 0.00
Step  13 | MOVE SOUTH                   | ✓ | 312B   | 1.00

✓ Goal complete on step 13!

============================================================
  RUN REPORT — Task: T1
  Outcome:      ✓ GOAL COMPLETE
  Steps taken:  13 / 100 (optimal: 14)
  Tokens:       4,821 in / 1,204 out
  TOTAL SCORE:  0.847
============================================================
```

---

## What the Memory Scroll Looks Like

The agent writes this itself. No template, no fixed structure. Here's what one agent produced after step 8 of T1:

```
[GOAL] Find KEY_BLUE → USE KEY_BLUE ON DOOR_1 → enter Hallway A
[MAP] Library(start,1,1). Corridor SOUTH at (3,5) → DOOR_1 → HallwayA
      DOOR_1 re-locks every ~8 steps, act immediately after unlocking
[INV] KEY_BLUE (do NOT drop)
[NOTES] Library fully swept. Key was at (5,3). Door is south.
[STEP] 8 — picked up key
```

A different agent on the same task might use a completely different schema. That's the point.

---

## Web Visualiser

After a run, drag the `logs/run_t1.jsonl` file into the web app and replay the agent's run step by step.

```bash
cd viz && npm install && npm run dev
# Open http://localhost:3000
```

Each step shows:
- **Observation panel** - colour-coded: position (blue), surroundings (purple), inventory (green), world events (amber), goal reminder (pink)
- **Scroll panel** - before and after each step, with a byte usage progress bar
- **Step summary** - action taken, result, token counts, latency

![Web Visualiser](https://img.shields.io/badge/Web%20Visualiser-Next.js%20%2B%20Tailwind-0ea5e9?style=flat-square&logo=nextdotjs)

---

## Architecture

The system has 5 layers. Each one has a single job.

```
┌─────────────┐  render()  ┌──────────────────┐
│ World Engine│ ──────────>│ Observation      │
│  (L1)       │            │ Renderer (L2)    │
│ ground truth│            └────────┬─────────┘
└──────┬──────┘                     │ obs_text
       │                            ▼
       │                 ┌──────────────────┐
       │  action result  │  Memory API (L3) │<-- scroll read
       │<────────────────│  2048-byte limit  │
       │                 └────────┬─────────┘
       │                          │ {obs + scroll}
       │                          ▼
       │                 ┌──────────────────┐
       │                 │  Agent Harness   │
       │                 │  (LLM + parser)  │
       │                 └────────┬─────────┘
       │                          │ {ACTION, MEMORY_UPDATE}
       │<── execute(action) ──────┘
       │                 Memory API <-- scroll write
       ▼
  [next step]
```

| Layer | File | Job |
|---|---|---|
| **L1** | `world/engine.py` | Ground truth state; action processing; world physics |
| **L2** | `agent/observation.py` | Converts world state to structured text the LLM can read |
| **L3** | `agent/memory.py` | 2,048-byte scroll; UTF-8 byte enforcement; 3-version history |
| **L4** | `agent/harness.py` | Runs the loop; calls the LLM; parses responses; logs everything |
| **L5** | `evaluation/scorer.py` | Scores task completion, memory efficiency, and step efficiency |

---

## Project Structure

```
the-amnesiac/
├── main.py                    Entry point
├── compare.py                 Memory-enabled vs memory-wiped comparison
├── benchmark.py               Multi-seed benchmark across all tasks
├── requirements.txt
├── .env.example
│
├── world/
│   ├── rooms.py               Room, Door, WorldObject, Direction data models
│   ├── engine.py              WorldEngine: action processing, physics, goal checking
│   ├── dynamics.py            Object drift, door relock, room shuffle, adversarial events
│   └── tasks.py               Goal types and real-time progress tracking
│
├── agent/
│   ├── memory.py              MemoryScroll: 2048B limit, history tracking
│   ├── null_memory.py         NullMemoryScroll: always-empty scroll for comparisons
│   ├── observation.py         render_observation(): world state to text block
│   ├── parser.py              parse_response(): ACTION + MEMORY_UPDATE extraction
│   ├── llm.py                 LLMClient: Anthropic + OpenAI, timeout, prompt caching
│   └── harness.py             AgentHarness: the main loop
│
├── evaluation/
│   ├── scorer.py              score_run() -> TaskScore
│   ├── analyser.py            Emergent memory pattern detection
│   └── report.py              Terminal and markdown report generation
│
├── tasks/
│   ├── t1_key_and_lock.json
│   ├── t2_fragment_assembly.json
│   ├── t3_moving_target.json
│   ├── t4_cartographer.json
│   ├── t5_relay_race.json
│   └── t6_labyrinth.json
│
├── tests/                     95 unit tests (all passing)
│   ├── test_world.py          World engine, movement, pickup/drop, goals, task configs
│   ├── test_parser.py         Response parsing, well-formed and malformed
│   ├── test_memory.py         Scroll read/write, byte budget, history, unicode
│   ├── test_observation.py    Observation format, null scroll behaviour
│   └── test_dynamics.py       Object drift, door relock, room shuffle, adversarial
│
├── logs/                      Auto-generated JSONL per run (gitignored)
└── viz/                       Next.js web visualiser
```

---

## Scoring

```
total_score = 0.60 x task_completion
            + 0.25 x memory_efficiency
            + 0.15 x step_efficiency

memory_efficiency = 0.50 x recall_accuracy
                  + 0.30 x compression_efficiency
                  + 0.20 x (1 - schema_instability)
```

A score above 0.75 across the benchmark suite indicates a strong agent. Task completion is weighted highest because nothing else matters if the agent cannot actually do the job.

---

## Design Choices

### The Agent Harness

The harness is a strict zero-context loop. Every step:

1. Events from the previous tick are cleared
2. A fresh observation is rendered
3. The scroll is prepended to the observation
4. The LLM receives both and nothing else
5. The response is parsed with a strict regex for `ACTION:` and `MEMORY_UPDATE:`
6. Parse errors fall back to WAIT and inject a system message into the next observation
7. Three consecutive parse errors terminate the run as a failure
8. The world ticks (dynamics fire, step count increments)
9. Everything is logged to JSONL

There is a 30-second hard timeout on every LLM call using a daemon thread. On timeout, WAIT is substituted and the agent is notified in the next observation. This matters for real-world reliability.

The harness deliberately does not help the agent. It does not summarise history, it does not hint at goals, and it does not interpret intentions. If the agent writes a bad scroll, it suffers the consequences next step.

### Observation Format

The observation answers one question: what does a newly-spawned amnesiac need to see right now?

```
[POSITION]         Room name, coordinates, facing direction

[SURROUNDINGS]     3-cell radius scan in all 8 compass directions.
                   Each direction reports the first notable thing:
                   wall / floor / object (with exact coords) / corridor to another room.
                   This gives the agent spatial awareness without needing a full map.

[INVENTORY]        What the agent is carrying, with weight and a FRAGILE warning if relevant.

[WORLD EVENTS]     What changed since the last step: drifted objects, re-locked doors,
                   corridor reroutes. [UNVERIFIED] tags mark adversarial false events.

[GOAL REMINDER]    Dynamic progress: "Fragments collected: 2/4. Still needed: FRAG_C, FRAG_D."
                   This regenerates from world state every step so it is always accurate
                   even if the agent's scroll goes stale.
```

The surroundings format is intentionally compact. A full grid dump would waste scroll space. By scanning 3 cells in each direction and returning the first notable thing, the agent gets enough to navigate without drowning in noise.

Object coordinates appear inline (e.g. `KEY_BLUE at (4,2) dist 2`) so the agent can record them in the scroll without needing to INSPECT.

### Memory Scroll Design

The 2,048-byte limit is deliberately tight but not punishing. A well-organised schema fits goals, a partial map, inventory notes, and a few dynamic warnings comfortably. A poorly-organised schema wastes bytes on redundant observations and fails to retain critical facts like which door a key belongs to.

The scroll is completely overwritten each step rather than appended. Append-only memory grows indefinitely and stops the agent from learning to prune. Overwrite forces the agent to make active decisions about what to keep, which is exactly the skill we are testing.

The history of the last 3 scroll versions is preserved for evaluation only. The agent cannot read it.

### Action Space

```
MOVE    N/S/E/W         Move one cell; fail silently on wall/locked door
TURN    <direction>     Change facing without moving (useful for orientation tracking)
PICKUP  <id>            Pick up any object within 3 Manhattan distance cells
DROP    <id>            Drop a carried item at current position
USE     <id> ON <id>    Apply an item to a target (key on door, primary interaction)
INSPECT <id>            Examine an object for hidden details
WAIT                    Skip turn (world dynamics still tick)
```

The action space is minimal by design. Everything a physical robot needs for object manipulation and navigation is here. Anything not here (combined actions, macro moves, conditional logic) must be planned through memory.

PICKUP range is 3 cells rather than 1. This reduces tedious positioning steps and lets the agent focus on higher-level planning. USE on a door still requires adjacency.

### World Dynamics

Static environments are too easy. THE AMNESIAC world actively fights the agent:

- **Door relock** (T1): a door re-locks on a timer, so the agent must act quickly after unlocking
- **Object drift** (T3): the target item relocates every few steps, so last-step coordinates in the scroll may be wrong
- **Room shuffle** (T6): corridor destinations swap every 10 steps, so a map the agent wrote 11 steps ago leads somewhere different now
- **Adversarial mode** (--adversarial flag): false world events are injected, tagged [UNVERIFIED], to test whether the agent trusts its scroll over noisy sensor data

### The Amnesiac Constraint

Most agent harnesses give the LLM full conversational history. That works for chatbots but it is not how physical systems operate. A robot does not have unbounded working memory across a full shift.

This constraint forces the LLM to behave like a robot: perceive the world, reason about what is relevant, compress knowledge efficiently, and act on incomplete information. The agent either builds a good memory schema and completes the task, or it does not.

The comparative mode (`compare.py`) makes this concrete. Run the same task with memory and without memory. The score delta is the value of the memory design.

---

## Tests

```bash
python -m pytest tests/ -v
```

95 tests, all passing. They cover:

- World engine: movement, wall collisions, door mechanics, pickup/drop lifecycle
- Parser: well-formed responses, edge cases, malformed output, partial blocks
- Memory: byte limits, UTF-8 encoding, truncation, history versioning, NullMemoryScroll
- Observation: all 8 directions, 3-cell radius detection, door display, dynamic goal reminder
- Dynamics: object drift, door relock, room shuffle, adversarial event tagging
- Task configs: all 6 JSON configs load correctly with valid world state

---

## Adding Your Own Task

Task configs are plain JSON. The schema is:

```json
{
  "id": "TX",
  "name": "My Task",
  "difficulty": "medium",
  "max_steps": 80,
  "optimal_steps": 20,
  "rooms": [ ... ],
  "doors": [ ... ],
  "objects": [ ... ],
  "agent": { "start_room": "...", "start_x": 1, "start_y": 1, "facing": "NORTH" },
  "goal": { "type": "reach_room", "target_room": "...", "description": "..." },
  "dynamics": {
    "door_relock": { "enabled": true, "interval": 8, "door_ids": ["DOOR_1"] }
  }
}
```

Drop it in `tasks/` and run `python main.py tx`.

**Supported goal types:**

| Type | What it checks |
|---|---|
| `reach_room` | Agent enters a target room |
| `reach_room_with_items` | Agent reaches a room carrying specific items |
| `collect_fragments_at_zone` | Agent collects all fragments and returns to a zone |
| `pickup_item` | Agent picks up a specific item |
| `visit_all_rooms` | Agent visits every room in a list |
| `reach_with_item_timed` | Agent delivers an item within a step limit |

---

## Requirements

```
anthropic>=0.30
openai>=1.30
python-dotenv>=1.0
pytest>=8.0
```

Python 3.10 or higher. No GPU required.

For the web visualiser: Node.js 18 or higher.
