import unittest

from agents.test_generator import DesignSpec, generate_test_suite


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


if __name__ == "__main__":
    unittest.main()
