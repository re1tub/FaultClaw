import json
import sys
import unittest
from unittest.mock import MagicMock, patch

from agents.test_generator import DesignSpec, generate_test_suite, load_model_candidates


def load_spec() -> DesignSpec:
    return DesignSpec.from_dict(
        {
            "design_name": "adder_4bit",
            "description": "4-bit combinational adder",
            "inputs": [
                {"name": "a", "bits": 4, "signed": False},
                {"name": "b", "bits": 4, "signed": False},
            ],
            "outputs": [
                {"name": "sum", "bits": 5, "signed": False},
            ],
            "behavior_hint": "sum = a + b",
        }
    )


class GeneratorTests(unittest.TestCase):
    def test_normal_mode_contains_multiple_categories(self) -> None:
        suite = generate_test_suite(load_spec())
        categories = {test["category"] for test in suite["tests"]}
        self.assertEqual(suite["mode"], "normal")
        self.assertIn("normal", categories)
        self.assertIn("edge", categories)
        self.assertIn("adversarial", categories)

    def test_breakdown_mode_exhaustive_for_four_bit_inputs(self) -> None:
        suite = generate_test_suite(load_spec(), breakdown=True)
        self.assertEqual(suite["mode"], "breakdown")
        self.assertEqual(suite["test_count"], 256)

    def test_feedback_generation_focuses_around_failure(self) -> None:
        suite = generate_test_suite(
            load_spec(),
            feedback={
                "failed_inputs": {
                    "a": 15,
                    "b": 1,
                }
            },
        )
        categories = [test["category"] for test in suite["tests"]]
        self.assertIn("feedback", categories)

    def test_expected_sum_is_computed_in_python(self) -> None:
        suite = generate_test_suite(load_spec())
        target = next(test for test in suite["tests"] if test["inputs"] == {"a": 15, "b": 1})
        self.assertEqual(target["expected"], {"sum": 16})

    def test_model_candidates_disabled_without_api_key(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(load_model_candidates(load_spec(), False, None), [])

    def test_model_candidates_parse_valid_json_response(self) -> None:
        # Inject a mock openai module so this test runs without openai installed.
        mock_openai_mod = MagicMock()
        mock_client = MagicMock()
        mock_openai_mod.OpenAI.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        content=json.dumps(
                            {
                                "tests": [
                                    {
                                        "inputs": {"a": 15, "b": 0},
                                        "rationale": "max input sanity check from model",
                                    },
                                    {
                                        "inputs": {"a": 15, "b": 99},
                                        "rationale": "invalid and should be ignored",
                                    },
                                ]
                            }
                        )
                    )
                )
            ]
        )

        with patch.dict(sys.modules, {"openai": mock_openai_mod}):
            with patch.dict("os.environ", {"NVIDIA_API_KEY": "test-key"}, clear=True):
                candidates = load_model_candidates(load_spec(), False, None)

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["inputs"], {"a": 15, "b": 0})
        self.assertEqual(candidates[0]["expected"], {"sum": 15})


if __name__ == "__main__":
    unittest.main()
