"""Agent 1: hardware design spec reader and normaliser.

Parses a hardware design specification from JSON, YAML, or a Verilog module
header and emits a DesignSpec-compatible JSON consumed by Agent 2.

Supported input formats (auto-detected from file extension):
  .json        — DesignSpec JSON (passthrough with validation)
  .yaml / .yml — YAML brief (requires PyYAML)
  .v  / .sv    — Verilog / SystemVerilog module header
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


class SpecParseError(ValueError):
    """Raised when a spec file cannot be parsed or fails structural validation."""


# ---------------------------------------------------------------------------
# Signal / spec normalisation
# ---------------------------------------------------------------------------

def _coerce_signal(data: Any, context: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise SpecParseError(f"{context}: entry must be a mapping, got {type(data).__name__}.")
    name = data.get("name")
    bits = data.get("bits")
    signed = bool(data.get("signed", False))
    if not isinstance(name, str) or not name:
        raise SpecParseError(f"{context}: 'name' must be a non-empty string.")
    if not isinstance(bits, int) or bits <= 0:
        raise SpecParseError(f"{context} '{name}': 'bits' must be a positive integer.")
    return {"name": name, "bits": bits, "signed": signed}


def _coerce_spec(raw: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalise a raw mapping into a DesignSpec-compatible dict."""
    if not isinstance(raw, dict):
        raise SpecParseError("Design spec must be a JSON object / YAML mapping.")
    design_name = raw.get("design_name")
    description = raw.get("description", "")
    behavior_hint = raw.get("behavior_hint", "")
    raw_inputs = raw.get("inputs")
    raw_outputs = raw.get("outputs")

    if not isinstance(design_name, str) or not design_name:
        raise SpecParseError("'design_name' must be a non-empty string.")
    if not isinstance(description, str):
        raise SpecParseError("'description' must be a string.")
    if not isinstance(behavior_hint, str):
        raise SpecParseError("'behavior_hint' must be a string.")
    if not isinstance(raw_inputs, list) or not raw_inputs:
        raise SpecParseError("'inputs' must be a non-empty list.")
    if not isinstance(raw_outputs, list) or not raw_outputs:
        raise SpecParseError("'outputs' must be a non-empty list.")

    return {
        "design_name": design_name,
        "description": description,
        "behavior_hint": behavior_hint,
        "inputs": [_coerce_signal(s, f"inputs[{i}]") for i, s in enumerate(raw_inputs)],
        "outputs": [_coerce_signal(s, f"outputs[{i}]") for i, s in enumerate(raw_outputs)],
    }


# ---------------------------------------------------------------------------
# JSON / YAML parser
# ---------------------------------------------------------------------------

def _parse_structured(text: str, suffix: str) -> dict[str, Any]:
    if suffix == ".json":
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise SpecParseError(f"Invalid JSON: {exc}") from exc

    try:
        import yaml  # type: ignore[import]
    except ImportError as exc:
        raise SpecParseError(
            "PyYAML is required to read YAML files. Install it with: pip install pyyaml"
        ) from exc
    try:
        return yaml.safe_load(text)
    except Exception as exc:
        raise SpecParseError(f"Invalid YAML: {exc}") from exc


# ---------------------------------------------------------------------------
# Verilog / SystemVerilog module header parser
# ---------------------------------------------------------------------------

_MODULE_RE = re.compile(r"\bmodule\s+(\w+)", re.IGNORECASE)
_ENDMODULE_RE = re.compile(r"\bendmodule\b", re.IGNORECASE)
_BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)

# Matches a single port declaration.  Handles:
#   input [3:0] a
#   output [4:0] sum
#   input signed [7:0] data
#   input wire [3:0] a, b          (multi-name, same width)
#   output logic [4:0] result
_PORT_RE = re.compile(
    r"\b(?P<dir>input|output)\b"
    r"(?:\s+(?:wire|reg|logic|tri))?"          # optional type keyword
    r"(?:\s+(?P<signed>signed))?"
    r"(?:\s*\[(?P<msb>\d+)\s*:\s*(?P<lsb>\d+)\])?"
    r"\s+(?P<names>\w+(?:\s*,\s*\w+)*)"
    r"(?=\s*[;,)])",                            # lookahead: end with ; , or )
    re.IGNORECASE,
)

_BEHAVIOR_HINT_RE = re.compile(r"//\s*behavior_hint\s*:\s*(.+)", re.IGNORECASE)
_LINE_COMMENT_RE = re.compile(r"//\s*(?!behavior_hint\b)(.+)")


def _parse_verilog(source: str) -> dict[str, Any]:
    clean = _BLOCK_COMMENT_RE.sub(" ", source)

    module_match = _MODULE_RE.search(clean)
    if not module_match:
        raise SpecParseError("No 'module' declaration found in the Verilog source.")
    design_name = module_match.group(1)

    body_start = module_match.end()
    end_match = _ENDMODULE_RE.search(clean, body_start)
    body = clean[body_start : end_match.start()] if end_match else clean[body_start:]

    hint_match = _BEHAVIOR_HINT_RE.search(source)
    behavior_hint = hint_match.group(1).strip() if hint_match else ""

    description = ""
    for m in _LINE_COMMENT_RE.finditer(source):
        candidate = m.group(1).strip()
        if candidate:
            description = candidate
            break

    inputs: list[dict[str, Any]] = []
    outputs: list[dict[str, Any]] = []

    for m in _PORT_RE.finditer(body):
        direction = m.group("dir").lower()
        is_signed = m.group("signed") is not None
        msb_str = m.group("msb")
        lsb_str = m.group("lsb")
        bits = int(msb_str) - int(lsb_str) + 1 if msb_str is not None else 1
        names = [n.strip() for n in m.group("names").split(",") if n.strip()]
        for port_name in names:
            signal = {"name": port_name, "bits": bits, "signed": is_signed}
            (inputs if direction == "input" else outputs).append(signal)

    if not inputs:
        raise SpecParseError("No input ports found in the Verilog module.")
    if not outputs:
        raise SpecParseError("No output ports found in the Verilog module.")

    return {
        "design_name": design_name,
        "description": description,
        "behavior_hint": behavior_hint,
        "inputs": inputs,
        "outputs": outputs,
    }


# ---------------------------------------------------------------------------
# Format dispatch
# ---------------------------------------------------------------------------

_VERILOG_SUFFIXES = {".v", ".sv"}
_STRUCTURED_SUFFIXES = {".json", ".yaml", ".yml"}


def parse_spec(path: Path, force_format: str | None = None) -> dict[str, Any]:
    """Read *path* and return a validated DesignSpec-compatible dict."""
    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8")

    if force_format is not None:
        if force_format == "verilog":
            return _coerce_spec(_parse_verilog(text))
        if force_format in {"json", "yaml"}:
            return _coerce_spec(_parse_structured(text, f".{force_format}"))
        raise SpecParseError(
            f"Unknown format '{force_format}'. Choose from: json, yaml, verilog."
        )

    if suffix in _VERILOG_SUFFIXES:
        return _coerce_spec(_parse_verilog(text))
    if suffix in _STRUCTURED_SUFFIXES:
        return _coerce_spec(_parse_structured(text, suffix))

    raise SpecParseError(
        f"Cannot determine parser for extension '{suffix}'. "
        "Pass --format {{json,yaml,verilog}} to force one."
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="FaultClaw Agent 1 — parse a hardware design spec into Agent 2 JSON."
    )
    parser.add_argument(
        "spec",
        help="Path to the design spec file (.json, .yaml, .yml, .v, .sv).",
    )
    parser.add_argument(
        "--format",
        choices=["json", "yaml", "verilog"],
        help="Force a specific parser (auto-detected from file extension by default).",
    )
    parser.add_argument(
        "--output",
        help="Write the output JSON to this path instead of stdout.",
    )
    args = parser.parse_args()

    spec_path = Path(args.spec)
    if not spec_path.exists():
        print(f"error: file not found: {spec_path}", file=sys.stderr)
        return 1

    try:
        spec_dict = parse_spec(spec_path, force_format=args.format)
    except SpecParseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    serialized = json.dumps(spec_dict, indent=2)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(serialized + "\n", encoding="utf-8")
    else:
        print(serialized)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
