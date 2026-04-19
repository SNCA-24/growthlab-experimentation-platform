#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from validation.harness.reporting import write_validation_reports  # noqa: E402
from validation.harness.run_pack import run_validation_pack  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a GrowthLab validation pack across one or more scenarios")
    parser.add_argument("targets", nargs="+", help="Scenario YAML files or scenario directories")
    parser.add_argument(
        "--output-dir",
        default=str(ROOT / "reports" / "validation"),
        help="Directory to write validation reports into",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    pack = run_validation_pack(args.targets, output_dir=args.output_dir)
    write_validation_reports(pack)
    for scenario in pack.scenarios:
        print(
            f"{scenario.scenario.scenario_id} trust={scenario.trust.overall_state.value} "
            f"srm={scenario.trust.srm.state.value} recommendation={scenario.recommendation_proxy or 'not_evaluated'}"
        )
    print(f"overall={pack.overall_state.value} output_dir={args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

