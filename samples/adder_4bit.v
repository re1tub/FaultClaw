// 4-bit combinational adder
// behavior_hint: sum = a + b
module adder_4bit (
    input  [3:0] a,
    input  [3:0] b,
    output [4:0] sum
);
    assign sum = a + b;
endmodule
