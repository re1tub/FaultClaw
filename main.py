"""Minimal orchestration entrypoint for the P1 slice of FaultClaw."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agents.test_generator import DesignSpec, generate_test_suite


def load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="FaultClaw pipeline entrypoint.")
    parser.add_argument("--design-spec", required=True, help="Path to Agent 1 output JSON.")
    parser.add_argument("--feedback", help="Optional Agent 3 feedback JSON.")
    parser.add_argument("--breakdown", action="store_true", help="Enable Breakdown Mode.")
    parser.add_argument("--output", help="Optional output file path for the generated suite.")
    args = parser.parse_args()

    spec = DesignSpec.from_dict(load_json(args.design_spec))
    feedback = load_json(args.feedback) if args.feedback else None
    suite = generate_test_suite(spec, breakdown=args.breakdown, feedback=feedback)
    serialized = json.dumps(suite, indent=2)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(serialized + "\n", encoding="utf-8")
    else:
        print(serialized)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
