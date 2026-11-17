import pytest

from net.rollback import advance, compare_states, hash_state, restore, rollback, snapshot


def state():
    return {"tick": 0, "x": 0.0, "hp": 10, "cooldown": 0.5, "rng": 1234}


def test_snapshot_includes_hp():
    assert snapshot(state())["hp"] == 10


def test_snapshot_includes_cooldown():
    assert snapshot(state())["cooldown"] == pytest.approx(0.5)


def test_snapshot_includes_rng():
    assert snapshot(state())["rng"] == 1234


def test_restore_restores_hp():
    current = state()
    current["hp"] = 0
    restored = restore(current, snapshot(state()))
    assert restored["hp"] == 10


def test_hash_changes_when_hp_changes():
    first = state()
    second = state()
    second["hp"] = 9
    assert hash_state(first) != hash_state(second)


def test_hash_changes_when_x_changes():
    first = state()
    second = state()
    second["x"] = 1.0
    assert hash_state(first) != hash_state(second)


def test_advance_increments_tick():
    assert advance(state(), [])["tick"] == 1


def test_advance_applies_input_delta():
    assert advance(state(), [{"tick": 0, "dx": 2.0}])["x"] == pytest.approx(2.0)


def test_rollback_restores_tick():
    current = state()
    current["tick"] = 9
    assert rollback(current, {0: snapshot(state())}, [], 0)["tick"] == 0


def test_rollback_restores_hp():
    current = state()
    current["hp"] = 0
    assert rollback(current, {0: snapshot(state())}, [], 0)["hp"] == 10


def test_rollback_replays_confirmed_inputs():
    current = state()
    result = rollback(current, {0: snapshot(state())}, [{"tick": 0, "dx": 1.0}, {"tick": 1, "dx": 1.0}], 0)
    assert result["x"] == pytest.approx(2.0)


def test_compare_states_detects_position_desync():
    first = state()
    second = state()
    second["x"] = 1.0
    assert compare_states(first, second) is False


def test_compare_states_detects_hp_desync():
    first = state()
    second = state()
    second["hp"] = 9
    assert compare_states(first, second) is False


def test_advance_decays_cooldown():
    assert advance(state(), [], dt=1.0 / 60.0)["cooldown"] == pytest.approx(0.4833, rel=1e-3)


def test_advance_without_inputs_still_advances_tick():
    result = advance(state(), [])
    assert result["tick"] == 1
    assert result["x"] == pytest.approx(0.0)
