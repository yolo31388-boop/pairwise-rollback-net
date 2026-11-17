"""Deterministic rollback networking (starter code with known defects)."""


def snapshot(state):
    return {"x": state.get("x", 0)}


def restore(state, snap):
    return dict(state)


def hash_state(state):
    return 0


def advance(state, inputs, dt=1.0 / 60.0):
    return dict(state)


def rollback(state, snapshots, inputs, tick):
    return dict(state)


def compare_states(first, second):
    return True
