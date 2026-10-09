import json
import os
import random
from interpreter import VALUES_PER_DIRECTION

N_STATES = VALUES_PER_DIRECTION ** 4
N_ACTIONS = 4
FORMAT_VERSION = 1


class ModelError(Exception):
    """Raised when a model file cannot be read, written or trusted."""

class Agent:
    def __init__(self, learn=True, alpha=0.1, gamma=0.9,
                 epsilon=1.0, epsilon_min=0.01, epsilon_decay=0.99):
        self.q = [[0.0] * N_ACTIONS for _ in range(N_STATES)]
        self.learn = learn
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.sessions = 0

    def act(self, state):
        if self.learn and random.random() < self.epsilon:
            return random.randrange(N_ACTIONS)
        values = self.q[state]
        best = max(values)
        return random.choice([a for a, v in enumerate(values) if v == best])

    def update(self, state, action, reward, next_state, done):
        if not self.learn:
            return
        target = reward
        if not done:
            target += self.gamma * max(self.q[next_state])
        self.q[state][action] += self.alpha * (target - self.q[state][action])

    def end_session(self):
        self.sessions += 1
        if self.learn:
            self.epsilon = max(self.epsilon_min,
                               self.epsilon * self.epsilon_decay)

    def save(self, path):
        data = {"version": FORMAT_VERSION, "states": N_STATES,
                "actions": N_ACTIONS, "sessions": self.sessions,
                "epsilon": self.epsilon, "q": self.q}
        tmp = path + ".tmp"
        try:
            folder = os.path.dirname(path)
            if folder:
                os.makedirs(folder, exist_ok=True)
            with open(tmp, "w") as file:
                json.dump(data, file)
            os.replace(tmp, path)
        except OSError as error:
            raise ModelError(f"cannot save to {path}: {error.strerror}")

    def load(self, path):
        try:
            with open(path) as file:
                data = json.load(file)
        except OSError as error:
            raise ModelError(f"cannot read {path}: {error.strerror}")
        except ValueError:
            raise ModelError(f"{path} is not a valid model file")
        try:
            q = data["q"]
            valid = (data["version"] == FORMAT_VERSION
                     and data["states"] == N_STATES
                     and data["actions"] == N_ACTIONS
                     and len(q) == N_STATES
                     and all(len(row) == N_ACTIONS
                             and all(isinstance(v, (int, float))
                                     for v in row)
                             for row in q))
            sessions = int(data["sessions"])
            epsilon = float(data["epsilon"])
        except (KeyError, TypeError, ValueError):
            valid = False
        if not valid:
            raise ModelError(f"{path} is not a compatible model file")
        self.q, self.sessions, self.epsilon = q, sessions, epsilon
