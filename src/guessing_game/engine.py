"""Pure game logic for the number guessing game.

This module MUST NOT perform any I/O, use logging, or import the CLI layer.
"""

import enum
import random


class GuessResult(enum.Enum):
    """Outcome of a valid guess compared with the secret number."""

    TOO_HIGH = "too_high"
    TOO_LOW = "too_low"
    CORRECT = "correct"


class GameEngine:
    """State and rules of a single round of the guessing game.

    The random source is injected so tests can reproduce a round. The secret
    number is private and never exposed.

    Attributes:
        MIN_NUMBER: Smallest possible secret number (inclusive).
        MAX_NUMBER: Largest possible secret number (inclusive).
    """

    MIN_NUMBER = 1
    MAX_NUMBER = 100

    def __init__(self, rng: random.Random | None = None) -> None:
        """Creates an engine and starts the first round.

        Args:
            rng: Source of randomness. A new random.Random() is used when
                omitted.
        """
        self._rng = rng if rng is not None else random.Random()
        self._secret = self.MIN_NUMBER
        self._attempts = 0
        self._finished = False
        self.start_new_round()

    def start_new_round(self) -> None:
        """Draws a new secret number and resets the round state."""
        self._secret = self._rng.randint(self.MIN_NUMBER, self.MAX_NUMBER)
        self._attempts = 0
        self._finished = False

    @property
    def attempts(self) -> int:
        """The number of valid guesses made in the current round."""
        return self._attempts

    @property
    def is_finished(self) -> bool:
        """Whether the current round has been won."""
        return self._finished

    def is_valid_guess(self, value: int) -> bool:
        """Checks whether a value lies within the allowed range.

        Args:
            value: The number to check.

        Returns:
            True if MIN_NUMBER <= value <= MAX_NUMBER.
        """
        return self.MIN_NUMBER <= value <= self.MAX_NUMBER

    def guess(self, value: int) -> GuessResult:
        """Evaluates a guess against the secret number.

        Every call that returns counts as one valid attempt. A call that
        raises leaves the round state unchanged.

        Args:
            value: The guessed number.

        Returns:
            TOO_HIGH, TOO_LOW, or CORRECT (which also ends the round).

        Raises:
            ValueError: If the value is outside the allowed range.
            RuntimeError: If the round has already been won.
        """
        if not self.is_valid_guess(value):
            raise ValueError(
                f"Guess must be between {self.MIN_NUMBER} and "
                f"{self.MAX_NUMBER}."
            )
        if self._finished:
            raise RuntimeError("The round is already finished.")
        self._attempts += 1
        if value > self._secret:
            return GuessResult.TOO_HIGH
        if value < self._secret:
            return GuessResult.TOO_LOW
        self._finished = True
        return GuessResult.CORRECT
