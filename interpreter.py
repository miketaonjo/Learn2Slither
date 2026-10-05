"""Interpreter: the ONLY bridge between the board and the agent.

It does two jobs:
  1. build the STATE: what the snake sees from its head, in the 4
     directions (nothing else is ever given to the agent);
  2. turn what happened on the board into a REWARD.
"""
from environment import UP, LEFT, DOWN, RIGHT, MOVES, EMPTY, GREEN, RED, DEAD

DIRECTIONS = (UP, LEFT, DOWN, RIGHT)

# ----------------------------------------------------------------------
# Rewards (the agent will try to maximise their sum)
# ----------------------------------------------------------------------
REWARDS = {
    GREEN: 30,    # good: the snake grows
    RED: -15,     # bad: the snake shrinks
    EMPTY: -1,    # small cost per move: no reason to wander
    DEAD: -100,   # very bad: wall, own body, or length 0
}


def reward(event):
    return REWARDS[event]


# ----------------------------------------------------------------------
# Vision
# ----------------------------------------------------------------------
def look(board):
    """What the head sees, for each direction.

    Returns {direction: "000GRW"}: the symbols met going away from the
    head, NEAREST FIRST, up to and including the wall.
    """
    seen = {}
    for direction in DIRECTIONS:
        d_row, d_col = MOVES[direction]
        row, col = board.snake[0]
        ray = ""
        while not ray.endswith("W"):
            row, col = row + d_row, col + d_col
            ray += board.symbol_at((row, col))
        seen[direction] = ray
    return seen


def render(seen):
    """The terminal figure of the subject (a cross centred on the head)."""
    left = seen[LEFT][::-1]               # farthest first, so W is on the left
    pad = " " * len(left)
    lines = [pad + symbol for symbol in seen[UP][::-1]]
    lines.append(left + "H" + seen[RIGHT])
    lines += [pad + symbol for symbol in seen[DOWN]]
    return "\n".join(lines)


# ----------------------------------------------------------------------
# State
# ----------------------------------------------------------------------
# For each direction we keep 3 pieces of information:
#   - how far is the first obstacle (wall or body segment):
#       0 = right next to the head, 1 = two cells away, 2 = farther
#   - is there a green apple before that obstacle?  (0/1)
#   - is there a red apple before that obstacle?    (0/1)
# That is 3 * 2 * 2 = 12 values per direction -> 12**4 = 20736 states.
# No absolute distance is used, so the same Q-table works on any board
# size (this is what makes the "board size" bonus possible).
VALUES_PER_DIRECTION = 12


def _describe(ray):
    """Turn one ray (nearest first) into a number from 0 to 11."""
    stops = [i for i, symbol in enumerate(ray) if symbol in "WS"]
    first_obstacle = stops[0]             # a ray always ends with a wall
    free = ray[:first_obstacle]
    distance = min(first_obstacle, 2)
    green = "G" in free
    red = "R" in free
    return (distance * 2 + green) * 2 + red


def encode(seen):
    """Pack the 4 rays into ONE integer (the key of the Q-table)."""
    state = 0
    for direction in DIRECTIONS:
        state = state * VALUES_PER_DIRECTION + _describe(seen[direction])
    return state
