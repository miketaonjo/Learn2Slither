# Learn2Slither

Snake controlled by a Q-learning agent using a Q-table.

## Installation

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Architecture

```text
Agent ──action──► Environment ──event + board──► Interpreter
  ▲                                                   │
  └──────────── state (int) + reward ─────────────────┘
```

The agent **never receives the board directly**. It only receives an integer representing the state, computed from its vision, and a reward.

## How It Works

At each step: **observe → choose → act → evaluate → update**.

### State Representation

From its head, the snake looks in four directions (`UP`, `LEFT`, `DOWN`, `RIGHT`) until it reaches a wall.

Each direction is summarized by a number from 0 to 11:

`value = (distance * 2 + green) * 2 + red`

- `distance`: 0 (obstacle immediately adjacent), 1 (one free cell), or 2 (at least two free cells) before the first obstacle (wall or snake's body).
- `green` / `red`: 1 if a green / red apple is visible before the obstacle, otherwise 0.

The four values are combined into a single integer, as the digits of a base-12 number: **12⁴ = 20,736 possible states**.

### Actions

Four possible actions: `UP`, `LEFT`, `DOWN`, `RIGHT` (numbered 0 to 3).

### Rewards

| Event | Reward |
|---|---:|
| Eat a green apple | +30 |
| Eat a red apple | −15 |
| Move without eating anything | −1 |
| Game over (wall, snake's body, length 0, or starvation) | −100 |

### Starvation

If the snake goes `3 × size × size` steps without eating a green apple (300 steps on a 10×10 board), it dies.

This is a design choice: without this rule, an agent could keep moving in circles indefinitely without ending the game.

### The Q-table

The **Q-table** stores all Q-values:

- **One row per state** (20,736 rows).
- **One column per action** (4 columns).
- A total of 20,736 × 4 = 82,944 values, all initialized to 0: the agent has no prior knowledge.

To choose an action, the agent reads the row corresponding to its current state and selects the action with the highest Q-value.

Illustrative example (values from a model trained over 1,000 sessions; values may vary between training runs):

| State | Situation (summarized vision) | UP | LEFT | DOWN | RIGHT | Best action |
|---|---|---:|---:|---:|---:|---|
| 0 | Obstacle immediately adjacent in all four directions | −93.5 | −93.5 | −93.5 | −93.5 | None (all actions lead to death) |
| 4 | UP, LEFT, DOWN blocked; RIGHT has one free cell | −46.9 | −46.9 | −46.9 | −13.4 | RIGHT |
| 10 | UP, LEFT, DOWN blocked; RIGHT has free space and a green apple | −10.0 | −10.0 | −19.0 | +22.0 | RIGHT |

### How Q-values Are Updated

After each step, the agent updates the value of the action it just took:

```text
Q(s, a) ← Q(s, a) + α × (target − Q(s, a))

target = r + γ × max Q(s', ·)   if the game continues
target = r                       if the game ends (no future reward)
```

| Symbol | Meaning | Value |
|---|---|---:|
| `s`, `a` | State and action before the step | — |
| `r` | Reward received | +30, −15, −1, or −100 |
| `s'` | State after the step | — |
| `max Q(s', ·)` | Highest Q-value for the next state, read from the Q-table | — |
| `α` (alpha) | Learning rate: the fraction of the error corrected at each update | 0.1 |
| `γ` (gamma) | Importance of future rewards | 0.9 |

Numerical examples (α = 0.1, γ = 0.9):

| Case | Reward | Best Q-value for `s'` | Target | Previous Q-value | Updated Q-value |
|---|---:|---:|---:|---:|---:|
| Green apple eaten (first time) | +30 | 0 | 30 | 0 | **+3.0** |
| Same situation (second time) | +30 | 0 | 30 | 3.0 | **+5.7** |
| Death (no future rewards) | −100 | N/A | −100 | 0 | **−10.0** |
| Empty move leading to a state with a Q-value of 3.0 | −1 | 3.0 | −1 + 0.9 × 3.0 = 1.7 | −0.1 | **+0.08** |

The last example illustrates the role of `γ`: a move that provides no immediate reward can still be valuable if it leads to a promising state.