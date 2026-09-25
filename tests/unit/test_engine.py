"""Unit tests for guessing_game.engine.GameEngine.

None of these tests touch real terminal input or output.
"""

import random

import pytest

from guessing_game.engine import GameEngine, GuessResult


class RecordingRandom(random.Random):
    """A Random whose randint returns scripted values and records its calls."""

    def __init__(self, values: list[int]) -> None:
        """Initializes the fake.

        Args:
            values: Values returned by successive randint calls. The last
                value is repeated once the list is exhausted.
        """
        super().__init__()
        self._values = list(values)
        self._next = 0
        self.calls: list[tuple[int, int]] = []

    def randint(self, a: int, b: int) -> int:
        """Records the call and returns the next scripted value.

        Args:
            a: Lower bound requested by the caller.
            b: Upper bound requested by the caller.

        Returns:
            The next scripted value.
        """
        self.calls.append((a, b))
        index = min(self._next, len(self._values) - 1)
        self._next += 1
        return self._values[index]


def test_range_constants() -> None:
    """The secret number range is fixed at 1 to 100."""
    assert GameEngine.MIN_NUMBER == 1
    assert GameEngine.MAX_NUMBER == 100


def test_constructor_draws_secret_from_full_range_once() -> None:
    """Building an engine starts a round with exactly one randint(1, 100)."""
    rng = RecordingRandom([50])
    GameEngine(rng)
    assert rng.calls == [(1, 100)]


def test_initial_state() -> None:
    """A fresh round has no attempts and is not finished."""
    engine = GameEngine(RecordingRandom([50]))
    assert engine.attempts == 0
    assert engine.is_finished is False


def test_start_new_round_draws_again_and_resets_state() -> None:
    """start_new_round draws a new secret and resets the round state."""
    rng = RecordingRandom([50, 60])
    engine = GameEngine(rng)
    engine.start_new_round()
    assert rng.calls == [(1, 100), (1, 100)]
    assert engine.attempts == 0
    assert engine.is_finished is False


def test_engine_can_be_built_without_injected_rng() -> None:
    """Omitting rng falls back to a default random source."""
    engine = GameEngine()
    assert engine.attempts == 0
    assert engine.is_finished is False


def test_secret_number_is_not_publicly_exposed() -> None:
    """No public attribute reveals the secret number (FR-002)."""
    engine = GameEngine(RecordingRandom([73]))
    public = [name for name in dir(engine) if not name.startswith("_")]
    for name in public:
        value = getattr(engine, name)
        if isinstance(value, int) and not isinstance(value, bool):
            assert value != 73, f"public attribute {name} exposes the secret"


# --- User Story 2: guessing and hints --------------------------------------


def _solve_by_bisection(engine: GameEngine) -> tuple[int, int]:
    """Plays a round to the end with a binary-search strategy.

    Args:
        engine: A freshly started engine.

    Returns:
        A tuple of the discovered secret number and the number of valid
        guesses used.
    """
    low, high = GameEngine.MIN_NUMBER, GameEngine.MAX_NUMBER
    while True:
        assert low <= high, "binary search left the valid range"
        middle = (low + high) // 2
        result = engine.guess(middle)
        if result is GuessResult.CORRECT:
            return middle, engine.attempts
        if result is GuessResult.TOO_HIGH:
            high = middle - 1
        else:
            low = middle + 1


def test_guess_reports_too_high() -> None:
    """A guess above the secret is TOO_HIGH and the round continues."""
    engine = GameEngine(RecordingRandom([50]))
    assert engine.guess(70) is GuessResult.TOO_HIGH
    assert engine.is_finished is False


def test_guess_reports_too_low() -> None:
    """A guess below the secret is TOO_LOW and the round continues."""
    engine = GameEngine(RecordingRandom([50]))
    assert engine.guess(30) is GuessResult.TOO_LOW
    assert engine.is_finished is False


def test_guess_reports_correct_and_finishes_round() -> None:
    """A guess equal to the secret is CORRECT and ends the round."""
    engine = GameEngine(RecordingRandom([50]))
    assert engine.guess(50) is GuessResult.CORRECT
    assert engine.is_finished is True


def test_each_valid_guess_increments_attempts() -> None:
    """Every valid guess, including a repeated one, counts as an attempt."""
    engine = GameEngine(RecordingRandom([50]))
    engine.guess(70)
    engine.guess(70)
    engine.guess(30)
    assert engine.attempts == 3
    engine.guess(50)
    assert engine.attempts == 4


def test_guess_after_round_finished_raises_and_keeps_state() -> None:
    """Guessing after the round is won raises RuntimeError, state unchanged."""
    engine = GameEngine(RecordingRandom([50]))
    engine.guess(50)
    with pytest.raises(RuntimeError):
        engine.guess(10)
    assert engine.attempts == 1
    assert engine.is_finished is True


def test_start_new_round_after_win_resets_state() -> None:
    """A new round after a win has no attempts and is playable again."""
    engine = GameEngine(RecordingRandom([50, 20]))
    engine.guess(50)
    engine.start_new_round()
    assert engine.attempts == 0
    assert engine.is_finished is False
    assert engine.guess(20) is GuessResult.CORRECT


def test_seeded_secrets_always_fall_in_range_and_vary() -> None:
    """100 seeded rounds have in-range, varying secrets (SC-002)."""
    secrets = set()
    for seed in range(100):
        engine = GameEngine(random.Random(seed))
        secret, _ = _solve_by_bisection(engine)
        assert GameEngine.MIN_NUMBER <= secret <= GameEngine.MAX_NUMBER
        secrets.add(secret)
    assert len(secrets) > 1


def test_same_seed_reproduces_the_same_round() -> None:
    """Two engines built from the same seed have the same secret."""
    first, _ = _solve_by_bisection(GameEngine(random.Random(12345)))
    second, _ = _solve_by_bisection(GameEngine(random.Random(12345)))
    assert first == second


def test_every_secret_is_found_within_seven_guesses() -> None:
    """Binary search wins within 7 valid guesses for any secret (SC-006)."""
    for secret in range(GameEngine.MIN_NUMBER, GameEngine.MAX_NUMBER + 1):
        engine = GameEngine(RecordingRandom([secret]))
        found, guesses = _solve_by_bisection(engine)
        assert found == secret
        assert guesses <= 7, f"secret {secret} needed {guesses} guesses"


# --- User Story 3: range validation ----------------------------------------


@pytest.mark.parametrize("value", [1, 50, 100])
def test_is_valid_guess_accepts_values_in_range(value: int) -> None:
    """Values from 1 to 100 inclusive are valid guesses."""
    engine = GameEngine(RecordingRandom([50]))
    assert engine.is_valid_guess(value) is True


@pytest.mark.parametrize("value", [0, 101, -5, 10**18, -(10**18)])
def test_is_valid_guess_rejects_values_out_of_range(value: int) -> None:
    """Values outside 1..100 are not valid guesses."""
    engine = GameEngine(RecordingRandom([50]))
    assert engine.is_valid_guess(value) is False


@pytest.mark.parametrize("value", [0, 101, -5])
def test_guess_out_of_range_raises_and_keeps_state(value: int) -> None:
    """An out-of-range guess raises ValueError and changes nothing."""
    engine = GameEngine(RecordingRandom([50]))
    engine.guess(70)
    with pytest.raises(ValueError):
        engine.guess(value)
    assert engine.attempts == 1
    assert engine.is_finished is False


def test_boundary_values_are_valid_guesses() -> None:
    """1 and 100 are accepted and counted as attempts."""
    engine = GameEngine(RecordingRandom([50]))
    assert engine.guess(1) is GuessResult.TOO_LOW
    assert engine.guess(100) is GuessResult.TOO_HIGH
    assert engine.attempts == 2


def test_out_of_range_guess_after_finish_raises_value_error() -> None:
    """The range is checked first, so a finished round gives ValueError."""
    engine = GameEngine(RecordingRandom([50]))
    engine.guess(50)
    with pytest.raises(ValueError):
        engine.guess(0)
    assert engine.attempts == 1
    assert engine.is_finished is True
