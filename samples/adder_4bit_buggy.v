// 4-bit combinational adder — BUGGY IMPLEMENTATION
// BUG: carry-out (sum[4]) is hardwired to 0.
// The lower 4 bits of the sum are correct, but any addition where a+b > 15
// silently drops the carry. Result wraps to (a+b) & 0xF instead of a+b.
// Example: 15+1 should give sum=16 (5'b10000), but gives sum=0 (5'b00000).
// behavior_hint: sum = a + b
module adder_4bit_buggy (
    input  [3:0] a,
    input  [3:0] b,
    output [4:0] sum
);
    // BUG: correct implementation is: assign sum = a + b;
    // Prefixing with 1'b0 forces sum[4] to 0, killing the carry-out.
    assign sum = {1'b0, a + b};
endmodule
