import argparse

def parse_args():
    parser = argparse.ArgumentParser(prog="snake", allow_abbrev=False)
    parser.add_argument("-sessions", type=positive_int, default=1)
    parser.add_argument("-save")
    parser.add_argument("-load")
    parser.add_argument("-visual", choices=("on", "off"), default="on")
    parser.add_argument("-speed", type=positive_int, default=10)
    parser.add_argument("-dontlearn", action="store_true")
    parser.add_argument("-step-by-step", action="store_true")
    args = parser.parse_args()
    if args.step_by_step and args.visual == "off":
        parser.error("-step-by-step needs -visual on")
    return args