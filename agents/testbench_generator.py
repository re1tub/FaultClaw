def generate_testbench(test_cases, dut_name="adder_4bit"):
    tb = f"""
`timescale 1ns/1ps

module tb;

reg [3:0] a;
reg [3:0] b;
wire [4:0] sum;

{dut_name} uut (
    .a(a),
    .b(b),
    .sum(sum)
);

initial begin
"""

    for a, b in test_cases:
        tb += f"""
    a = 4'b{a:04b};
    b = 4'b{b:04b};
    #1;
    $display("%d,%d,%d", a, b, sum);
"""

    tb += """
    $finish;
end

endmodule
"""

    return tb
