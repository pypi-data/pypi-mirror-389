import importlib
import random

import pytest

from joytide import race as race_fn

_race_impl_mod = importlib.import_module(race_fn.__module__)


def _no_sleep(_seconds: float):
    return None


def _no_clear(_cmd: str):
    return 0


def _fake_banner(text: str, **kwargs) -> str:
    return f"[{text}]"


def _fake_confetti(**kwargs):
    print("<confetti>")


def test_requires_two_racers(capsys):
    race_fn(["only_one"])
    out = capsys.readouterr().out
    assert "at least two" in out


def test_width_too_small(capsys):
    race_fn(["A", "B"], width=5)
    out = capsys.readouterr().out
    assert "Width too small" in out


def test_delay_must_be_positive(capsys):
    race_fn(["A", "B"], delay=0)
    out = capsys.readouterr().out
    assert "Delay must be" in out


def test_race_deterministic_winner(monkeypatch, capsys):
    monkeypatch.setattr(_race_impl_mod.time, "sleep", _no_sleep)
    monkeypatch.setattr(_race_impl_mod.os, "system", _no_clear)

    if hasattr(_race_impl_mod, "banner"):
        monkeypatch.setattr(_race_impl_mod, "banner", _fake_banner)
    if hasattr(_race_impl_mod, "confetti"):
        monkeypatch.setattr(_race_impl_mod, "confetti", _fake_confetti)

    monkeypatch.setattr(random, "randint", lambda a, b: 1)

    names = ["Alice", "Bob"]
    race_fn(names, width=12, delay=0.001)

    out = capsys.readouterr().out

    assert "[🏁 ASCII RACE 🏁]" in out
    assert "Winner: Alice!" in out
    assert "[🏁 ASCII RACE 🏁]" in out
