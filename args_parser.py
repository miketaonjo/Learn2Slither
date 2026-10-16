import argparse


def positive_int(text):
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{text!r} is not an integer")
    if value < 1:
        raise argparse.ArgumentTypeError("must be positive int")
    return value


def parse_args():
    parser = argparse.ArgumentParser(prog="snake", allow_abbrev=False)
    parser.add_argument("-size", type=positive_int, default=10)
    parser.add_argument("-sessions", type=positive_int, default=1)
    parser.add_argument("-save")
    parser.add_argument("-load")
    parser.add_argument("-visual", choices=("on", "off"), default="on")
    parser.add_argument("-speed", type=positive_int, default=10)
    parser.add_argument("-dontlearn", action="store_true")
    parser.add_argument("-step-by-step", action="store_true")
    args = parser.parse_args()
    if not 8 <= args.size <= 15:
        parser.error("Board size must be between 8 and 15")
    if args.step_by_step and args.visual == "off":
        parser.error("-step-by-step needs -visual on")
    return args
