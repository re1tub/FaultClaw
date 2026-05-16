"""Persistent run history for FaultClaw.

Reads from and appends to memory/history.json. Each entry records one
pipeline run: design name, timestamp, test counts, and any failed test cases
reported by Agent 3.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_STORE_PATH = Path(__file__).parent / "history.json"


# ---------------------------------------------------------------------------
# Internal I/O helpers
# ---------------------------------------------------------------------------

def _load(store_path: Path) -> list[dict[str, Any]]:
    if not store_path.exists():
        return []
    try:
        return json.loads(store_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def _write(records: list[dict[str, Any]], store_path: Path) -> None:
    store_path.parent.mkdir(parents=True, exist_ok=True)
    store_path.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def save_run(
    design_name: str,
    mode: str,
    total_tests: int,
    tests_passed: int = 0,
    tests_failed: int = 0,
    failed_tests: list[dict[str, Any]] | None = None,
    store_path: Path = DEFAULT_STORE_PATH,
) -> dict[str, Any]:
    """Append one run record to the history store and return it.

    tests_passed / tests_failed default to 0 until Agent 3 is wired in.
    failed_tests is the list of test-case dicts (same shape as Agent 2 output)
    that Agent 3 reports as mismatches.
    """
    record: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "design_name": design_name,
        "mode": mode,
        "total_tests": total_tests,
        "tests_passed": tests_passed,
        "tests_failed": tests_failed,
        "failed_tests": failed_tests or [],
    }
    records = _load(store_path)
    records.append(record)
    _write(records, store_path)
    return record


def load_history(
    design_name: str | None = None,
    store_path: Path = DEFAULT_STORE_PATH,
) -> list[dict[str, Any]]:
    """Return all run records, optionally filtered to a single design."""
    records = _load(store_path)
    if design_name is None:
        return records
    return [r for r in records if r.get("design_name") == design_name]


def failure_patterns(
    design_name: str | None = None,
    store_path: Path = DEFAULT_STORE_PATH,
) -> list[dict[str, Any]]:
    """Return every unique failed test case across history, deduplicated by inputs.

    Useful for seeding future Agent 2 runs with known-bad input regions.
    """
    seen: set[str] = set()
    patterns: list[dict[str, Any]] = []
    for record in load_history(design_name=design_name, store_path=store_path):
        for test in record.get("failed_tests", []):
            key = json.dumps(test.get("inputs", {}), sort_keys=True)
            if key not in seen:
                seen.add(key)
                patterns.append(test)
    return patterns
