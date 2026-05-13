# THE AMNESIAC

> An LLM agent that forgets everything between every step — and must design its own memory to survive.

**Humanoid Internship Challenge · Summer 2025**

---

## What Is This?

THE AMNESIAC is an agent harness built around a single radical constraint: the agent has **zero conversational context** between steps. At each step it receives only:

1. A fresh observation of its current state in a dynamic 2D grid world
2. The contents of its own **memory scroll** — a structured text document it previously wrote (max 2,048 bytes)

To complete long-horizon tasks — collecting objects, navigating locked doors, tracking drifting items — the agent must design, maintain, and iteratively refine its own memory schema. A poorly organised scroll leads directly to task failure.

This mirrors a real problem in physical AI deployment: a robot operating an 8-hour shift cannot hold the entire shift in memory.

---

## Architecture

```
┌─────────────┐  render()  ┌──────────────────┐
│ World Engine│ ──────────► │ Observation      │
│ (ground     │             │ Renderer (L2)    │
│  truth)     │             └────────┬─────────┘
└──────┬──────┘                      │ obs_text
       │                             ▼
       │                  ┌──────────────────┐
       │   action result  │  Memory API (L3) │◄── scroll read
       │◄─────────────────│  (2048B limit)   │
       │                  └────────┬─────────┘
       │                           │ {obs + scroll}
       │                           ▼
       │                  ┌──────────────────┐
       │                  │  Agent Harness   │
       │                  │  (LLM + parser)  │
       │                  └────────┬─────────┘
       │                           │ {ACTION, MEMORY_UPDATE}
       │◄── execute(action) ───────┘
       │                  Memory API ◄── scroll write
       ▼
  [next step]
```

| Layer | File | Responsibility |
|---|---|---|
| L1 | `world/engine.py` | Ground truth state; action processing; physics |
| L2 | `agent/observation.py` | World state → structured observation text |
| L3 | `agent/memory.py` | 2,048-byte scroll; byte enforcement; history |
| L4 | `agent/harness.py` | Main loop; LLM orchestration; logging |
| L5 | `evaluation/scorer.py` | Task + memory + step efficiency scoring |

---

## Setup

```bash
git clone https://github.com/mnaumansiddiqui06/the-amnesiac.git
cd the-amnesiac
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY (or OPENAI_API_KEY)
```

---

## Running

```bash
# Run Task T1 (easy — Key & Lock) with Claude
python main.py t1

# Run Task T2 with GPT-4o
python main.py t2 --provider openai

# Run with a specific seed, step limit, and save a markdown report
python main.py t3 --seed 7 --max-steps 80 --report logs/t3_report.md

# Run all unit tests
python -m pytest tests/ -v
```

### CLI Options

| Flag | Default | Description |
|---|---|---|
| `task` | required | Task ID: `t1` `t2` `t3` `t4` `t5` |
| `--provider` | `anthropic` | `anthropic` or `openai` |
| `--model` | auto | Model override (e.g. `claude-haiku-4-5-20251001`) |
| `--temperature` | `0.3` | LLM temperature |
| `--max-tokens` | `800` | Max output tokens |
| `--seed` | `42` | World RNG seed |
| `--max-steps` | task default | Override step limit |
| `--report PATH` | none | Write markdown report |
| `--quiet` / `-q` | off | Suppress per-step output |

---

## Tasks

| ID | Name | Difficulty | Description |
|---|---|---|---|
| T1 | Key & Lock | Easy | Find KEY_BLUE, unlock DOOR_1, enter Hallway A |
| T2 | Fragment Assembly | Medium | Collect 4 fragments across 3 rooms, return to assembly zone |
| T3 | Moving Target | Medium | Track and pick up TOKEN_1 — it drifts every 3 steps |
| T4 | Cartographer | Hard | Visit all 5 rooms in a hub-and-spoke layout |
| T5 | Relay Race | Hard | Carry fragile RELIC through 4 rooms in ≤50 steps |

---

## Scoring

```
total_score = 0.60 × task_completion
            + 0.25 × memory_efficiency
            + 0.15 × step_efficiency

memory_efficiency = 0.5 × recall_accuracy
                  + 0.3 × compression_efficiency
                  + 0.2 × (1 - schema_instability)
```

A score > 0.75 across the full benchmark suite indicates a successful agent.

---

## Example Output

```
Starting Task T1: Key & Lock
Goal: Find KEY_BLUE and use it to unlock DOOR_1, then enter Hallway A
Max steps: 100

Step   Action                           OK   Scroll   Progress
-----------------------------------------------------------------
Step   1 | MOVE EAST                    | ✓ | 87B    | 0.00
Step   2 | MOVE EAST                    | ✓ | 134B   | 0.00
Step   8 | PICKUP KEY_BLUE              | ✓ | 256B   | 0.00
Step  12 | USE KEY_BLUE ON DOOR_1       | ✓ | 298B   | 0.00
Step  13 | MOVE SOUTH                   | ✓ | 312B   | 1.00

✓ Goal complete on step 13!

============================================================
  RUN REPORT — Task: T1
  Outcome:      ✓ GOAL COMPLETE
  TOTAL SCORE:  0.847
============================================================
```

---

## Memory Scroll

The agent controls its own scroll schema. Example from a T1 run after step 8:

```
[GOAL] Have KEY_BLUE ✓ → unlock DOOR_1 → enter Hallway A
[MAP] Library(start)--S(3,5)-->DOOR_1-->HallwayA
      DOOR_1 re-locks every ~8 steps — act fast
[INV] KEY_BLUE (do NOT drop)
[NOTES] Library swept. DOOR_1 is at (3,5) facing S.
[STEP] 8 — picked up key
```

---

## Project Structure

```
the-amnesiac/
├── main.py            world/         agent/         evaluation/
│                      ├── rooms.py   ├── memory.py  ├── scorer.py
│                      ├── engine.py  ├── obs...py   ├── analyser.py
│                      ├── dynamics   ├── parser.py  └── report.py
│                      └── tasks.py  ├── llm.py
├── tasks/             └── harness.py
├── tests/   (65 unit tests — all passing)
└── logs/    (auto-generated JSONL per run)
```
