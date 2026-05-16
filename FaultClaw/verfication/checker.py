from adder_golden import golden_adder
from logger import log_failure


def check_case(a, b, dut_sum, dut_cout):

    expected_sum, expected_cout = golden_adder(a, b)

    passed = (
        expected_sum == dut_sum and
        expected_cout == dut_cout
    )

    if passed:
        print("PASS")

    else:
        print("FAIL")
        print(f"Inputs: A={a}, B={b}")
        print(f"Expected: SUM={expected_sum}, COUT={expected_cout}")
        print(f"Observed: SUM={dut_sum}, COUT={dut_cout}")

        log_failure(
            a,
            b,
            expected_sum,
            expected_cout,
            dut_sum,
            dut_cout
        )


# Example DUT outputs
test_cases = [
    (0, 0, 0, 0),
    (1, 1, 2, 0),
    (15, 1, 0, 0),   # intentionally wrong
    (15, 15, 14, 1)
]

for case in test_cases:
    check_case(*case)