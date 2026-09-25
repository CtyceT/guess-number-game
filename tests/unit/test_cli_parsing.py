"""Unit tests for the pure input-parsing functions in guessing_game.cli."""

import pytest

from guessing_game.cli import PlayAgainChoice, parse_guess, parse_play_again


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("42", 42),
        ("1", 1),
        ("100", 100),
        (" 42 ", 42),
        ("\t7\n", 7),
        ("0", 0),
        ("101", 101),
        ("-5", -5),
        ("9" * 18, int("9" * 18)),
        ("9" * 19, 10**18),
        ("-" + "9" * 19, -(10**18)),
        ("9" * 5000, 10**18),
    ],
)
def test_parse_guess_accepts_plain_integers(raw: str, expected: int) -> None:
    """Plain digit strings (optionally negative) parse to integers."""
    assert parse_guess(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "   ",
        "3.5",
        "50.0",
        "abc",
        "#",
        "+5",
        "007",
        "1_0",
        "５",
        "-",
        "--5",
        "4 2",
        "0x10",
    ],
)
def test_parse_guess_rejects_invalid_format(raw: str) -> None:
    """Anything that is not a plain integer literal returns None."""
    assert parse_guess(raw) is None


@pytest.mark.parametrize("raw", ["", "   ", "\t"])
def test_parse_play_again_blank_means_replay(raw: str) -> None:
    """Enter (blank input) means play again."""
    assert parse_play_again(raw) is PlayAgainChoice.REPLAY


@pytest.mark.parametrize("raw", ["n", "N", " n ", "\tN\n"])
def test_parse_play_again_n_means_quit(raw: str) -> None:
    """'n' or 'N', ignoring surrounding whitespace, means quit."""
    assert parse_play_again(raw) is PlayAgainChoice.QUIT


@pytest.mark.parametrize("raw", ["y", "Y", "yes", "abc", "nn", "no", "1"])
def test_parse_play_again_other_input_is_unknown(raw: str) -> None:
    """Every other input is unrecognised and must be asked again."""
    assert parse_play_again(raw) is PlayAgainChoice.UNKNOWN
