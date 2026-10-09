import pygame
from environment import Board, UP, LEFT, DOWN, RIGHT, DEAD
from display import Display
from interpreter import look, render


KEYS = {pygame.K_UP: UP, pygame.K_LEFT: LEFT,
        pygame.K_DOWN: DOWN, pygame.K_RIGHT: RIGHT}

NAMES = {pygame.K_UP: "UP", pygame.K_LEFT: "LEFT",
         pygame.K_DOWN: "DOWN", pygame.K_RIGHT: "RIGHT"}

board = Board(10)
view = Display(10, 30)
view.draw(board, wait=False)

try:
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                raise KeyboardInterrupt
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    raise KeyboardInterrupt
                if event.key in KEYS:
                    print(NAMES[event.key])
                    result = board.step(KEYS[event.key])
                    if result == DEAD:
                        print("--- DEAD ---")
                        board.reset()
                    seen = look(board)
                    print(render(seen))
                    print("length :", len(board.snake))
                    if result == DEAD:
                        print("--- DEAD ---")
                        board.reset()
                    view.draw(board, wait=False)
        view.clock.tick(30)
except KeyboardInterrupt:
    view.close()
