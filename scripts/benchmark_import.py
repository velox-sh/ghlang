#!/usr/bin/env python3
import subprocess
import sys
import time


def measure(label: str, code: str, runs: int = 5) -> float:
    """Measure the average time to execute the given code snippet over a number of runs"""
    times = []

    for _ in range(runs):
        start = time.perf_counter()

        subprocess.run(
            [sys.executable, "-c", code],
            check=True,
            capture_output=True,
        )

        times.append(time.perf_counter() - start)

    avg = sum(times) / len(times)
    print(f"  {label}: {avg * 1000:.0f}ms avg ({runs} runs)")

    return avg


print("Import benchmarks\n")

cli = measure(
    "ghlang.cli (autocomplete path)",
    "from ghlang.cli.utils import themes_autocomplete, format_autocomplete",
)
viz = measure(
    "ghlang.visualizers (heavy path)",
    "from ghlang.visualizers import generate_pie",
)

ratio = viz / cli
print(f"\n  Visualizers are {ratio:.1f}x slower to import than the autocomplete path")
