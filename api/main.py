"""FaultClaw REST API.

Endpoints
---------
POST /verify           — full pipeline on adder_4bit.v (normal mode)
POST /verify/buggy     — full pipeline with buggy DUT (carry-out hardwired to 0)
POST /verify/breakdown — full pipeline in Breakdown Mode (256 tests)
GET  /history          — return all run records from memory/history.json
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agents.spec_reader import SpecParseError, parse_spec
from agents.test_generator import DesignSpec, generate_test_suite
from agents.verification_judge import run_verification
from memory.store import load_history, save_run

app = FastAPI(title="FaultClaw API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_SPEC_PATH = Path(__file__).resolve().parent.parent / "samples" / "adder_4bit.v"

_RESPONSE_FIELDS = (
    "design_name",
    "mode",
    "dut",
    "total_tests",
    "tests_passed",
    "tests_failed",
    "coverage_pct",
    "failed_tests",
)


def _run_pipeline(breakdown: bool = False, buggy: bool = False) -> dict:
    try:
        spec_dict = parse_spec(_SPEC_PATH)
    except (FileNotFoundError, SpecParseError) as exc:
        raise RuntimeError(f"spec parse failed: {exc}") from exc

    spec = DesignSpec.from_dict(spec_dict)
    suite = generate_test_suite(spec, breakdown=breakdown)
    report = run_verification(suite, buggy=buggy)

    save_run(
        design_name=report["design_name"],
        mode=report["mode"],
        total_tests=report["total_tests"],
        tests_passed=report["tests_passed"],
        tests_failed=report["tests_failed"],
        failed_tests=report["failed_tests"],
    )

    return {k: report[k] for k in _RESPONSE_FIELDS}


@app.post("/verify")
def verify():
    try:
        return _run_pipeline()
    except Exception as exc:
        return JSONResponse(status_code=500, content={"error": str(exc)})


@app.post("/verify/buggy")
def verify_buggy():
    try:
        return _run_pipeline(buggy=True)
    except Exception as exc:
        return JSONResponse(status_code=500, content={"error": str(exc)})


@app.post("/verify/breakdown")
def verify_breakdown():
    try:
        return _run_pipeline(breakdown=True)
    except Exception as exc:
        return JSONResponse(status_code=500, content={"error": str(exc)})


@app.get("/history")
def history():
    try:
        return load_history()
    except Exception as exc:
        return JSONResponse(status_code=500, content={"error": str(exc)})
