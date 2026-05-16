import json
from pathlib import Path


def log_failure(
    a,
    b,
    expected_sum,
    expected_cout,
    observed_sum,
    observed_cout
):

    failure = {
        "A": a,
        "B": b,
        "expected": {
            "SUM": expected_sum,
            "COUT": expected_cout
        },
        "observed": {
            "SUM": observed_sum,
            "COUT": observed_cout
        }
    }

    # Get path to current verification folder
    current_dir = Path(__file__).parent

    # Create failures.json path
    log_file = current_dir / "failures.json"

    try:
        with open(log_file, "a") as f:
            json.dump(failure, f)
            f.write("\n")

        print("Failure logged successfully.")

    except Exception as e:
        print(f"ERROR: Could not write failure log.")
        print(e)