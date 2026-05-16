"""Orchestration entrypoint for the FaultClaw pipeline.

Stage 1 — Agent 1 (spec_reader):        parse hardware design spec → DesignSpec dict
Stage 2 — Agent 2 (test_generator):     generate adversarial test suite
Stage 3 — Agent 3 (verification_judge): run suite against DUT, produce pass/fail report
Stage 4 — memory.store:                 persist results to memory/history.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from agents.spec_reader import SpecParseError, parse_spec
from agents.test_generator import DesignSpec, generate_test_suite
from agents.verification_judge import run_verification
from memory.store import save_run


def load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="FaultClaw pipeline: Agent 1 (spec_reader) → Agent 2 (test_generator)."
    )
    parser.add_argument(
        "--design-spec",
        required=True,
        help="Path to the hardware design spec (.v, .sv, .yaml, .yml, or .json).",
    )
    parser.add_argument(
        "--format",
        choices=["json", "yaml", "verilog"],
        help="Force Agent 1 parser (auto-detected from file extension by default).",
    )
    parser.add_argument("--feedback", help="Optional Agent 3 failure-feedback JSON.")
    parser.add_argument("--breakdown", action="store_true", help="Enable Breakdown Mode.")
    parser.add_argument("--buggy", action="store_true", help="Simulate the buggy adder DUT in Agent 3.")
    parser.add_argument("--output", help="Optional output file path for the verification report.")
    args = parser.parse_args()

    # --- Agent 1: parse the raw design spec ---
    try:
        spec_dict = parse_spec(Path(args.design_spec), force_format=args.format)
    except FileNotFoundError:
        print(f"error (Agent 1): file not found: {args.design_spec}", file=sys.stderr)
        return 1
    except SpecParseError as exc:
        print(f"error (Agent 1): {exc}", file=sys.stderr)
        return 1

    # --- Agent 2: generate the test suite ---
    spec = DesignSpec.from_dict(spec_dict)
    feedback = load_json(args.feedback) if args.feedback else None
    suite = generate_test_suite(spec, breakdown=args.breakdown, feedback=feedback)

    # --- Agent 3: run suite against DUT, produce verification report ---
    report = run_verification(suite, buggy=args.buggy)

    # --- memory.store: persist real pass/fail counts from Agent 3 ---
    save_run(
        design_name=report["design_name"],
        mode=report["mode"],
        total_tests=report["total_tests"],
        tests_passed=report["tests_passed"],
        tests_failed=report["tests_failed"],
        failed_tests=report["failed_tests"],
    )

    serialized = json.dumps(report, indent=2)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(serialized + "\n", encoding="utf-8")
    else:
        print(serialized)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
