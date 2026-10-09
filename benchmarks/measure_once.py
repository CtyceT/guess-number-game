"""Runs bench_driver.py once and reports its resource usage as one JSON line.

Each invocation of this module is its own fresh process with exactly one
child (bench_driver.py), so `resource.getrusage(RUSAGE_CHILDREN)` reports
that one child's own peak RSS and CPU time rather than a stale high-water
mark inherited from earlier runs. See specs/003-ci-test-quality-perf/
research.md D6 and contracts/benchmark-ipc.md for the design rationale and
the JSON schema produced here.
"""

import json
import resource
import subprocess
import sys
import time
from typing import TypedDict

_DRIVER_PATH = "benchmarks/bench_driver.py"


class MeasurementResult(TypedDict):
    """One run's measured metrics, matching contracts/benchmark-ipc.md."""

    response_time_s: float | None
    cpu_time_s: float | None
    max_rss_kb: int | None
    ok: bool
    error: str | None


def _run_once() -> MeasurementResult:
    """Runs bench_driver.py as the sole child process and measures it.

    Returns:
        The metrics for this one run, or an `ok: False` result with an
        error message if bench_driver.py exited with a non-zero status.
    """
    start = time.perf_counter()
    result = subprocess.run(
        [sys.executable, _DRIVER_PATH],
        capture_output=True,
        text=True,
        check=False,
    )
    response_time_s = time.perf_counter() - start

    if result.returncode != 0:
        return MeasurementResult(
            response_time_s=None,
            cpu_time_s=None,
            max_rss_kb=None,
            ok=False,
            error=f"bench_driver exited with code {result.returncode}",
        )

    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    return MeasurementResult(
        response_time_s=response_time_s,
        cpu_time_s=usage.ru_utime + usage.ru_stime,
        max_rss_kb=usage.ru_maxrss,
        ok=True,
        error=None,
    )


def main() -> int:
    """Prints one JSON line with this run's metrics and always exits 0.

    A failed child run is reported inside the JSON payload (`ok: False`
    plus `error`), never by propagating a non-zero exit code from this
    process itself.

    Returns:
        Always 0.
    """
    print(json.dumps(_run_once()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
