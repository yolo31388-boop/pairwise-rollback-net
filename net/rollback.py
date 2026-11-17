"""Deterministic rollback networking core.

Design notes:
- Snapshots capture *all* simulation-relevant state (position, hp, cooldown,
  buffs, RNG state, tick) so a rollback fully restores the simulation.
- All floats are quantized after every mutation so results are bit-stable
  across platforms (no cross-machine float drift).
- The simulation advances on fixed ticks only; wall-clock time never enters
  the replay path, so every machine replays the same frame sequence.
- State hashes cover the full state, not just position, so collision/damage
  desyncs are detected.
- rollback() restores the snapshot and replays confirmed inputs in tick
  order, so confirmed remote input is never silently overwritten.
"""

import copy
import hashlib

# Quantization step for floats: 1e-9 keeps physics precision while removing
# cross-platform low-bit float noise.
_QUANT = 1e-9

# Deterministic RNG (LCG) constants — identical on every platform.
_LCG_A = 1103515245
_LCG_C = 12345
_LCG_M = 2 ** 31


def quantize(value):
    """Round a float to the fixed quantization grid."""
    if isinstance(value, float):
        return round(value / _QUANT) * _QUANT
    return value


def snapshot(state):
    """Capture the complete simulation state (deep copy, floats quantized)."""
    snap = copy.deepcopy(state)
    return {k: quantize(v) for k, v in snap.items()}


def restore(state, snap):
    """Restore a snapshot, replacing the current state entirely."""
    return copy.deepcopy(snap)


def _canonical(state):
    items = []
    for key in sorted(state):
        value = state[key]
        if isinstance(value, float):
            value = quantize(value)
        items.append((key, value))
    return repr(items).encode("utf-8")


def hash_state(state):
    """Deterministic hash over the *full* state (not just position)."""
    digest = hashlib.sha256(_canonical(state)).hexdigest()
    return int(digest[:16], 16)


def _advance_rng(rng):
    return (rng * _LCG_A + _LCG_C) % _LCG_M


def advance(state, inputs, dt=1.0 / 60.0):
    """Advance the simulation exactly one fixed tick.

    Applies every input scheduled for the current tick, decays cooldowns,
    steps the deterministic RNG, and increments the tick counter.
    """
    new = copy.deepcopy(state)
    tick = new.get("tick", 0)

    dx = 0.0
    for inp in inputs or []:
        if inp.get("tick") == tick:
            dx += inp.get("dx", 0.0)
    new["x"] = quantize(new.get("x", 0.0) + dx)

    if "cooldown" in new:
        new["cooldown"] = quantize(max(0.0, new["cooldown"] - dt))

    if "rng" in new:
        new["rng"] = _advance_rng(new["rng"])

    new["tick"] = tick + 1
    return new


def rollback(state, snapshots, inputs, tick):
    """Roll back to the snapshot at ``tick`` and replay confirmed inputs.

    Confirmed inputs are replayed in strict tick order from the restored
    snapshot, so the post-rollback state includes every confirmed input
    instead of being overwritten by stale remote state.
    """
    if tick not in snapshots:
        raise KeyError(f"no snapshot for tick {tick}")

    new = restore(state, snapshots[tick])

    by_tick = {}
    for inp in inputs or []:
        t = inp.get("tick")
        if t is not None and t >= tick:
            by_tick.setdefault(t, []).append(inp)

    for t in sorted(by_tick):
        while new.get("tick", 0) < t:
            new = advance(new, [])
        new = advance(new, by_tick[t])

    return new


def compare_states(first, second):
    """True iff both states agree on every (quantized) field."""
    keys = set(first) | set(second)
    for key in keys:
        a, b = first.get(key), second.get(key)
        if isinstance(a, float) or isinstance(b, float):
            if quantize(a) != quantize(b):
                return False
        elif a != b:
            return False
    return True
