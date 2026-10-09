import sys
from environment import Board, DEAD, ACTION_NAMES
from interpreter import look, render, encode, reward
from agent import Agent, ModelError
from args_parser import parse_args

SIZE = 10
STEP_CAP_PER_CELL = 100

def positive_int(text):
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{text!r} is not an integer")
    if value < 1:
        raise argparse.ArgumentTypeError("must be >= 1")
    return value

def open_display(speed):
    try:
        from display import Display
        return Display(SIZE, speed)
    except (ImportError, RuntimeError) as error:
        sys.exit(f"Error: cannot open the graphical display: {error}")
    
def run_session(board, agent, view, step_by_step):
    board.reset()
    seen = look(board)
    state = encode(seen)
    cap = STEP_CAP_PER_CELL * board.size * board.size
    while board.steps < cap:
        if view:
            view.draw(board, wait=not step_by_step)
            print(render(seen))
            if step_by_step:
                view.wait_key()
        action = agent.act(state)
        if view:
            print(ACTION_NAMES[action])
        event = board.step(action)
        done = event == DEAD
        if not done:
            seen = look(board)
        next_state = state if done else encode(seen)
        agent.update(state, action, reward(event), next_state, done)
        if done:
            break
        state = next_state
    return board.max_length, board.steps

def main():
    args = parse_args()
    agent = Agent(learn=not args.dontlearn)
    board = Board(SIZE)
    view = None
    best_length = best_duration = 0
    try:
        if args.load:
            agent.load(args.load)
            print(f"Load trained model from {args.load}")
        if args.visual == "on":
            view = open_display(args.speed)
        for _ in range(args.sessions):
            length, duration = run_session(board, agent, view,
                                           args.step_by_step)
            agent.end_session()
            best_length = max(best_length, length)
            best_duration = max(best_duration, duration)
        print(f"Game over, max length = {best_length}, "
              f"max duration = {best_duration}")
        if args.save:
            agent.save(args.save)
            print(f"Save learning state in {args.save}")
    except ModelError as error:
        sys.exit(f"Error: {error}")
    except KeyboardInterrupt:
        print("\nInterrupted")
    finally:
        if view:
            view.close()


if __name__ == "__main__":
    main()