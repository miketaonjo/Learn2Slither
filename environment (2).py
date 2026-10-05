"""Environment: the board and the rules of the game.

The environment knows EVERYTHING about the game. It never talks to the
agent directly: the interpreter (see interpreter.py) is the only module
that reads the board and decides what the agent is allowed to see.
"""
import random

# Actions are ABSOLUTE directions (not relative to the snake's heading).
UP, LEFT, DOWN, RIGHT = 0, 1, 2, 3
ACTION_NAMES = ("UP", "LEFT", "DOWN", "RIGHT")
MOVES = {UP: (-1, 0), LEFT: (0, -1), DOWN: (1, 0), RIGHT: (0, 1)}

# What happened after a move (used by the interpreter to compute rewards).
EMPTY, GREEN, RED, DEAD = "empty", "green", "red", "dead"

START_LENGTH = 3
MIN_SIZE = 5  # smaller boards leave no room for the snake and 3 apples


class Board:
    def __init__(self, size=10, seed=None):
        if not isinstance(size, int) or size < MIN_SIZE:
            raise ValueError(f"board size must be an integer >= {MIN_SIZE}")
        self.size = size
        self.rng = random.Random(seed)
        self.reset()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------
    def reset(self):
        """Start a new game (= a new training session)."""
        self.snake = self._random_snake()  # list of (row, col), head first
        self.greens = []
        self.reds = []
        for _ in range(2):
            self._place(self.greens)
        self._place(self.reds)
        self.steps = 0
        self.max_length = len(self.snake)

    def _inside(self, cell):
        row, col = cell
        return 0 <= row < self.size and 0 <= col < self.size

    def _random_snake(self):
        """Random head, random direction, 2 contiguous cells behind it."""
        while True:
            head = (self.rng.randrange(self.size),
                    self.rng.randrange(self.size))
            dr, dc = MOVES[self.rng.randrange(4)]
            snake = [(head[0] - i * dr, head[1] - i * dc)
                     for i in range(START_LENGTH)]
            if all(self._inside(cell) for cell in snake):
                return snake

    def _place(self, apples):
        """Add an apple on a random free cell (no snake, no other apple).

        If the snake fills the whole board there is no free cell left:
        we simply skip instead of crashing.
        """
        taken = set(self.snake) | set(self.greens) | set(self.reds)
        free = [(r, c) for r in range(self.size)
                for c in range(self.size) if (r, c) not in taken]
        if free:
            apples.append(self.rng.choice(free))

    # ------------------------------------------------------------------
    # Rules
    # ------------------------------------------------------------------
    def step(self, action):
        """Move the head one cell. Return the event (EMPTY/GREEN/RED/DEAD).

        The snake is a list: we always add the new head, then remove the
        tail(s) depending on what was eaten:
            nothing -> +1 head, -1 tail          = same length
            green   -> +1 head, no tail removed  = length + 1
            red     -> +1 head, -2 tails         = length - 1
        """
        self.steps += 1
        dr, dc = MOVES[action]
        head = (self.snake[0][0] + dr, self.snake[0][1] + dc)

        # Wall or own body (tail included) -> game over
        if not self._inside(head) or head in self.snake:
            return DEAD

        self.snake.insert(0, head)
        if head in self.greens:
            self.greens.remove(head)
            self._place(self.greens)
            event = GREEN
        elif head in self.reds:
            self.reds.remove(head)
            self.snake.pop()
            self.snake.pop()
            self._place(self.reds)
            event = RED
        else:
            self.snake.pop()
            event = EMPTY

        if not self.snake:  # length dropped to 0
            return DEAD
        self.max_length = max(self.max_length, len(self.snake))
        return event

    # ------------------------------------------------------------------
    # Read access (used by the interpreter and the display)
    # ------------------------------------------------------------------
    def symbol_at(self, cell):
        """W wall, H head, S body, G green, R red, 0 empty."""
        if not self._inside(cell):
            return "W"
        if cell == self.snake[0]:
            return "H"
        if cell in self.snake:
            return "S"
        if cell in self.greens:
            return "G"
        if cell in self.reds:
            return "R"
        return "0"
