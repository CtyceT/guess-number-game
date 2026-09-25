"""Terminal I/O layer for the number guessing game."""

import enum
import logging
import re
import sys
from collections.abc import Callable

from guessing_game.engine import GameEngine, GuessResult

_LOGGER = logging.getLogger(__name__)
_PACKAGE_LOGGER_NAME = "guessing_game"
_GUESS_PROMPT = "請輸入猜測（1-100）："
_FORMAT_ERROR = "輸入無效：請輸入 1 到 100 的整數。"
_RANGE_ERROR = "輸入無效：數字必須介於 1 到 100 之間。"
_PLAY_AGAIN_PROMPT = "再玩一局？按 Enter 再玩，輸入 n 離開："
_PLAY_AGAIN_RETRY = "請按 Enter 再玩，或輸入 n 離開。"

_INTEGER_PATTERN = re.compile(r"-?(0|[1-9][0-9]*)")
_MAX_DIGITS = 18
_OVERFLOW_VALUE = 10**_MAX_DIGITS


class PlayAgainChoice(enum.Enum):
    """Player's answer to the "play again?" question."""

    REPLAY = "replay"
    QUIT = "quit"
    UNKNOWN = "unknown"


def parse_guess(raw: str) -> int | None:
    """Parses the text a player typed as a guess.

    Only plain integer literals are accepted: ASCII digits without a leading
    plus sign or leading zeros, optionally preceded by a minus sign. Range
    checking (1 to 100) is not done here; it belongs to the game engine.

    Args:
        raw: The raw text entered by the player.

    Returns:
        The integer value, or None if the format is invalid. Digit strings
        longer than 18 digits are not converted and yield plus or minus
        10**18, which is always out of range.
    """
    text = raw.strip()
    if _INTEGER_PATTERN.fullmatch(text) is None:
        return None
    digits = text.lstrip("-")
    if len(digits) > _MAX_DIGITS:
        return -_OVERFLOW_VALUE if text.startswith("-") else _OVERFLOW_VALUE
    return int(text)


def parse_play_again(raw: str) -> PlayAgainChoice:
    """Interprets the answer to the "play again?" question.

    Args:
        raw: The raw text entered by the player.

    Returns:
        REPLAY for blank input, QUIT for "n" or "N" (surrounding whitespace
        ignored), and UNKNOWN for anything else.
    """
    text = raw.strip()
    if not text:
        return PlayAgainChoice.REPLAY
    if text.lower() == "n":
        return PlayAgainChoice.QUIT
    return PlayAgainChoice.UNKNOWN


def configure_logging() -> None:
    """Configures the package logger: INFO level, written to stdout.

    Only the application entry point should call this. Calling it more than
    once does not duplicate handlers.
    """
    logger = logging.getLogger(_PACKAGE_LOGGER_NAME)
    logger.setLevel(logging.INFO)
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    logger.addHandler(handler)


def _play_round(
    game: GameEngine,
    input_fn: Callable[[str], str],
    output_fn: Callable[[str], None],
) -> None:
    """Prompts for guesses until the current round is won.

    Args:
        game: The engine holding the current round.
        input_fn: Reads one line of player input, given a prompt string.
        output_fn: Displays one message to the player.
    """
    while not game.is_finished:
        guess = parse_guess(input_fn(_GUESS_PROMPT))
        if guess is None:
            output_fn(_FORMAT_ERROR)
            continue
        if not game.is_valid_guess(guess):
            output_fn(_RANGE_ERROR)
            continue
        result = game.guess(guess)
        if result is GuessResult.TOO_HIGH:
            output_fn("太大")
        elif result is GuessResult.TOO_LOW:
            output_fn("太小")
        else:
            output_fn(f"答對！你總共猜了 {game.attempts} 次。")


def _wants_to_play_again(
    input_fn: Callable[[str], str],
    output_fn: Callable[[str], None],
) -> bool:
    """Asks whether to play another round, repeating until understood.

    Args:
        input_fn: Reads one line of player input, given a prompt string.
        output_fn: Displays one message to the player.

    Returns:
        True to play again, False to quit.
    """
    while True:
        choice = parse_play_again(input_fn(_PLAY_AGAIN_PROMPT))
        if choice is PlayAgainChoice.REPLAY:
            return True
        if choice is PlayAgainChoice.QUIT:
            return False
        output_fn(_PLAY_AGAIN_RETRY)


def run(
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
    engine: GameEngine | None = None,
) -> int:
    """Runs the game until the player leaves.

    Args:
        input_fn: Reads one line of player input, given a prompt string.
        output_fn: Displays one message to the player.
        engine: The game engine to use. A new one is created when omitted.

    Returns:
        The process exit code.
    """
    game = engine if engine is not None else GameEngine()
    try:
        _LOGGER.info("新局開始")
        while True:
            _play_round(game, input_fn, output_fn)
            _LOGGER.info("本局結束，總猜測次數：%d", game.attempts)
            if not _wants_to_play_again(input_fn, output_fn):
                output_fn("再見！")
                _LOGGER.info("玩家離開（原因：n）")
                return 0
            game.start_new_round()
            _LOGGER.info("新局開始")
    except (KeyboardInterrupt, EOFError) as error:
        reason = "Ctrl+C" if isinstance(error, KeyboardInterrupt) else "輸入結束"
        output_fn("")
        output_fn("已離開遊戲，再見！")
        _LOGGER.info("玩家離開（原因：%s）", reason)
        return 0


def main() -> int:
    """Application entry point.

    Returns:
        The process exit code.
    """
    configure_logging()
    return run()
