from environment import UP, LEFT, DOWN, RIGHT, MOVES, EMPTY, GREEN, RED, DEAD

DIRECTIONS = (UP, LEFT, DOWN, RIGHT)

# Number of possible encoded values for each direction
VALUES_PER_DIRECTION = 12

REWARDS = {
    GREEN: 30,
    RED: -15,
    EMPTY: -1,
    DEAD: -100,
}


def reward(event):
    """Return the reward associated with a game event"""
    return REWARDS[event]


def look(board):
    """Observe the cells visible along the four directions from snake's head"""
    cells = board.grid()
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
                ray.append("W")
                break
            ray.append(cells.get((row, col), "0"))
        seen[direction] = "".join(ray)
    return seen


def render(seen):
    """Format the directional observations as a terminal diagram"""
    left = seen[LEFT][::-1]
    pad = " " * len(left)
    lines = [pad + symbol for symbol in seen[UP][::-1]]
    lines.append(left + "H" + seen[RIGHT])
    lines += [pad + symbol for symbol in seen[DOWN]]
    return "\n".join(lines)


def _describe(ray):
    """Encode the nearest obstacle and visible apples along 1 direct (0-11)"""
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
    """Convert directional observations into a single Q-table state index"""
    state = 0
    for direction in DIRECTIONS:
        state = state * VALUES_PER_DIRECTION + _describe(seen[direction])
    return state
