"""Display: the pygame window. It only DRAWS what the board contains."""
import os

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame  # noqa: E402

BACKGROUND = (240, 240, 240)
GRID = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
SNAKE = (0, 0, 255)
HEAD = (0, 0, 140)


class Display:
    def __init__(self, size, speed):
        self.size = size
        self.speed = speed                 # moves per second
        self.cell = max(10, min(60, 600 // size))
        pygame.init()
        pygame.display.set_caption("Snake Game")
        side = self.cell * size
        self.screen = pygame.display.set_mode((side, side))
        self.clock = pygame.time.Clock()

    def _events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                raise KeyboardInterrupt  # same as Ctrl+C
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                raise KeyboardInterrupt  # same as Ctrl+C

    def _rect(self, cell):
        row, col = cell
        return pygame.Rect(col * self.cell, row * self.cell,
                           self.cell, self.cell)

    def draw(self, board, caption="Snake Game", wait=True):
        """Draw the board, then wait to respect the display speed."""
        self._events()
        pygame.display.set_caption(caption)
        self.screen.fill(BACKGROUND)
        for apple in board.greens:
            pygame.draw.rect(self.screen, GREEN, self._rect(apple))
        for apple in board.reds:
            pygame.draw.rect(self.screen, RED, self._rect(apple))
        for i, segment in enumerate(board.snake):
            pygame.draw.rect(self.screen, HEAD if i == 0 else SNAKE,
                             self._rect(segment))
        for row in range(self.size):
            for col in range(self.size):
                pygame.draw.rect(self.screen, GRID,
                                 self._rect((row, col)), 1)
        pygame.display.flip()
        if wait:
            self.clock.tick(self.speed)

    def wait_key(self):
        """Step-by-step mode: block until SPACE / ENTER / RIGHT is pressed."""
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    raise KeyboardInterrupt  # same as Ctrl+C
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        raise KeyboardInterrupt  # same as Ctrl+C
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN,
                                     pygame.K_RIGHT):
                        return
            self.clock.tick(30)            # do not burn the CPU while waiting

    def close(self):
        pygame.quit()
