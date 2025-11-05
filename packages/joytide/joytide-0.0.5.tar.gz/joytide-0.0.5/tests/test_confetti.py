import pytest
from joytide import confetti


def test_confetti_invalid_inputs():
    with pytest.raises(ValueError):
        confetti(width=0)
    with pytest.raises(ValueError):
        confetti(height=-1)
    with pytest.raises(ValueError):
        confetti(density=2)
    with pytest.raises(ValueError):
        confetti(duration=0)


def test_confetti_runs_and_prints(capsys):
    # Run a very short version to test output
    confetti(width=10, height=3, duration=0.3, density=0.3)
    out = capsys.readouterr().out
    assert "*" in out or "✨" in out or "🎉" in out
    assert len(out) > 0
