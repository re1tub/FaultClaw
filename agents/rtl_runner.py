import subprocess

def run_rtl_sim(testbench_file, dut_file):
    subprocess.run([
        "iverilog",
        "-o",
        "sim.out",
        testbench_file,
        dut_file
    ], check=True)

    result = subprocess.run(
        ["vvp", "sim.out"],
        capture_output=True,
        text=True,
        check=True
    )

    return result.stdout