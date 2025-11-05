import pytest
from joytide import art
import random


def test_valid_art(capsys):
    art(theme="animal", size="small")
    captured = capsys.readouterr()
    # something needs to be printed ( actual output depends on random )
    assert captured.out.strip() != ""


def test_invalid_theme(capsys):
    art(theme="invalid_theme", size="small")
    # see what is printed to stdout
    captured = capsys.readouterr()
    assert "Invalid theme" in captured.out


def test_invalid_size(capsys):
    # huge is invalid
    art(theme="animal", size="huge")
    # see what is printed to stdout
    captured = capsys.readouterr()
    assert "Invalid size" in captured.out


def test_random_theme_calls_choice(monkeypatch, capsys):
    called = []

    # rather than using real random.choice in the test
    def fake_choice(seq):
        called.append(seq)
        return seq[0]

    monkeypatch.setattr(random, "choice", fake_choice)
    art(theme="random", size="small")
    captured = capsys.readouterr()
    assert any(isinstance(seq, list) for seq in called)
    assert captured.out.strip() != ""
