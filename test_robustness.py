"""Everything an evaluator could try to break the project.

Run with:   python -m unittest -v test_robustness
"""
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest

import interpreter
from agent import Agent, ModelError
from environment import (DEAD, DOWN, EMPTY, GREEN, LEFT, RED, RIGHT, UP,
                         Board)

HERE = os.path.dirname(os.path.abspath(__file__))
ENV = dict(os.environ, SDL_VIDEODRIVER="dummy")


def write(path, text):
    with open(path, "w") as file:
        file.write(text)


def read(path):
    with open(path) as file:
        return file.read()


def snake(*args, stdin=subprocess.DEVNULL, env=ENV, timeout=120):
    """Run ./snake and return (exit code, stdout, stderr)."""
    done = subprocess.run(
        [sys.executable, os.path.join(HERE, "snake"), *args], cwd=HERE,
        env=env, stdin=stdin, capture_output=True, text=True,
        timeout=timeout)
    return done.returncode, done.stdout, done.stderr


class CleanFailure(unittest.TestCase):
    """A bad input must give a clear message, never a Python traceback."""

    def assert_clean(self, code, err, expected_code=None):
        self.assertNotIn("Traceback", err)
        if expected_code is None:
            self.assertNotEqual(code, 0)
        else:
            self.assertEqual(code, expected_code)
        self.assertTrue(err.strip(), "an error message is expected")


class TestBoard(unittest.TestCase):
    def test_start_is_random_contiguous_and_inside(self):
        starts = set()
        for _ in range(100):
            b = Board(10)
            starts.add(tuple(b.snake))
            self.assertEqual(len(b.snake), 3)
            for (r1, c1), (r2, c2) in zip(b.snake, b.snake[1:]):
                self.assertEqual(abs(r1 - r2) + abs(c1 - c2), 1)
            self.assertTrue(all(0 <= r < 10 and 0 <= c < 10
                                for r, c in b.snake))
            self.assertEqual((len(b.greens), len(b.reds)), (2, 1))
        self.assertGreater(len(starts), 20)

    def test_rules(self):
        def board(snake, greens=((0, 0), (0, 1)), reds=((9, 9),)):
            b = Board(10)
            b.snake, b.greens, b.reds = list(snake), list(greens), list(reds)
            return b
        line = [(5, 5), (6, 5), (7, 5)]
        self.assertEqual(board([(0, 5), (1, 5), (2, 5)]).step(UP), DEAD)
        self.assertEqual(board([(5, 0), (5, 1), (5, 2)]).step(LEFT), DEAD)
        self.assertEqual(board([(5, 9), (5, 8), (5, 7)]).step(RIGHT), DEAD)
        self.assertEqual(board([(9, 5), (8, 5), (7, 5)]).step(DOWN), DEAD)
        self.assertEqual(board(line).step(DOWN), DEAD)       # own neck
        self.assertEqual(board(line).step(UP), EMPTY)
        b = board(line, greens=[(4, 5), (0, 0)])
        self.assertEqual(b.step(UP), GREEN)
        self.assertEqual((len(b.snake), len(b.greens)), (4, 2))
        b = board(line, reds=[(4, 5)])
        self.assertEqual(b.step(UP), RED)
        self.assertEqual((len(b.snake), len(b.reds)), (2, 1))
        self.assertEqual(board([(5, 5)], reds=[(4, 5)]).step(UP), DEAD)

    def test_body_collision_in_a_curl(self):
        b = Board(10)
        b.snake = [(5, 5), (5, 6), (6, 6), (6, 5), (6, 4)]
        b.greens, b.reds = [(0, 0), (0, 1)], [(9, 9)]
        self.assertEqual(b.step(DOWN), DEAD)                 # (6, 5) is body

    def test_sizes(self):
        for bad in (0, 4, -1, 2.5, "10", None):
            with self.assertRaises(ValueError):
                Board(bad)
        for size in (5, 6, 15, 50):
            Board(size)

    def test_full_board_does_not_crash(self):
        b = Board(5)
        cells = [(r, c if r % 2 == 0 else 4 - c)
                 for r in range(5) for c in range(5)]
        b.snake = cells[::-1][:24][::-1]   # 24 cells, 1 free left
        b.greens, b.reds = [], []
        b._place(b.greens)
        b._place(b.greens)                 # no room: silently skipped
        self.assertLessEqual(len(b.greens), 1)

    def test_random_games_never_break_invariants(self):
        for size in (5, 7, 10, 15):
            for seed in range(60):
                b = Board(size, seed)
                while True:
                    event = b.step(b.rng.randrange(4))
                    if event == DEAD:
                        break
                    taken = b.snake + b.greens + b.reds
                    self.assertEqual(len(taken), len(set(taken)))
                    self.assertEqual((len(b.greens), len(b.reds)), (2, 1))


class TestInterpreter(unittest.TestCase):
    def test_vision_matches_the_subject_figure(self):
        b = Board(10)
        b.snake = [(7, 9), (8, 9), (8, 8)]
        b.greens, b.reds = [(2, 9), (3, 6)], [(3, 9)]
        lines = interpreter.render(interpreter.look(b)).split("\n")
        self.assertEqual([x.strip() for x in lines[:8]],
                         list("W00GR000"))
        self.assertEqual(lines[8], "W000000000HW")
        self.assertEqual([x.strip() for x in lines[9:]], list("S0W"))

    def test_vision_in_every_corner_and_tiny_snake(self):
        for size in (5, 10):
            for head in ((0, 0), (0, size - 1), (size - 1, 0),
                         (size - 1, size - 1)):
                b = Board(size)
                b.snake = [head]
                seen = interpreter.look(b)
                interpreter.encode(seen)
                interpreter.render(seen)
                self.assertTrue(all(ray.endswith("W")
                                    for ray in seen.values()))

    def test_state_does_not_depend_on_board_size(self):
        states = set()
        for size in (8, 12, 20):
            b = Board(size)
            b.snake = [(2, 2), (2, 1), (2, 0)]
            b.greens, b.reds = [(7, 7), (7, 6)], [(6, 6)]
            states.add(interpreter.encode(interpreter.look(b)))
        self.assertEqual(len(states), 1)

    def test_state_range(self):
        for seed in range(50):
            b = Board(10, seed)
            while b.step(b.rng.randrange(4)) != DEAD:
                state = interpreter.encode(interpreter.look(b))
                self.assertTrue(0 <= state < 12 ** 4)


class TestAgent(CleanFailure):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.dir.name, "m.json")

    def tearDown(self):
        self.dir.cleanup()

    def bad_model(self, content, binary=False):
        with open(self.path, "wb" if binary else "w") as file:
            file.write(content)
        with self.assertRaises(ModelError):
            Agent().load(self.path)

    def test_save_load_roundtrip(self):
        a = Agent(seed=1)
        a.learn(5, 2, 10, 6, False)
        a.sessions, a.epsilon = 7, 0.5
        a.save(self.path)
        b = Agent()
        b.load(self.path)
        self.assertEqual((b.q, b.sessions, b.epsilon), (a.q, 7, 0.5))

    def test_corrupted_models_are_refused(self):
        good_q = '{"format": "learn2slither-qtable-v1", "sessions": 0, ' \
                 '"epsilon": 1, "q": %s}'
        self.bad_model("")
        self.bad_model("not json at all")
        self.bad_model("[]")
        self.bad_model("null")
        self.bad_model("{}")
        self.bad_model("[" * 100000)                    # RecursionError
        self.bad_model(b"\xff\xfe\x00\x80binary", binary=True)
        self.bad_model(good_q % "[]")
        self.bad_model(good_q % '{"1": [1, 2, 3]}')
        self.bad_model(good_q % '{"1": [1, 2, 3, "x"]}')
        self.bad_model(good_q % '{"1": [1, 2, 3, NaN]}')
        self.bad_model(good_q % '{"abc": [1, 2, 3, 4]}')
        self.bad_model(good_q % '{"1": 5}')
        self.bad_model(good_q % '{"' + "9" * 5000 + '": [1,2,3,4]}')
        self.bad_model(good_q.replace('"sessions": 0', '"sessions": -3')
                       % "{}")
        self.bad_model(good_q.replace('"epsilon": 1', '"epsilon": 7')
                       % "{}")

    def test_missing_file_and_directory(self):
        with self.assertRaises(ModelError):
            Agent().load(os.path.join(self.dir.name, "nope.json"))
        with self.assertRaises(ModelError):
            Agent().load(self.dir.name)

    def test_dontlearn_never_touches_the_q_table(self):
        a = Agent(learn=False)
        a.learn(1, 1, 99, 2, False)
        a.end_session()
        self.assertEqual((a.q, a.sessions), ({}, 0))
        self.assertIn(a.choose(123), range(4))             # unknown state

    def test_learning_moves_q_towards_reward(self):
        a = Agent(alpha=0.5)
        a.learn(1, 0, 10, None, True)
        self.assertEqual(a.q[1][0], 5.0)

    def test_save_leaves_no_half_written_file(self):
        Agent().save(self.path)
        self.assertEqual(os.listdir(self.dir.name), ["m.json"])


class TestCommandLine(CleanFailure):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.model = os.path.join(self.dir.name, "m.json")

    def tearDown(self):
        self.dir.cleanup()

    def test_bad_arguments(self):
        for args in (["-sessions", "0"], ["-sessions", "-5"],
                     ["-sessions", "abc"], ["-sessions", "1.5"],
                     ["-sessions", ""], ["-sessions"],
                     ["-sessions", "99999999999999999999"],
                     ["-size", "4"], ["-size", "51"], ["-size", "x"],
                     ["-size", "-10"], ["-speed", "0"], ["-speed", "nan"],
                     ["-speed", "inf"], ["-speed", "abc"],
                     ["-visual", "maybe"], ["-visual"], ["-seed", "x"],
                     ["-unknown"], ["--help-me"], ["-s", "3"],
                     ["-dontlearn", "yes"], ["random_word"]):
            with self.subTest(args=args):
                code, _, err = snake(*args)
                self.assert_clean(code, err, 2)

    def test_help_works(self):
        code, out, _ = snake("-h")
        self.assertEqual(code, 0)
        self.assertIn("-sessions", out)

    def test_bad_model_files_on_load(self):
        os.mkdir(os.path.join(self.dir.name, "adir"))
        write(self.model, "garbage")
        for path in (self.model, os.path.join(self.dir.name, "nope"),
                     os.path.join(self.dir.name, "adir"), "", "/dev/null"):
            with self.subTest(path=path):
                code, _, err = snake("-load", path, "-visual", "off")
                self.assert_clean(code, err, 1)

    def test_bad_save_paths_fail_immediately(self):
        write(self.model, "x")
        for path in (self.dir.name, os.path.join(self.model, "sub", "m"),
                     "/proc/forbidden/m.json", ""):
            with self.subTest(path=path):
                t = time.time()
                code, _, err = snake("-sessions", "100000", "-save", path,
                                     "-visual", "off")
                self.assert_clean(code, err, 1)
                self.assertLess(time.time() - t, 10)     # no wasted training

    def test_save_creates_missing_folders_and_odd_names(self):
        path = os.path.join(self.dir.name, "new dir", "é model.txt")
        code, out, err = snake("-sessions", "3", "-save", path,
                               "-visual", "off")
        self.assertEqual(code, 0, err)
        self.assertTrue(os.path.isfile(path))

    def test_train_then_use_without_learning(self):
        code, _, err = snake("-sessions", "50", "-save", self.model,
                             "-visual", "off", "-seed", "1")
        self.assertEqual(code, 0, err)
        before = read(self.model)
        code, out, err = snake("-load", self.model, "-dontlearn",
                               "-sessions", "20", "-save", self.model + "2",
                               "-visual", "off")
        self.assertEqual(code, 0, err)
        self.assertIn("Load trained model", out)
        self.assertEqual(json.loads(read(self.model + "2"))["q"],
                         json.loads(before)["q"])       # model untouched

    def test_continue_training_same_file(self):
        for _ in range(2):
            code, _, err = snake("-sessions", "5", "-load", self.model,
                                 "-save", self.model, "-visual", "off") \
                if os.path.exists(self.model) else \
                snake("-sessions", "5", "-save", self.model, "-visual", "off")
            self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(read(self.model))["sessions"], 10)

    def test_dontlearn_without_model(self):
        code, _, err = snake("-dontlearn", "-sessions", "5", "-visual", "off")
        self.assertEqual(code, 0, err)

    def test_every_board_size_with_the_same_model(self):
        snake("-sessions", "200", "-save", self.model, "-visual", "off")
        for size in (5, 8, 10, 15, 50):
            code, _, err = snake("-load", self.model, "-dontlearn", "-size",
                                 str(size), "-sessions", "5", "-visual",
                                 "off")
            self.assertEqual(code, 0, f"size {size}: {err}")

    def test_visual_mode_prints_state_and_action(self):
        code, out, err = snake("-sessions", "1", "-speed", "1000", "-seed",
                               "3")
        self.assertEqual(code, 0, err)
        self.assertRegex(out, r"(?m)^(UP|LEFT|DOWN|RIGHT)$")
        self.assertIn("H", out)

    def test_no_display_available_falls_back(self):
        env = dict(os.environ, SDL_VIDEODRIVER="no-such-driver")
        code, out, err = snake("-sessions", "2", env=env)
        self.assertEqual(code, 0, err)
        self.assertIn("no graphical display", err)

    def test_step_by_step_without_stdin(self):
        code, out, err = snake("-visual", "off", "-step-by-step",
                               "-sessions", "2", stdin=subprocess.DEVNULL)
        self.assertEqual(code, 0, err)
        self.assertNotIn("Traceback", err)

    def test_step_by_step_with_enter_presses(self):
        done = subprocess.run(
            [sys.executable, os.path.join(HERE, "snake"), "-visual", "off",
             "-step-by-step", "-seed", "1"], cwd=HERE, env=ENV,
            input="\n" * 500, capture_output=True, text=True, timeout=60)
        self.assertEqual(done.returncode, 0, done.stderr)

    def test_pipe_closed_early(self):
        done = subprocess.run(
            f"{sys.executable} snake -sessions 50 -speed 1000 | head -n 1",
            shell=True, cwd=HERE, env=ENV, capture_output=True, text=True,
            timeout=60)
        self.assertNotIn("Traceback", done.stderr)

    def test_ctrl_c_stops_cleanly_and_still_saves(self):
        proc = subprocess.Popen(
            [sys.executable, os.path.join(HERE, "snake"), "-sessions",
             "5000000", "-visual", "off", "-save", self.model], cwd=HERE,
            env=ENV, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True)
        time.sleep(3)
        proc.send_signal(signal.SIGINT)
        out, err = proc.communicate(timeout=30)
        self.assertEqual(proc.returncode, 0, err)
        self.assertNotIn("Traceback", err)
        self.assertIn("Save learning state", out)
        self.assertTrue(os.path.isfile(self.model))

    def test_tiny_and_big_boards_run(self):
        for size in ("5", "50"):
            code, _, err = snake("-size", size, "-sessions", "20",
                                 "-visual", "off")
            self.assertEqual(code, 0, err)


if __name__ == "__main__":
    unittest.main()
