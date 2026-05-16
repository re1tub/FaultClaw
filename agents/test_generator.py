"""Agent 2: deterministic adversarial test generation with optional model hints."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

class SpecValidationError(ValueError):
    """Raised when the incoming design spec is malformed."""


@dataclass(frozen=True)
class SignalSpec:
    name: str
    bits: int
    signed: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SignalSpec":
        if not isinstance(data, dict):
            raise SpecValidationError("Signal entries must be objects.")
        name = data.get("name")
        bits = data.get("bits")
        signed = bool(data.get("signed", False))
        if not isinstance(name, str) or not name:
            raise SpecValidationError("Signal name must be a non-empty string.")
        if not isinstance(bits, int) or bits <= 0:
            raise SpecValidationError(f"Signal '{name}' must declare a positive bit width.")
        return cls(name=name, bits=bits, signed=signed)

    @property
    def min_value(self) -> int:
        if self.signed:
            return -(2 ** (self.bits - 1))
        return 0

    @property
    def max_value(self) -> int:
        if self.signed:
            return (2 ** (self.bits - 1)) - 1
        return (2**self.bits) - 1


@dataclass(frozen=True)
class DesignSpec:
    design_name: str
    description: str
    inputs: tuple[SignalSpec, ...]
    outputs: tuple[SignalSpec, ...]
    behavior_hint: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DesignSpec":
        if not isinstance(data, dict):
            raise SpecValidationError("Design spec must be a JSON object.")

        design_name = data.get("design_name")
        description = data.get("description", "")
        behavior_hint = data.get("behavior_hint", "")
        raw_inputs = data.get("inputs")
        raw_outputs = data.get("outputs")

        if not isinstance(design_name, str) or not design_name:
            raise SpecValidationError("design_name must be a non-empty string.")
        if not isinstance(description, str):
            raise SpecValidationError("description must be a string.")
        if not isinstance(behavior_hint, str):
            raise SpecValidationError("behavior_hint must be a string.")
        if not isinstance(raw_inputs, list) or not raw_inputs:
            raise SpecValidationError("inputs must be a non-empty list.")
        if not isinstance(raw_outputs, list) or not raw_outputs:
            raise SpecValidationError("outputs must be a non-empty list.")

        inputs = tuple(SignalSpec.from_dict(item) for item in raw_inputs)
        outputs = tuple(SignalSpec.from_dict(item) for item in raw_outputs)
        return cls(
            design_name=design_name,
            description=description,
            inputs=inputs,
            outputs=outputs,
            behavior_hint=behavior_hint,
        )

    def validate_input_values(self, values: dict[str, int]) -> None:
        expected_names = {signal.name for signal in self.inputs}
        received_names = set(values)
        if expected_names != received_names:
            raise SpecValidationError(
                f"Input names mismatch. Expected {sorted(expected_names)}, got {sorted(received_names)}."
            )
        for signal in self.inputs:
            value = values[signal.name]
            if not isinstance(value, int):
                raise SpecValidationError(f"Input '{signal.name}' must be an integer.")
            if value < signal.min_value or value > signal.max_value:
                raise SpecValidationError(
                    f"Input '{signal.name}'={value} exceeds supported range "
                    f"[{signal.min_value}, {signal.max_value}]."
                )


def compute_expected_outputs(spec: DesignSpec, inputs: dict[str, int]) -> dict[str, int]:
    """Compute expected outputs for a simple adder-like design."""

    spec.validate_input_values(inputs)
    if len(spec.inputs) < 2 or len(spec.outputs) != 1:
        raise SpecValidationError("The default generator currently supports two-input, one-output designs.")

    ordered_inputs = [inputs[signal.name] for signal in spec.inputs]
    total = sum(ordered_inputs)
    output_signal = spec.outputs[0]

    if output_signal.signed:
        min_value = output_signal.min_value
        max_value = output_signal.max_value
        span = max_value - min_value + 1
        total = ((total - min_value) % span) + min_value

    return {output_signal.name: total}


def build_test_case(
    spec: DesignSpec,
    test_id: str,
    category: str,
    inputs: dict[str, int],
    rationale: str,
) -> dict[str, Any]:
    expected = compute_expected_outputs(spec, inputs)
    return {
        "id": test_id,
        "category": category,
        "inputs": inputs,
        "expected": expected,
        "rationale": rationale,
    }


def default_input_pair(spec: DesignSpec, a_value: int, b_value: int) -> dict[str, int]:
    return {
        spec.inputs[0].name: a_value,
        spec.inputs[1].name: b_value,
    }


def dedupe_tests(tests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for test in tests:
        key = json.dumps(test["inputs"], sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(test)
    return deduped


def generate_normal_tests(spec: DesignSpec) -> list[dict[str, Any]]:
    max_value = spec.inputs[0].max_value
    midpoint = max_value // 2
    curated_pairs = [
        (0, 0, "zero input sanity check"),
        (1, 1, "small-value addition"),
        (2, 3, "basic carry-free addition"),
        (midpoint, 1, "midrange plus small increment"),
        (3, midpoint, "asymmetric representative input"),
        (max(1, midpoint - 1), max(1, midpoint - 2), "representative midrange pair"),
    ]
    tests = [
        build_test_case(spec, f"normal_{index:03d}", "normal", default_input_pair(spec, a, b), rationale)
        for index, (a, b, rationale) in enumerate(curated_pairs, start=1)
    ]
    return dedupe_tests(tests)


def generate_edge_tests(spec: DesignSpec) -> list[dict[str, Any]]:
    max_value = spec.inputs[0].max_value
    near_max = max(0, max_value - 1)
    midpoint = max_value // 2
    curated_pairs = [
        (0, max_value, "minimum plus maximum boundary"),
        (max_value, 0, "maximum plus minimum boundary"),
        (max_value, 1, "overflow boundary from max plus one"),
        (near_max, 1, "near-max carry transition"),
        (max_value, max_value, "maximum plus maximum stress case"),
        (midpoint, midpoint, "midpoint carry-chain boundary"),
        (midpoint - 1 if midpoint > 0 else 0, midpoint, "pre-carry to carry boundary"),
        (5 if max_value >= 10 else midpoint, 10 if max_value >= 10 else near_max, "alternating bit pattern"),
    ]
    tests = [
        build_test_case(spec, f"edge_{index:03d}", "edge", default_input_pair(spec, a, b), rationale)
        for index, (a, b, rationale) in enumerate(curated_pairs, start=1)
    ]
    return dedupe_tests(tests)


def generate_adversarial_tests(spec: DesignSpec) -> list[dict[str, Any]]:
    max_value = spec.inputs[0].max_value
    near_max = max(0, max_value - 1)
    midpoint = max_value // 2
    curated_pairs = [
        (max_value, 1, "overflow edge that often exposes missing carry-out logic"),
        (max_value, near_max, "carry-chain stress with near-saturation inputs"),
        (midpoint, max_value, "asymmetric high-risk carry propagation"),
        (7 if max_value >= 7 else near_max, 8 if max_value >= 8 else max_value, "crosses a binary carry boundary"),
        (3, max_value, "small plus max to catch bad width assumptions"),
        (near_max, near_max, "double near-overflow boundary"),
    ]
    tests = [
        build_test_case(
            spec,
            f"adversarial_{index:03d}",
            "adversarial",
            default_input_pair(spec, a, b),
            rationale,
        )
        for index, (a, b, rationale) in enumerate(curated_pairs, start=1)
    ]
    return dedupe_tests(tests)


def generate_breakdown_tests(spec: DesignSpec) -> list[dict[str, Any]]:
    tests: list[dict[str, Any]] = []
    max_a = spec.inputs[0].max_value
    max_b = spec.inputs[1].max_value
    test_index = 1

    for a in range(max_a + 1):
        for b in range(max_b + 1):
            total = a + b
            category = "adversarial" if total > max(max_a, max_b) else "edge"
            rationale = "breakdown exhaustive sweep across the entire input space"
            tests.append(
                build_test_case(
                    spec,
                    f"breakdown_{test_index:03d}",
                    category,
                    default_input_pair(spec, a, b),
                    rationale,
                )
            )
            test_index += 1
    return tests


def generate_feedback_tests(spec: DesignSpec, feedback: dict[str, Any]) -> list[dict[str, Any]]:
    failed_inputs = feedback.get("failed_inputs")
    if not isinstance(failed_inputs, dict):
        return []

    spec.validate_input_values(failed_inputs)
    a_signal, b_signal = spec.inputs[0], spec.inputs[1]
    center_a = failed_inputs[a_signal.name]
    center_b = failed_inputs[b_signal.name]

    candidates: list[tuple[int, int, str]] = []
    for delta_a in (-1, 0, 1):
        for delta_b in (-1, 0, 1):
            candidate_a = min(max(center_a + delta_a, a_signal.min_value), a_signal.max_value)
            candidate_b = min(max(center_b + delta_b, b_signal.min_value), b_signal.max_value)
            rationale = f"feedback-focused neighborhood around reported failure ({center_a}, {center_b})"
            candidates.append((candidate_a, candidate_b, rationale))

    tests = [
        build_test_case(spec, f"feedback_{index:03d}", "feedback", default_input_pair(spec, a, b), rationale)
        for index, (a, b, rationale) in enumerate(candidates, start=1)
    ]
    return dedupe_tests(tests)


def _nemotron_env() -> dict[str, Any] | None:
    api_key = os.getenv("NVIDIA_API_KEY") or os.getenv("NEMOTRON_API_KEY")
    if not api_key:
        return None

    return {
        "api_key": api_key,
        "base_url": os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"),
        "model": os.getenv("NEMOTRON_MODEL", "nvidia/nemotron-3-super-120b-a12b"),
        "temperature": float(os.getenv("NEMOTRON_TEMPERATURE", "1")),
        "top_p": float(os.getenv("NEMOTRON_TOP_P", "0.95")),
        "max_tokens": int(os.getenv("NEMOTRON_MAX_TOKENS", "4096")),
        "reasoning_budget": int(os.getenv("NEMOTRON_REASONING_BUDGET", "4096")),
        "enable_thinking": os.getenv("NEMOTRON_ENABLE_THINKING", "true").lower() != "false",
    }


def _build_model_prompt(spec: DesignSpec, breakdown: bool, feedback: dict[str, Any] | None) -> str:
    prompt = {
        "task": (
            "Generate additional high-value hardware verification tests for this design. "
            "Return JSON only with a top-level 'tests' array. Each test must include "
            "'inputs' and 'rationale'."
        ),
        "constraints": {
            "max_tests": 6,
            "categories": ["adversarial"],
            "respect_declared_input_ranges": True,
            "prefer_novel_cases": True,
        },
        "design_spec": {
            "design_name": spec.design_name,
            "description": spec.description,
            "behavior_hint": spec.behavior_hint,
            "inputs": [
                {
                    "name": signal.name,
                    "bits": signal.bits,
                    "signed": signal.signed,
                    "min_value": signal.min_value,
                    "max_value": signal.max_value,
                }
                for signal in spec.inputs
            ],
            "outputs": [
                {
                    "name": signal.name,
                    "bits": signal.bits,
                    "signed": signal.signed,
                }
                for signal in spec.outputs
            ],
        },
        "mode": "breakdown" if breakdown else "normal",
        "feedback": feedback or {},
    }
    return json.dumps(prompt, indent=2)


def _extract_response_text(response: Any) -> str:
    message = response.choices[0].message
    content = getattr(message, "content", "")

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
            else:
                text = getattr(item, "text", None)
                if text:
                    parts.append(str(text))
        return "".join(parts)

    return str(content or "")


def _parse_model_candidates(raw_text: str, spec: DesignSpec) -> list[dict[str, Any]]:
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError:
        return []

    raw_tests = payload.get("tests")
    if not isinstance(raw_tests, list):
        return []

    parsed: list[dict[str, Any]] = []
    for index, candidate in enumerate(raw_tests, start=1):
        if not isinstance(candidate, dict):
            continue
        inputs = candidate.get("inputs")
        rationale = candidate.get("rationale", "model-suggested adversarial candidate")
        if not isinstance(inputs, dict) or not isinstance(rationale, str):
            continue
        try:
            spec.validate_input_values(inputs)
            parsed.append(
                build_test_case(
                    spec,
                    f"model_{index:03d}",
                    "adversarial",
                    inputs,
                    rationale,
                )
            )
        except SpecValidationError:
            continue
    return parsed


def load_model_candidates(_spec: DesignSpec, _breakdown: bool, _feedback: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Optionally fetch extra adversarial candidates from a Nemotron-compatible API."""

    config = _nemotron_env()
    if config is None:
        return []

    from openai import OpenAI  # noqa: PLC0415 — lazy import, only needed when API key is set
    client = OpenAI(
        base_url=config["base_url"],
        api_key=config["api_key"],
    )
    response = client.chat.completions.create(
        model=config["model"],
        messages=[
            {
                "role": "user",
                "content": _build_model_prompt(_spec, _breakdown, _feedback),
            }
        ],
        temperature=config["temperature"],
        top_p=config["top_p"],
        max_tokens=config["max_tokens"],
        extra_body={
            "chat_template_kwargs": {"enable_thinking": config["enable_thinking"]},
            "reasoning_budget": config["reasoning_budget"],
        },
    )
    return _parse_model_candidates(_extract_response_text(response), _spec)


def generate_test_suite(spec: DesignSpec, breakdown: bool = False, feedback: dict[str, Any] | None = None) -> dict[str, Any]:
    tests: list[dict[str, Any]] = []

    if breakdown:
        tests.extend(generate_breakdown_tests(spec))
    else:
        tests.extend(generate_normal_tests(spec))
        tests.extend(generate_edge_tests(spec))
        tests.extend(generate_adversarial_tests(spec))

    if feedback:
        tests.extend(generate_feedback_tests(spec, feedback))

    tests.extend(load_model_candidates(spec, breakdown, feedback))
    tests = dedupe_tests(tests)

    return {
        "design_name": spec.design_name,
        "mode": "breakdown" if breakdown else "normal",
        "test_count": len(tests),
        "tests": tests,
    }


def load_json_file(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate adversarial tests for FaultClaw Agent 2.")
    parser.add_argument("--spec", required=True, help="Path to the Agent 1 design spec JSON file.")
    parser.add_argument("--feedback", help="Optional path to failure feedback JSON from Agent 3.")
    parser.add_argument("--breakdown", action="store_true", help="Enable exhaustive Breakdown Mode.")
    parser.add_argument("--output", help="Optional path to write the generated test suite JSON.")
    args = parser.parse_args()

    spec_payload = load_json_file(Path(args.spec))
    feedback_payload = load_json_file(Path(args.feedback)) if args.feedback else None
    spec = DesignSpec.from_dict(spec_payload)
    suite = generate_test_suite(spec, breakdown=args.breakdown, feedback=feedback_payload)
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
