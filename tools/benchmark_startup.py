from __future__ import annotations

import argparse
import csv
import json
import statistics
import subprocess
import time
from pathlib import Path


def run_once(executable: Path) -> float:
    start = time.perf_counter()
    completed = subprocess.run(
        [str(executable), "--smoke-startup"],
        capture_output=True,
        text=True,
        check=False,
    )
    elapsed_ms = (time.perf_counter() - start) * 1000.0

    if completed.returncode != 0:
        raise RuntimeError(
            f"{executable} exited with code {completed.returncode}. stderr: {completed.stderr.strip()}"
        )
    return elapsed_ms


def benchmark(executable: Path, runs: int) -> dict[str, float | str | int]:
    samples = [run_once(executable) for _ in range(runs)]
    return {
        "executable": str(executable),
        "runs": runs,
        "mean_ms": round(statistics.mean(samples), 2),
        "median_ms": round(statistics.median(samples), 2),
        "min_ms": round(min(samples), 2),
        "max_ms": round(max(samples), 2),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("executable", type=Path)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--csv", dest="csv_path", type=Path, default=None)
    parser.add_argument("--json", dest="json_path", type=Path, default=None)
    args = parser.parse_args()

    result = benchmark(args.executable, args.runs)
    print(json.dumps(result, ensure_ascii=True))

    if args.csv_path is not None:
        args.csv_path.parent.mkdir(parents=True, exist_ok=True)
        file_exists = args.csv_path.exists()
        with args.csv_path.open("a", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(
                fh,
                fieldnames=[
                    "executable",
                    "runs",
                    "mean_ms",
                    "median_ms",
                    "min_ms",
                    "max_ms",
                ],
            )
            if not file_exists:
                writer.writeheader()
            writer.writerow(result)

    if args.json_path is not None:
        args.json_path.parent.mkdir(parents=True, exist_ok=True)
        args.json_path.write_text(
            json.dumps(result, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

