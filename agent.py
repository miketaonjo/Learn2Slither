"""Agent: a Q-table + an epsilon-greedy policy.

The agent knows NOTHING about the board. It only receives a state (an
integer) and a reward (a number), and answers with an action (0 to 3).
"""
import json
import math
import os
import random

N_ACTIONS = 4
MODEL_FORMAT = "learn2slither-qtable-v1"


class ModelError(Exception):
    """A model file cannot be read or written (message is user friendly)."""


class Agent:
    def __init__(self, learn=True, alpha=0.1, gamma=0.9, epsilon=1.0,
                 epsilon_min=0.01, epsilon_decay=0.995, seed=None):
        self.learn_enabled = learn
        self.alpha = alpha                  # learning rate
        self.gamma = gamma                  # importance of the future
        self.epsilon = epsilon              # probability of a random move
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.sessions = 0                   # sessions this model learned from
        self.q = {}                         # state -> [Q(UP), Q(LEFT), ...]
        self.rng = random.Random(seed)

    # ------------------------------------------------------------------
    # Decision
    # ------------------------------------------------------------------
    def choose(self, state):
        """Epsilon-greedy: sometimes explore, otherwise take the best."""
        if self.learn_enabled and self.rng.random() < self.epsilon:
            return self.rng.randrange(N_ACTIONS)
        values = self.q.get(state, [0.0] * N_ACTIONS)
        best = max(values)
        # Ties (e.g. unknown state) are broken randomly
        return self.rng.choice(
            [action for action in range(N_ACTIONS) if values[action] == best])

    # ------------------------------------------------------------------
    # Learning
    # ------------------------------------------------------------------
    def learn(self, state, action, reward, next_state, done):
        """Q(s,a) += alpha * (reward + gamma * max Q(s',.) - Q(s,a))."""
        if not self.learn_enabled:
            return
        row = self.q.setdefault(state, [0.0] * N_ACTIONS)
        target = reward
        if not done:
            target += self.gamma * max(
                self.q.get(next_state, [0.0] * N_ACTIONS))
        row[action] += self.alpha * (target - row[action])

    def end_session(self):
        """Explore a bit less after each training session."""
        if self.learn_enabled:
            self.sessions += 1
            self.epsilon = max(self.epsilon_min,
                               self.epsilon * self.epsilon_decay)

    # ------------------------------------------------------------------
    # Export / import
    # ------------------------------------------------------------------
    def save(self, path):
        data = {
            "format": MODEL_FORMAT,
            "sessions": self.sessions,
            "epsilon": self.epsilon,
            "q": {str(state): row for state, row in self.q.items()},
        }
        tmp = path + ".tmp"
        try:
            folder = os.path.dirname(path)
            if folder:
                os.makedirs(folder, exist_ok=True)
            with open(tmp, "w", encoding="utf-8") as file:
                json.dump(data, file)
            os.replace(tmp, path)           # never leaves a half-written model
        except OSError as error:
            raise ModelError(f"cannot save model to '{path}': "
                             f"{error.strerror or error}") from error

    def load(self, path):
        if not os.path.isfile(path):
            raise ModelError(f"model file '{path}' not found")
        try:
            with open(path, encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, ValueError, RecursionError) as error:
            raise ModelError(
                f"model file '{path}' is not readable: {error}") from error
        try:
            q = self._check(data)
        except (KeyError, TypeError, ValueError, AttributeError) as error:
            raise ModelError(
                f"model file '{path}' is not a valid model "
                f"({error})") from error
        self.q = q
        self.sessions = data["sessions"]
        self.epsilon = data["epsilon"]

    @staticmethod
    def _check(data):
        """Validate EVERYTHING in a file before trusting it."""
        if not isinstance(data, dict) or data.get("format") != MODEL_FORMAT:
            raise ValueError("wrong format")
        sessions, epsilon = data["sessions"], data["epsilon"]
        if (not isinstance(sessions, int) or isinstance(sessions, bool)
                or sessions < 0):
            raise ValueError("bad 'sessions'")
        if (not isinstance(epsilon, (int, float)) or isinstance(epsilon, bool)
                or not 0 <= epsilon <= 1):
            raise ValueError("bad 'epsilon'")
        q = {}
        for key, row in data["q"].items():
            if (not isinstance(row, list) or len(row) != N_ACTIONS
                    or not all(isinstance(v, (int, float))
                               and not isinstance(v, bool)
                               and math.isfinite(v) for v in row)):
                raise ValueError(f"bad Q-values for state {key}")
            q[int(key)] = [float(v) for v in row]
        return q
