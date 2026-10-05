"""Command line, wiring of the 4 modules, and the session loop.

    environment -> interpreter -> agent -> (action) -> environment ...
"""
import argparse
import math
import os
import sys

import interpreter
from agent import Agent, ModelError
from environment import ACTION_NAMES, DEAD, GREEN, MIN_SIZE, RED, Board

MAX_SESSIONS = 10_000_000
MAX_SIZE = 50
SUCCESS_LENGTH = 10                 # the goal of the subject


# ----------------------------------------------------------------------
# Command line
# ----------------------------------------------------------------------
def bounded(kind, low, high, label):
    """argparse type: a number of the given kind between low and high."""
    def parse(text):
        try:
            value = kind(text)
        except ValueError:
            raise argparse.ArgumentTypeError(
                f"'{text}' is not a valid {label}") from None
        if math.isnan(value) or not low <= value <= high:
            raise argparse.ArgumentTypeError(
                f"{label} must be between {low} and {high} (got {text})")
        return value
    return parse


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="./snake", allow_abbrev=False,
        description="Snake controlled by a Q-learning agent.")
    parser.add_argument("-sessions", default=1, metavar="N",
                        type=bounded(int, 1, MAX_SESSIONS, "sessions"),
                        help="number of sessions to play (default 1)")
    parser.add_argument("-save", metavar="FILE",
                        help="export the model to FILE at the end")
    parser.add_argument("-load", metavar="FILE",
                        help="import the model from FILE before starting")
    parser.add_argument("-visual", choices=("on", "off"), default="on",
                        help="graphical window + terminal output (default on)")
    parser.add_argument("-dontlearn", action="store_true",
                        help="use the model without updating it")
    parser.add_argument("-step-by-step", action="store_true",
                        help="one move per key press (SPACE / ENTER)")
    parser.add_argument("-speed", default=10.0, metavar="MOVES_PER_SEC",
                        type=bounded(float, 0.1, 1000, "speed"),
                        help="display speed (default 10)")
    parser.add_argument("-size", default=10, metavar="N",
                        type=bounded(int, MIN_SIZE, MAX_SIZE, "board size"),
                        help="board size (default 10)")
    parser.add_argument("-seed", type=int, metavar="N",
                        help="make a run reproducible")
    return parser.parse_args(argv)


def check_save_path(path):
    """Fail NOW (not after an hour of training) if we cannot save."""
    folder = os.path.dirname(path) or "."
    if not path.strip():
        raise ModelError("empty file name for -save")
    if os.path.isdir(path):
        raise ModelError(f"'{path}' is a directory")
    try:
        os.makedirs(folder, exist_ok=True)
    except OSError as error:
        raise ModelError(f"cannot create '{folder}': {error.strerror}")
    if not os.access(folder, os.W_OK):
        raise ModelError(f"cannot write in '{folder}': permission denied")


# ----------------------------------------------------------------------
# One session = one game
# ----------------------------------------------------------------------
def run_session(board, agent, view, args, verbose, caption):
    board.reset()
    idle_limit = board.size ** 2 * 2     # moves allowed without any apple
    idle = 0
    seen = interpreter.look(board)
    state = interpreter.encode(seen)
    while True:
        if view:
            view.draw(board, f"{caption} - length {len(board.snake)}")
        if args.step_by_step:
            try:
                view.wait_key() if view else input("[Enter] next move ")
            except EOFError:             # stdin closed: stop asking
                args.step_by_step = False
        if verbose:
            print(interpreter.render(seen))
        action = agent.choose(state)
        if verbose:
            print(f"\n{ACTION_NAMES[action]}\n")
        event = board.step(action)
        done = event == DEAD
        next_state = None
        if not done:
            seen = interpreter.look(board)
            next_state = interpreter.encode(seen)
        agent.learn(state, action, interpreter.reward(event),
                    next_state, done)
        if done:
            break
        state = next_state
        idle = 0 if event in (GREEN, RED) else idle + 1
        if idle >= idle_limit:           # looping forever: end the session
            break
    if view:
        view.draw(board, f"{caption} - game over", wait=False)
    agent.end_session()
    return board.max_length, board.steps


# ----------------------------------------------------------------------
# Whole program
# ----------------------------------------------------------------------
def open_display(args):
    if args.visual == "off":
        return None
    try:
        from display import Display
        return Display(args.size, args.speed)
    except (ImportError, RuntimeError) as error:   # no pygame / no screen
        print(f"Warning: no graphical display ({error}); "
              "continuing as if -visual off", file=sys.stderr)
        return None


def summary(results):
    lengths = [length for length, _ in results]
    wins = sum(length >= SUCCESS_LENGTH for length in lengths)
    print(f"Game over, max length = {max(lengths)}, "
          f"max duration = {max(steps for _, steps in results)}")
    print(f"Average length = {sum(lengths) / len(lengths):.2f}, "
          f"length >= {SUCCESS_LENGTH} in "
          f"{100 * wins / len(lengths):.1f}% of {len(lengths)} sessions")


def run(args):
    agent = Agent(learn=not args.dontlearn, seed=args.seed)
    try:
        if args.load is not None:
            agent.load(args.load)
            print(f"Load trained model from {args.load}")
        if args.save is not None:
            check_save_path(args.save)
        board = Board(args.size, args.seed)
    except (ModelError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    view = open_display(args)
    verbose = view is not None or args.step_by_step
    results = []
    every = max(1, args.sessions // 10)
    try:
        for number in range(1, args.sessions + 1):
            caption = f"Snake Game - session {number}/{args.sessions}"
            length, steps = run_session(board, agent, view, args,
                                        verbose, caption)
            results.append((length, steps))
            if verbose:
                print(f"Session {number}/{args.sessions} over: "
                      f"length = {length}, duration = {steps}")
            elif number % every == 0:
                print(f"Session {number}/{args.sessions}: "
                      f"last length = {length}")
    except KeyboardInterrupt:     # Ctrl+C, window closed, or ESC
        print("\nInterrupted.")
    finally:
        if view:
            view.close()
    if results:
        summary(results)
    if args.save is not None:
        try:
            agent.save(args.save)
            print(f"Save learning state in {args.save}")
        except ModelError as error:
            print(f"Error: {error}", file=sys.stderr)
            return 1
    return 0


def main():
    try:
        code = run(parse_args())
    except BrokenPipeError:              # e.g. ./snake ... | head
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        code = 0
    sys.exit(code)
