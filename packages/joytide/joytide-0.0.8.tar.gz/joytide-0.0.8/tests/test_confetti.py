import pytest
from joytide.core import confetti


def test_confetti_invalid_dimensions():
    # width or height ≤ 0 should raise
    with pytest.raises(ValueError):
        confetti(width=0, height=10, spawn_time=0.1)
    with pytest.raises(ValueError):
        confetti(width=10, height=-1, spawn_time=0.1)


def test_confetti_invalid_physics_values():
    # gravity and wind can't be negative
    with pytest.raises(ValueError):
        confetti(width=10, height=5, gravity=-0.5)
    with pytest.raises(ValueError):
        confetti(width=10, height=5, wind=-0.5)
    # spawn_time should be > 0
    with pytest.raises(ValueError):
        confetti(width=10, height=5, spawn_time=0)


def test_confetti_runs_and_prints(monkeypatch, capsys):
    """
    Run a very short confetti simulation to ensure it prints frames.
    Monkeypatch time.sleep and time.time to make it end fast.
    """
    import time

    fake_time = [0]

    def fake_now():
        fake_time[0] += 0.05
        return fake_time[0]

    monkeypatch.setattr(time, "time", fake_now)
    monkeypatch.setattr(time, "sleep", lambda x: None)

    # should print some characters to stdout
    confetti(width=15, height=5, n_particles=20, spawn_time=0.2)
    out = capsys.readouterr().out
    assert any(c in out for c in ["*", "✨", "🎉", "💫"])
    assert len(out.strip()) > 0


def test_confetti_stops_naturally(monkeypatch):
    """Ensure confetti eventually ends once particles have landed."""
    import time

    fake_time = [0]

    def fake_now():
        fake_time[0] += 0.5
        return fake_time[0]

    monkeypatch.setattr(time, "time", fake_now)
    monkeypatch.setattr(time, "sleep", lambda x: None)

    # Should finish cleanly
    confetti(width=10, height=5, n_particles=10, spawn_time=0.5)
