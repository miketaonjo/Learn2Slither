import random

# Movement identifiers and their corresponding display names
UP, LEFT, DOWN, RIGHT = 0, 1, 2, 3
ACTION_NAMES = ("UP", "LEFT", "DOWN", "RIGHT")

# Row and column offsets for each movement direction
MOVES = {UP: (-1, 0), LEFT: (0, -1), DOWN: (1, 0), RIGHT: (0, 1)}

# Game events returned by Board.step()
EMPTY, GREEN, RED, DEAD = "empty", "green", "red", "dead"

START_LENGTH = 3
HUNGER_FACTOR = 3


class Board:
    def __init__(self, size, seed=None):
        """Initialize the board and create a new game state"""
        self.size = size
        self.rng = random.Random(seed)
        self.hunger_limit = HUNGER_FACTOR * size * size
        self.reset()

    def reset(self):
        """Reset the snake, apples, and session counters"""
        self.snake = self._random_snake()
        self.greens = []
        self.reds = []
        for _ in range(2):
            self._place(self.greens)
        self._place(self.reds)
        self.steps = 0
        self.hunger = 0
        self.max_length = len(self.snake)

    def _inside(self, cell):
        """Return whether a cell is within the board boundaries"""
        row, col = cell
        return 0 <= row < self.size and 0 <= col < self.size

    def _random_snake(self):
        """Generate a randomly positioned snake that fits on the board"""
        while True:
            head = (self.rng.randrange(self.size),
                    self.rng.randrange(self.size))
            dr, dc = MOVES[self.rng.randrange(4)]
            snake = []
            for i in range(START_LENGTH):
                snake.append((head[0] - i * dr, head[1] - i * dc))
            if all(self._inside(cell) for cell in snake):
                return snake

    def _place(self, apples):
        """Place a new apple in a randomly selected free cell"""
        taken = set(self.snake) | set(self.greens) | set(self.reds)
        free = [(r, c) for r in range(self.size)
                for c in range(self.size) if (r, c) not in taken]
        if free:
            apples.append(self.rng.choice(free))

    def step(self, action):
        """Move the snake, process collisions, and return the game event"""
        if not isinstance(action, int) or action not in MOVES:
            raise ValueError(
                f"Invalid action {action!r}, expected 0-3 {ACTION_NAMES}")
        self.steps += 1
        dr, dc = MOVES[action]
        head = (self.snake[0][0] + dr, self.snake[0][1] + dc)

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

        if event == GREEN:
            self.hunger = 0
        else:
            self.hunger += 1
            if self.hunger >= self.hunger_limit:
                return DEAD  # starved
        return event

    def grid(self):
        """Return a mapping of occupied cells to their display symbols"""
        cells = {cell: "S" for cell in self.snake}
        cells[self.snake[0]] = "H"
        for apple in self.greens:
            cells[apple] = "G"
        for apple in self.reds:
            cells[apple] = "R"
        return cells
