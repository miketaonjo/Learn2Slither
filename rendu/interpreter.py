"""Interpreter: the ONLY bridge between the board and the agent.

It does two jobs:
  1. build the STATE: what the snake sees from its head, in the 4
     directions (nothing else is ever given to the agent);
  2. turn what happened on the board into a REWARD.
"""
from environment import UP, LEFT, DOWN, RIGHT, MOVES, EMPTY, GREEN, RED, DEAD

DIRECTIONS = (UP, LEFT, DOWN, RIGHT)

REWARDS = {
    GREEN: 30,
    RED: -15,
    EMPTY: -1,
    DEAD: -100,
}


def reward(event):
    return REWARDS[event]

def look(board):
       cells = board.grid()              # all non-empty cells, built once
       size = board.size
       seen = {}
       for direction in DIRECTIONS:
           d_row, d_col = MOVES[direction]
           row, col = board.snake[0]
           ray = []
           while True:
               row += d_row
               col += d_col
               if not (0 <= row < size and 0 <= col < size):
                   ray.append("W")       # outside the board = wall
                   break
               ray.append(cells.get((row, col), "0"))
           seen[direction] = "".join(ray)
       return seen

def render(seen):
    left = seen[LEFT][::-1]
    pad = " " * len(left)
    lines = [pad + symbol for symbol in seen[UP][::-1]]
    lines.append(left + "H" + seen[RIGHT])
    lines += [pad + symbol for symbol in seen[DOWN]]
    return "\n".join(lines)

VALUES_PER_DIRECTION = 12

def _describe(ray):
       first_obstacle = ray.find("W")
       body = ray.find("S")
       if 0 <= body < first_obstacle:
           first_obstacle = body
       free = ray[:first_obstacle]
       distance = min(first_obstacle, 2)
       green = "G" in free
       red = "R" in free
       return (distance * 2 + green) * 2 + red

def encode(seen):
    state = 0
    for direction in DIRECTIONS:
        state = state * VALUES_PER_DIRECTION + _describe(seen[direction])
    return state
