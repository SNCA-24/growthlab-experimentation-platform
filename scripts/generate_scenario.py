#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from simulator.scenario_runner.run import run_scenario  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a GrowthLab synthetic scenario")
    parser.add_argument("--scenario", required=True, help="Path to a scenario YAML file")
    parser.add_argument("--output-dir", required=True, help="Directory to write parquet outputs into")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run_scenario(args.scenario, args.output_dir)
    counts = {name: len(frame) for name, frame in result.tables.items()}
    summary = " ".join(f"{table}={rows}" for table, rows in counts.items())
    print(f"{result.scenario.scenario_id} {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

