import json
import math
import os
import random

from interpreter import VALUES_PER_DIRECTION

N_STATES = VALUES_PER_DIRECTION ** 4
N_ACTIONS = 4
ACTION_ORDER = ["UP", "LEFT", "DOWN", "RIGHT"]


class ModelError(Exception):
    """Represent errors encountered while loading or saving a model"""


class Agent:
    def __init__(
        self,
        learn=True,
        alpha=0.1,
        gamma=0.9,
        epsilon=1.0,
        epsilon_min=0.01,
        epsilon_decay=0.99
    ):
        """Initialize the Q-table and learning parameters"""
        self.q = [[0.0] * N_ACTIONS for _ in range(N_STATES)]
        self.learn = learn
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.sessions = 0

    def act(self, state):
        """Choose an action using the epsilon-greedy policy"""
        if not 0 <= state < N_STATES:
            raise ValueError("Invalid state")

        if self.learn and random.random() < self.epsilon:
            return random.randrange(N_ACTIONS)

        values = self.q[state]
        best = max(values)
        return random.choice([
            action for action, value in enumerate(values)
            if value == best
        ])

    def update(self, state, action, reward, next_state, done):
        """Update the Q-value for the observed transition"""
        if not self.learn:
            return

        if not 0 <= state < N_STATES:
            raise ValueError("Invalid state")
        if not 0 <= next_state < N_STATES:
            raise ValueError("Invalid next state")
        if not 0 <= action < N_ACTIONS:
            raise ValueError("Invalid action")

        target = reward
        if not done:
            target += self.gamma * max(self.q[next_state])

        self.q[state][action] += (
            self.alpha * (target - self.q[state][action])
        )

    def end_session(self):
        """Record the end of a session and decay exploration"""
        self.sessions += 1
        if self.learn:
            self.epsilon = max(
                self.epsilon_min,
                self.epsilon * self.epsilon_decay,
            )

    def save(self, path):
        """Save the trained model to a JSON file"""
        if not isinstance(path, (str, os.PathLike)):
            raise ModelError("A valid save path is required")

        path = os.fspath(path)
        if not isinstance(path, str) or not path.strip():
            raise ModelError("A valid save path is required")

        rows = {
            str(state): [round(value, 4) for value in row]
            for state, row in enumerate(self.q)
            if any(row)
        }

        data = {
            "states": N_STATES,
            "actions": N_ACTIONS,
            "action_order": ACTION_ORDER,
            "sessions": self.sessions,
            "epsilon": self.epsilon,
            "visited_states": len(rows),
            "q": rows,
        }

        tmp = path + ".tmp"

        try:
            folder = os.path.dirname(path)
            if folder:
                os.makedirs(folder, exist_ok=True)

            with open(tmp, "w", encoding="utf-8") as file:
                json.dump(
                    data,
                    file,
                    indent=2,
                    allow_nan=False,
                )
                file.write("\n")
                file.flush()
                os.fsync(file.fileno())

            os.replace(tmp, path)

        except (OSError, TypeError, ValueError) as error:
            try:
                os.remove(tmp)
            except FileNotFoundError:
                pass
            except OSError:
                pass

            raise ModelError(
                f"Cannot save model to '{path}': {error}"
            ) from error

    def load(self, path):
        """Load and validate a model from a JSON file"""
        if not isinstance(path, (str, os.PathLike)):
            raise ModelError("A valid model path is required")

        path = os.fspath(path)
        if not isinstance(path, str) or not path.strip():
            raise ModelError("A valid model path is required")

        try:
            with open(path, "r", encoding="utf-8") as file:
                data = json.load(file)

        except FileNotFoundError as error:
            raise ModelError(
                f"Model file not found: '{path}'."
            ) from error
        except PermissionError as error:
            raise ModelError(
                f"Permission denied when reading '{path}'."
            ) from error
        except json.JSONDecodeError as error:
            raise ModelError(
                f"Invalid JSON in model file '{path}' "
                f"at line {error.lineno}, column {error.colno}."
            ) from error
        except UnicodeDecodeError as error:
            raise ModelError(
                f"Model file '{path}' is not valid UTF-8"
            ) from error
        except OSError as error:
            raise ModelError(
                f"Cannot read model file '{path}': {error}"
            ) from error

        try:
            if not isinstance(data, dict):
                raise ValueError("The document must be a JSON object")

            if type(data.get("states")) is not int:
                raise ValueError("Invalid state count")
            if data["states"] != N_STATES:
                raise ValueError("Incompatible state count")

            if type(data.get("actions")) is not int:
                raise ValueError("Invalid action count")
            if data["actions"] != N_ACTIONS:
                raise ValueError("Incompatible action count")

            if data.get("action_order", ACTION_ORDER) != ACTION_ORDER:
                raise ValueError("Incompatible action order")

            sessions = data["sessions"]
            if type(sessions) is not int or sessions < 0:
                raise ValueError("Invalid session count")

            epsilon = data["epsilon"]
            if (
                type(epsilon) not in (int, float)
                or not math.isfinite(epsilon)
                or not 0 <= epsilon <= 1
            ):
                raise ValueError("Invalid epsilon value")

            saved_rows = data["q"]
            if not isinstance(saved_rows, dict):
                raise ValueError("Invalid Q-table")

            q = [[0.0] * N_ACTIONS for _ in range(N_STATES)]

            for key, row in saved_rows.items():
                if not isinstance(key, str) or not key.isdigit():
                    raise ValueError("Invalid state index")

                state = int(key)
                if not 0 <= state < N_STATES:
                    raise ValueError("State index out of range")

                if not isinstance(row, list) or len(row) != N_ACTIONS:
                    raise ValueError("Invalid Q-table row.")

                for value in row:
                    if (
                        type(value) not in (int, float)
                        or not math.isfinite(value)
                    ):
                        raise ValueError("Invalid Q-value")

                q[state] = [float(value) for value in row]

        except (KeyError, TypeError, ValueError, OverflowError) as error:
            raise ModelError(
                f"Incompatible or corrupted model file '{path}': "
                f"{error}"
            ) from error

        self.q = q
        self.sessions = sessions
        self.epsilon = float(epsilon)
