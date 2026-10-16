import sys
from environment import Board, DEAD, ACTION_NAMES
from interpreter import look, render, encode, reward
from agent import Agent, ModelError
from args_parser import parse_args


def open_display(size, speed):
    """Create and initialize the game display"""
    try:
        from display import Display
        return Display(size, speed)
    except (ImportError, RuntimeError) as error:
        sys.exit(f"Error: cannot open the display: {error}")


def run_session(board, agent, view, step_by_step):
    """Run one game session and return its maximum length and duration"""
    board.reset()
    seen = look(board)
    state = encode(seen)
    while True:
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
    view = None
    try:
        args = parse_args()
        agent = Agent(learn=not args.dontlearn)
        board = Board(args.size)
        lengths = []
        durations = []
        if args.load:
            agent.load(args.load)
            print(f"Load trained model from {args.load}")
        if args.visual == "on":
            view = open_display(args.size, args.speed)
        for _ in range(args.sessions):
            length, duration = run_session(
                board,
                agent,
                view,
                args.step_by_step
            )
            agent.end_session()
            lengths.append(length)
            durations.append(duration)
        count = len(lengths)
        if count > 0:
            print("\n--- Final results ---")
            print(f"Nb of sessions : {count}")
            print(f"Max length : {max(lengths)}")
            print(f"Max duration : {max(durations)}")
            print(
                f"Sessions with length >= 10 : "
                f"{sum(n >= 10 for n in lengths)}/{count}"
            )
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
