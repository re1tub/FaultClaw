"""FaultClaw REST API — v2.0.0 (no auth).

Endpoints
---------
POST /upload                 — upload a hardware spec file (.v .sv .json .yaml)
POST /verify                 — demo: run adder_4bit.v (normal mode)
POST /verify/buggy           — demo: buggy DUT
POST /verify/breakdown       — demo: breakdown mode
POST /verify/{file_id}       — run pipeline on uploaded file
GET  /results                — all results (last 10)
GET  /results/{file_id}      — latest result for a specific uploaded file
GET  /history                — raw memory/history.json (legacy)
"""

from __future__ import annotations

import json
import sqlite3
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from agents.spec_reader import SpecParseError, parse_spec
from agents.test_generator import DesignSpec, generate_test_suite
from agents.verification_judge import run_verification
from memory.store import load_history, save_run

# ---------------------------------------------------------------------------
# Paths & constants
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
UPLOADS_DIR = ROOT / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)
AUTH_DB = ROOT / "auth.db"
_SPEC_PATH = ROOT / "samples" / "adder_4bit.v"
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_SUFFIXES = {".v", ".sv", ".json", ".yaml", ".yml"}
_SUFFIX_TYPE = {".v": "verilog", ".sv": "verilog", ".json": "json", ".yaml": "yaml", ".yml": "yaml"}
_BASE_FIELDS = (
    "design_name", "mode", "dut",
    "total_tests", "tests_passed", "tests_failed",
    "coverage_pct", "failed_tests",
)


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
def _db() -> sqlite3.Connection:
    conn = sqlite3.connect(AUTH_DB)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db() -> None:
    with _db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS uploads (
                file_id          TEXT PRIMARY KEY,
                filename         TEXT NOT NULL,
                filepath         TEXT NOT NULL,
                detected_type    TEXT NOT NULL,
                upload_timestamp TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS results (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id     TEXT NOT NULL,
                mode        TEXT NOT NULL,
                report_json TEXT NOT NULL,
                timestamp   TEXT NOT NULL
            );
        """)


_init_db()


# ---------------------------------------------------------------------------
# Pipeline helper
# ---------------------------------------------------------------------------
def _run_pipeline(
    spec_path: Path | None = None,
    breakdown: bool = False,
    buggy: bool = False,
) -> dict:
    path = spec_path or _SPEC_PATH
    try:
        spec_dict = parse_spec(path)
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
    return {k: report[k] for k in _BASE_FIELDS}


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="FaultClaw API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(
            400,
            f"File type '{suffix}' not supported. Allowed: {', '.join(sorted(ALLOWED_SUFFIXES))}",
        )
    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(400, "File exceeds the 10 MB limit.")

    file_id = str(uuid.uuid4())
    filepath = UPLOADS_DIR / f"{file_id}{suffix}"
    filepath.write_bytes(content)

    detected_type = _SUFFIX_TYPE[suffix]
    timestamp = datetime.now(timezone.utc).isoformat()

    with _db() as conn:
        conn.execute(
            "INSERT INTO uploads VALUES (?, ?, ?, ?, ?)",
            (file_id, file.filename, str(filepath), detected_type, timestamp),
        )

    return {
        "file_id": file_id,
        "filename": file.filename,
        "detected_type": detected_type,
        "upload_timestamp": timestamp,
    }


# ---------------------------------------------------------------------------
# Demo endpoints — no auth, use hardcoded adder spec
# Defined before /verify/{file_id} to prevent route shadowing.
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Verification on an uploaded file
# ---------------------------------------------------------------------------
class VerifyBody(BaseModel):
    mode: str = "normal"


@app.post("/verify/{file_id}")
def verify_file(file_id: str, body: VerifyBody):
    if body.mode not in {"normal", "breakdown", "buggy"}:
        raise HTTPException(400, "mode must be one of: normal, breakdown, buggy")

    with _db() as conn:
        row = conn.execute(
            "SELECT filepath FROM uploads WHERE file_id = ?", (file_id,)
        ).fetchone()

    if not row:
        raise HTTPException(404, "File not found.")

    filepath = Path(row["filepath"])
    if not filepath.exists():
        raise HTTPException(404, "Uploaded file is no longer available on disk.")

    try:
        report = _run_pipeline(
            spec_path=filepath,
            breakdown=(body.mode == "breakdown"),
            buggy=(body.mode == "buggy"),
        )
    except Exception as exc:
        raise HTTPException(500, str(exc))

    timestamp = datetime.now(timezone.utc).isoformat()
    full = {**report, "timestamp": timestamp, "file_id": file_id, "run_mode": body.mode}

    with _db() as conn:
        conn.execute(
            "INSERT INTO results (file_id, mode, report_json, timestamp) VALUES (?, ?, ?, ?)",
            (file_id, body.mode, json.dumps(full), timestamp),
        )

    return full


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
@app.get("/results")
def get_all_results():
    with _db() as conn:
        rows = conn.execute(
            "SELECT id, file_id, mode, report_json, timestamp FROM results "
            "ORDER BY timestamp DESC LIMIT 10"
        ).fetchall()
    out = []
    for row in rows:
        r = json.loads(row["report_json"])
        out.append({
            "id": row["id"],
            "file_id": row["file_id"],
            "mode": row["mode"],
            "timestamp": row["timestamp"],
            "design_name": r.get("design_name", ""),
            "total_tests": r.get("total_tests", 0),
            "tests_passed": r.get("tests_passed", 0),
            "tests_failed": r.get("tests_failed", 0),
            "coverage_pct": r.get("coverage_pct", 0),
        })
    return out


@app.get("/results/{file_id}")
def get_result_by_file(file_id: str):
    with _db() as conn:
        row = conn.execute(
            "SELECT report_json, timestamp FROM results "
            "WHERE file_id = ? ORDER BY timestamp DESC LIMIT 1",
            (file_id,),
        ).fetchone()
    if not row:
        raise HTTPException(404, "No results found for this file.")
    report = json.loads(row["report_json"])
    return {
        **{k: report.get(k) for k in _BASE_FIELDS},
        "timestamp": row["timestamp"],
        "file_id": file_id,
    }


# ---------------------------------------------------------------------------
# Legacy
# ---------------------------------------------------------------------------
@app.get("/history")
def history():
    try:
        return load_history()
    except Exception as exc:
        return JSONResponse(status_code=500, content={"error": str(exc)})
