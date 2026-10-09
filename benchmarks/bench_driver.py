"""Benchmark workload: plays one full round of the guessing game via its CLI.

Uses a fixed seed so the secret number and the binary-search guess sequence
are identical on every run, making the workload deterministic and
reproducible across CI executions. See specs/003-ci-test-quality-perf/
research.md D5 for the design rationale.
"""

import random
import sys
from pathlib import Path

# The project has no installed package / PYTHONPATH of its own outside of
# pytest's `pythonpath = ["src"]` config, so a plain `python
# benchmarks/bench_driver.py` subprocess needs this to find `guessing_game`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from guessing_game.cli import run  # noqa: E402
from guessing_game.engine import GameEngine, GuessResult  # noqa: E402

SEED = 20261009


def _compute_guess_sequence(seed: int) -> list[int]:
    """Replays a binary search against a throwaway engine to get fixed guesses.

    Args:
        seed: Seed for the engine's random source; determines the secret
            number that the real run (built with the same seed) will have.

    Returns:
        The ordered list of guesses a binary search makes against that
        secret number, in the order they must be submitted to win.
    """
    shadow_engine = GameEngine(rng=random.Random(seed))
    low, high = GameEngine.MIN_NUMBER, GameEngine.MAX_NUMBER
    guesses: list[int] = []
    while not shadow_engine.is_finished:
        mid = (low + high) // 2
        guesses.append(mid)
        result = shadow_engine.guess(mid)
        if result is GuessResult.TOO_HIGH:
            high = mid - 1
        elif result is GuessResult.TOO_LOW:
            low = mid + 1
    return guesses


def main() -> int:
    """Plays one full round through the existing CLI interface and exits.

    The guess sequence is precomputed before `run` is ever called, so the
    `input_fn` passed to it never needs to inspect `output_fn`'s messages.

    Returns:
        The process exit code from `guessing_game.cli.run`.
    """
    guesses = _compute_guess_sequence(SEED)
    responses = iter([str(guess) for guess in guesses] + ["n"])
    engine = GameEngine(rng=random.Random(SEED))
    return run(
        input_fn=lambda _prompt: next(responses),
        output_fn=lambda _message: None,
        engine=engine,
    )


if __name__ == "__main__":
    sys.exit(main())
