"""Tests for the command-line entry point."""

from __future__ import annotations

from calculator.cli import main


def test_oneshot_expression(capsys):
    exit_code = main(["(1", "+", "2)", "-", "-3"])
    assert exit_code == 0
    assert capsys.readouterr().out.strip() == "6"


def test_oneshot_error_returns_nonzero(capsys):
    exit_code = main(["1", "+"])
    assert exit_code == 1
    assert "Error" in capsys.readouterr().err


def test_repl_evaluates_then_exits_on_eof(capsys, monkeypatch):
    lines = iter(["1 + 2", "10 - 4"])

    def fake_input(_prompt: str) -> str:
        try:
            return next(lines)
        except StopIteration:
            raise EOFError from None

    monkeypatch.setattr("builtins.input", fake_input)
    assert main([]) == 0

    out_lines = capsys.readouterr().out.splitlines()
    assert "3" in out_lines
    assert "6" in out_lines
