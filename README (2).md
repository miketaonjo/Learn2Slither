# Learn2Slither

Snake controlled by a Q-learning agent (Q-table).

## Install
    python3 -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    chmod +x snake

## Usage
    ./snake -sessions 10 -save models/10sess.json -visual off
    ./snake -visual on -load models/10000sess.json -dontlearn -sessions 5
    ./snake -visual on -load models/100sess.json -sessions 10 -dontlearn -step-by-step
    ./snake -load models/10000sess.json -dontlearn -size 12   # bonus

Options: -sessions N, -save FILE, -load FILE, -visual on|off, -dontlearn,
-step-by-step (SPACE/ENTER = next move, ESC = quit), -speed MOVES_PER_SEC,
-size N (bonus), -seed N.

## Models (models/)
1, 10, 100, 1000, 5000 and 10000 training sessions (best: 10000sess.json).

## Tests
    flake8 .
    python -m unittest -v test_robustness
