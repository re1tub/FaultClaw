"""Agent 3: verification judge.

Runs every test case from Agent 2 against a Python DUT simulation, compares
actual vs. expected outputs, and returns a structured report including
pass/fail counts, coverage percentage, and per-failure explanations.

DUT modes
---------
golden  — correct 4-bit adder: sum[4:0] = a + b
buggy   — carry-out hardwired to 0: sum[4:0] = (a + b) & 0x0F
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# DUT simulation models
# ---------------------------------------------------------------------------

def _golden_adder(a: int, b: int) -> dict[str, int]:
    return {"sum": a + b}


def _buggy_adder(a: int, b: int) -> dict[str, int]:
    """Buggy adder: carry-out (sum[4]) is hardwired to 0."""
    return {"sum": (a + b) & 0x0F}


def _run_dut(inputs: dict[str, int], buggy: bool) -> dict[str, int]:
    a = inputs["a"]
    b = inputs["b"]
    return _buggy_adder(a, b) if buggy else _golden_adder(a, b)

# ---------------------------------------------------------------------------
# Failure diagnosis
# ---------------------------------------------------------------------------

def _explain(inputs: dict[str, int], expected: dict[str, Any], actual: dict[str, Any]) -> str:
    a, b = inputs["a"], inputs["b"]
    raw = a + b
    parts: list[str] = []

    for sig, exp_val in expected.items():
        act_val = actual.get(sig)
        if act_val == exp_val:
            continue
        parts.append(f"{sig}: expected {exp_val}, got {act_val}")
        if sig == "sum" and act_val == (raw & 0x0F) and exp_val == raw:
            carry = (raw >> 4) & 1
            parts.append(
                f"carry-out bit missing — sum[4] should be {carry} "
                f"({a}+{b}={raw} overflows 4 bits)"
            )

    return "; ".join(parts) if parts else "output mismatch"


# ---------------------------------------------------------------------------
# Core verification logic
# ---------------------------------------------------------------------------

def run_verification(
    suite: dict[str, Any],
    buggy: bool = False,
) -> dict[str, Any]:
    """Run *suite* against the DUT and return a full verification report."""
    tests: list[dict[str, Any]] = suite.get("tests", [])
    results: list[dict[str, Any]] = []
    failed_tests: list[dict[str, Any]] = []
    passed = 0

    for test in tests:
        inputs: dict[str, int] = test["inputs"]
        expected: dict[str, Any] = test["expected"]
        actual = _run_dut(inputs, buggy=buggy)
        ok = actual == expected

        result: dict[str, Any] = {
            "id": test["id"],
            "category": test["category"],
            "inputs": inputs,
            "expected": expected,
            "actual": actual,
            "passed": ok,
            "rationale": test.get("rationale", ""),
        }
        if ok:
            passed += 1
        else:
            result["failure_explanation"] = _explain(inputs, expected, actual)
            failed_tests.append(result)

        results.append(result)

    total = len(tests)
    failed = total - passed
    coverage_pct = round(passed / total * 100, 1) if total else 0.0

    return {
        "design_name": suite.get("design_name", ""),
        "mode": suite.get("mode", ""),
        "dut": "buggy_adder" if buggy else "golden_adder",
        "total_tests": total,
        "tests_passed": passed,
        "tests_failed": failed,
        "coverage_pct": coverage_pct,
        "failed_tests": failed_tests,
        "results": results,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="FaultClaw Agent 3 — run a test suite against the DUT and report results."
    )
    parser.add_argument(
        "--suite",
        required=True,
        help="Path to the Agent 2 test suite JSON.",
    )
    parser.add_argument(
        "--buggy",
        action="store_true",
        help="Simulate the buggy adder DUT (carry-out hardwired to 0).",
    )
    parser.add_argument(
        "--output",
        help="Write the verification report JSON to this path instead of stdout.",
    )
    args = parser.parse_args()

    suite_path = Path(args.suite)
    if not suite_path.exists():
        print(f"error: file not found: {suite_path}", file=sys.stderr)
        return 1

    suite = json.loads(suite_path.read_text(encoding="utf-8"))
    report = run_verification(suite, buggy=args.buggy)
    serialized = json.dumps(report, indent=2)

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(serialized + "\n", encoding="utf-8")
    else:
        print(serialized)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
