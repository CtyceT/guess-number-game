"""Integration tests that drive guessing_game.cli.run with scripted I/O.

No real terminal is used: input and output are injected callables.
"""

import logging
import random
import re
import sys
from collections.abc import Iterator

import pytest

from guessing_game.cli import configure_logging, run
from guessing_game.engine import GameEngine


class FixedRandom(random.Random):
    """A Random whose randint returns scripted values in order."""

    def __init__(self, values: list[int]) -> None:
        """Initializes the fake.

        Args:
            values: Values returned by successive randint calls. The last
                value is repeated once the list is exhausted.
        """
        super().__init__()
        self._values = list(values)
        self._next = 0

    def randint(self, a: int, b: int) -> int:
        """Returns the next scripted value, ignoring the bounds.

        Args:
            a: Lower bound requested by the caller (unused).
            b: Upper bound requested by the caller (unused).

        Returns:
            The next scripted value.
        """
        index = min(self._next, len(self._values) - 1)
        self._next += 1
        return self._values[index]


class ScriptedInput:
    """An input_fn that replays a fixed list of answers and records prompts."""

    def __init__(self, answers: list[str]) -> None:
        """Initializes the script.

        Args:
            answers: Answers returned by successive calls.
        """
        self._answers = list(answers)
        self.prompts: list[str] = []

    def __call__(self, prompt: str) -> str:
        """Returns the next scripted answer.

        Args:
            prompt: The prompt the game asked with.

        Returns:
            The next scripted answer.

        Raises:
            AssertionError: If the game asks for more input than scripted.
        """
        self.prompts.append(prompt)
        if not self._answers:
            raise AssertionError(f"unexpected extra prompt: {prompt!r}")
        return self._answers.pop(0)


class OutputRecorder:
    """An output_fn that records every message."""

    def __init__(self) -> None:
        """Initializes an empty recorder."""
        self.lines: list[str] = []

    def __call__(self, message: str) -> None:
        """Records one message.

        Args:
            message: The message the game displayed.
        """
        self.lines.append(message)


@pytest.fixture
def package_logger() -> Iterator[logging.Logger]:
    """Yields the package logger and restores its handlers and level after.

    Yields:
        The ``guessing_game`` logger.
    """
    logger = logging.getLogger("guessing_game")
    saved_handlers = list(logger.handlers)
    saved_level = logger.level
    yield logger
    logger.handlers[:] = saved_handlers
    logger.setLevel(saved_level)


def _game_messages(caplog: pytest.LogCaptureFixture) -> list[str]:
    """Extracts the messages logged by the guessing_game package.

    Args:
        caplog: The pytest log capture fixture.

    Returns:
        Formatted messages of every record from a guessing_game logger.
    """
    return [
        record.getMessage()
        for record in caplog.records
        if record.name.startswith("guessing_game")
    ]


# --- User Story 1: starting a game -----------------------------------------


def test_configure_logging_installs_single_stdout_info_handler(
    package_logger: logging.Logger,
) -> None:
    """configure_logging sets INFO and exactly one stdout handler."""
    configure_logging()
    configure_logging()
    handlers = [
        handler
        for handler in package_logger.handlers
        if isinstance(handler, logging.StreamHandler)
    ]
    assert len(handlers) == 1
    assert handlers[0].stream is sys.stdout
    assert package_logger.level == logging.INFO


def test_run_logs_new_round_once_at_info(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Starting the game logs the "新局開始" event exactly once at INFO."""
    caplog.set_level(logging.INFO, logger="guessing_game")
    engine = GameEngine(FixedRandom([50]))
    exit_code = run(
        input_fn=ScriptedInput(["50", "n"]),
        output_fn=OutputRecorder(),
        engine=engine,
    )
    assert exit_code == 0
    assert _game_messages(caplog).count("新局開始") == 1
    started = [r for r in caplog.records if r.getMessage() == "新局開始"]
    assert started[0].levelno == logging.INFO


# --- User Story 2: guessing and hints --------------------------------------

GUESS_PROMPT = "請輸入猜測（1-100）："


def test_hints_then_correct_answer_ends_round() -> None:
    """Too-high, too-low, then correct guesses show the matching messages."""
    engine = GameEngine(FixedRandom([50]))
    answers = ScriptedInput(["70", "30", "50", "n"])
    output = OutputRecorder()
    run(input_fn=answers, output_fn=output, engine=engine)

    assert output.lines[0] == "太大"
    assert output.lines[1] == "太小"
    assert "答對" in output.lines[2]
    assert engine.is_finished is True
    assert answers.prompts[:3] == [GUESS_PROMPT] * 3


def test_secret_is_not_shown_before_the_answer_is_correct() -> None:
    """No message shown before the win contains the secret number (FR-002)."""
    engine = GameEngine(FixedRandom([50]))
    output = OutputRecorder()
    run(
        input_fn=ScriptedInput(["70", "30", "50", "n"]),
        output_fn=output,
        engine=engine,
    )
    win_index = next(i for i, line in enumerate(output.lines) if "答對" in line)
    assert all("50" not in line for line in output.lines[:win_index])


# --- User Story 3: input validation ----------------------------------------

FORMAT_ERROR = "輸入無效：請輸入 1 到 100 的整數。"
RANGE_ERROR = "輸入無效：數字必須介於 1 到 100 之間。"


def test_invalid_inputs_show_errors_and_are_not_counted() -> None:
    """Bad format and out-of-range inputs re-prompt without using attempts."""
    engine = GameEngine(FixedRandom([50]))
    answers = ScriptedInput(
        ["abc", "3.5", "+5", "007", "", "0", "101", "-5", " 42 ", "50", "n"]
    )
    output = OutputRecorder()
    run(input_fn=answers, output_fn=output, engine=engine)

    assert output.lines[:5] == [FORMAT_ERROR] * 5
    assert output.lines[5:8] == [RANGE_ERROR] * 3
    assert output.lines[8] == "太小"
    assert "答對" in output.lines[9]
    assert answers.prompts[:10] == [GUESS_PROMPT] * 10
    assert engine.attempts == 2
    win_index = next(i for i, line in enumerate(output.lines) if "答對" in line)
    assert all("50" not in line for line in output.lines[:win_index])


# --- User Story 4: finishing and playing again -----------------------------

PLAY_AGAIN_PROMPT = "再玩一局？按 Enter 再玩，輸入 n 離開："
PLAY_AGAIN_RETRY = "請按 Enter 再玩，或輸入 n 離開。"


def test_win_shows_attempt_count_and_asks_to_play_again(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Winning shows the total valid guesses and asks about another round."""
    caplog.set_level(logging.INFO, logger="guessing_game")
    answers = ScriptedInput(["70", "30", "50", "n"])
    output = OutputRecorder()
    run(
        input_fn=answers,
        output_fn=output,
        engine=GameEngine(FixedRandom([50])),
    )
    assert "答對！你總共猜了 3 次。" in output.lines
    assert answers.prompts[3] == PLAY_AGAIN_PROMPT
    assert "本局結束，總猜測次數：3" in _game_messages(caplog)


def test_enter_starts_a_new_round_with_attempts_reset(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Blank input replays: new secret, attempts back to zero, event logged."""
    caplog.set_level(logging.INFO, logger="guessing_game")
    output = OutputRecorder()
    exit_code = run(
        input_fn=ScriptedInput(["50", "", "20", "n"]),
        output_fn=output,
        engine=GameEngine(FixedRandom([50, 20])),
    )
    assert exit_code == 0
    wins = [line for line in output.lines if "答對" in line]
    assert wins == ["答對！你總共猜了 1 次。", "答對！你總共猜了 1 次。"]
    assert _game_messages(caplog).count("新局開始") == 2


@pytest.mark.parametrize("answer", ["n", "N"])
def test_n_quits_with_goodbye_and_logs_departure(
    answer: str, caplog: pytest.LogCaptureFixture
) -> None:
    """'n' or 'N' ends the game normally with exit code 0."""
    caplog.set_level(logging.INFO, logger="guessing_game")
    output = OutputRecorder()
    exit_code = run(
        input_fn=ScriptedInput(["50", answer]),
        output_fn=output,
        engine=GameEngine(FixedRandom([50])),
    )
    assert exit_code == 0
    assert output.lines[-1] == "再見！"
    assert "玩家離開（原因：n）" in _game_messages(caplog)


def test_unrecognised_answers_are_asked_again(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Other answers re-ask without starting a round or quitting."""
    caplog.set_level(logging.INFO, logger="guessing_game")
    answers = ScriptedInput(["50", "y", "abc", "n"])
    output = OutputRecorder()
    run(
        input_fn=answers,
        output_fn=output,
        engine=GameEngine(FixedRandom([50])),
    )
    assert output.lines.count(PLAY_AGAIN_RETRY) == 2
    assert answers.prompts[1:] == [PLAY_AGAIN_PROMPT] * 3
    assert _game_messages(caplog).count("新局開始") == 1


# --- Interrupts: Ctrl+C and end of input -----------------------------------


class InterruptingInput:
    """An input_fn that replays answers, then raises an exception."""

    def __init__(self, answers: list[str], error: BaseException) -> None:
        """Initializes the script.

        Args:
            answers: Answers returned before the exception is raised.
            error: The exception raised once the answers run out.
        """
        self._answers = list(answers)
        self._error = error

    def __call__(self, prompt: str) -> str:
        """Returns the next answer or raises the configured exception.

        Args:
            prompt: The prompt the game asked with (unused).

        Returns:
            The next scripted answer.

        Raises:
            BaseException: The configured error once answers are exhausted.
        """
        if not self._answers:
            raise self._error
        return self._answers.pop(0)


@pytest.mark.parametrize(
    ("error", "reason"),
    [
        (KeyboardInterrupt(), "Ctrl+C"),
        (EOFError(), "輸入結束"),
    ],
)
@pytest.mark.parametrize(
    "answers",
    [
        pytest.param([], id="while-guessing"),
        pytest.param(["50"], id="at-play-again-prompt"),
    ],
)
def test_interrupt_ends_game_gracefully(
    answers: list[str],
    error: BaseException,
    reason: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Ctrl+C and end of input leave cleanly in both phases (FR-014)."""
    caplog.set_level(logging.INFO, logger="guessing_game")
    output = OutputRecorder()
    exit_code = run(
        input_fn=InterruptingInput(answers, error),
        output_fn=output,
        engine=GameEngine(FixedRandom([50])),
    )
    assert exit_code == 0
    assert output.lines[-2:] == ["", "已離開遊戲，再見！"]
    assert f"玩家離開（原因：{reason}）" in _game_messages(caplog)


# --- Logging restrictions ---------------------------------------------------


def test_logs_only_the_three_event_kinds_and_never_leak_the_secret(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A full session logs only allowed INFO events, no secrets or guesses."""
    caplog.set_level(logging.INFO, logger="guessing_game")
    run(
        input_fn=ScriptedInput(
            ["abc", "0", "50", "80", "73", "", "61", "n"]
        ),
        output_fn=OutputRecorder(),
        engine=GameEngine(FixedRandom([73, 61])),
    )
    records = [r for r in caplog.records if r.name.startswith("guessing_game")]
    allowed = re.compile(
        r"新局開始|本局結束，總猜測次數：\d+|玩家離開（原因：.+）"
    )
    assert all(r.levelno == logging.INFO for r in records)
    assert all(allowed.fullmatch(r.getMessage()) for r in records)
    text = "\n".join(r.getMessage() for r in records)
    assert "73" not in text
    assert "61" not in text
    assert "abc" not in text
    messages = [r.getMessage() for r in records]
    assert messages.count("新局開始") == 2
    assert messages.count("本局結束，總猜測次數：3") == 1
    assert messages.count("本局結束，總猜測次數：1") == 1
    assert messages.count("玩家離開（原因：n）") == 1
