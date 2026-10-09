import os
import pygame

BACKGROUND = (0, 0, 0)
GRID = (100, 100, 100)
GREEN = (144, 205, 120)
RED = (232, 105, 105)
SNAKE = (178, 145, 245)
HEAD = (150, 105, 235)


class Display:
    def __init__(self, size, speed):
        self.size = size
        self.speed = speed
        self.cell = max(10, min(60, 600 // size))
        pygame.display.init()
        pygame.display.set_caption("Learn2Slither")
        side = self.cell * size
        self.screen = pygame.display.set_mode((side, side))
        self.clock = pygame.time.Clock()

    def _events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                raise KeyboardInterrupt
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                raise KeyboardInterrupt

    def _rect(self, cell):
        row, col = cell
        return pygame.Rect(col * self.cell, row * self.cell,
                           self.cell, self.cell)

    def draw(self, board, caption="Learn2Slither", wait=True):
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
                    raise KeyboardInterrupt
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        raise KeyboardInterrupt
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN,
                                     pygame.K_RIGHT):
                        return
            self.clock.tick(30)

    def close(self):
        pygame.quit()
