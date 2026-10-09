"""Runs the guessing-game performance benchmark: samples, averages, a report.

Calls measure_once.py as a fresh subprocess once per sample (see
specs/003-ci-test-quality-perf/research.md D6 for why), averages the
successful samples, writes the result to benchmark_summary.md, and emits a
`##vso[task.uploadsummary]` logging command so Azure Pipelines shows it in
the run's Extensions/summary tab. Always exits 0: performance numbers carry
no pass/fail threshold (FR-010/FR-015), and the pipeline step that invokes
this script additionally sets `continueOnError: true` as an independent
safety net.
"""

import json
import statistics
import subprocess
import sys
from pathlib import Path
from typing import TypedDict

_MEASURE_ONCE_PATH = "benchmarks/measure_once.py"
_SAMPLE_COUNT = 10
_SUMMARY_PATH = Path("benchmark_summary.md")


class Sample(TypedDict):
    """One benchmark sample: a MeasurementResult tagged with its run index."""

    run_index: int
    response_time_s: float | None
    cpu_time_s: float | None
    max_rss_kb: int | None
    ok: bool
    error: str | None


def _collect_sample(run_index: int) -> Sample:
    """Runs measure_once.py once and returns its sample, tagged with its index.

    Any failure to launch measure_once.py or to parse its output is itself
    reported as a failed sample (never raised), so the remaining samples
    can still be collected.

    Args:
        run_index: 1-based index of this sample among the `_SAMPLE_COUNT`
            runs.

    Returns:
        The sample for this run, always including `run_index`.
    """
    try:
        result = subprocess.run(
            [sys.executable, _MEASURE_ONCE_PATH],
            capture_output=True,
            text=True,
            check=False,
        )
        payload = json.loads(result.stdout.strip().splitlines()[-1])
    except (OSError, ValueError, IndexError) as error:
        payload = {
            "response_time_s": None,
            "cpu_time_s": None,
            "max_rss_kb": None,
            "ok": False,
            "error": f"measure_once.py failed to run or produce valid JSON: {error}",
        }
    return Sample(run_index=run_index, **payload)


def _average(samples: list[Sample], key: str) -> float | None:
    """Averages one numeric field over the samples that succeeded.

    Args:
        samples: All collected samples (successful and failed).
        key: The field name to average: `response_time_s`, `cpu_time_s`, or
            `max_rss_kb`.

    Returns:
        The mean of that field over samples where `ok` is `True`, or
        `None` if every sample failed (never 0, which would read as a
        good result).
    """
    values = [sample[key] for sample in samples if sample["ok"]]
    if not values:
        return None
    return statistics.fmean(values)


def _format_summary(samples: list[Sample]) -> str:
    """Renders the samples and their averages as a Markdown report.

    Args:
        samples: All `_SAMPLE_COUNT` collected samples, in run order.

    Returns:
        The full Markdown text to write to `benchmark_summary.md`.
    """
    ok_count = sum(1 for sample in samples if sample["ok"])
    avg_response = _average(samples, "response_time_s")
    avg_cpu = _average(samples, "cpu_time_s")
    avg_rss = _average(samples, "max_rss_kb")

    lines = [
        "# 猜數字遊戲效能量測摘要",
        "",
        f"- 樣本數：{len(samples)}（成功：{ok_count}）",
        f"- 平均回應時間（秒）：{avg_response if avg_response is not None else 'N/A'}",
        f"- 平均 CPU 時間（秒）：{avg_cpu if avg_cpu is not None else 'N/A'}",
        f"- 平均記憶體峰值（KB）：{avg_rss if avg_rss is not None else 'N/A'}",
        "",
        "| run_index | ok | response_time_s | cpu_time_s | max_rss_kb | error |",
        "|---|---|---|---|---|---|",
    ]
    for sample in samples:
        lines.append(
            f"| {sample['run_index']} | {sample['ok']} | "
            f"{sample['response_time_s']} | {sample['cpu_time_s']} | "
            f"{sample['max_rss_kb']} | {sample['error']} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    """Collects samples, writes the summary, and signals Azure Pipelines.

    Always exits 0 regardless of how many samples failed.

    Returns:
        Always 0.
    """
    samples = [_collect_sample(run_index) for run_index in range(1, _SAMPLE_COUNT + 1)]
    _SUMMARY_PATH.write_text(_format_summary(samples), encoding="utf-8")
    print(f"##vso[task.uploadsummary]{_SUMMARY_PATH.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
