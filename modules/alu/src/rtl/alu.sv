// ---------------------------------------------------------------------------
// alu.sv  --  Combinational ALU: arithmetic, logic, shift and compare
//
//   Workspace:  rtl-lab
//   Module:     alu
//   Author:     Henri Schulz <henri.schulz.bs@icloud.com>
//   Created:    2026-09-10 22:04  (rtl 0.1.0)
//
// This header was generated when the file was created; from here on the
// file is yours.
// ---------------------------------------------------------------------------

`default_nettype none

module alu
  import alu_pkg::*;
#(
    parameter int unsigned Width = 8
) (
    input  alu_op_e          op_i,
    input  logic [Width-1:0] a_i,
    input  logic [Width-1:0] b_i,

    output logic [Width-1:0] result_o,
    output logic             zero_o,     // result is all zeroes
    output logic             carry_o     // carry out on ADD, borrow on SUB
);

  localparam int unsigned ShiftWidth = $clog2(Width);

  // One bit wider than the operands, so the carry falls out on top.
  logic [Width:0]           sum;
  logic [ShiftWidth-1:0]    shamt;

  assign shamt = b_i[ShiftWidth-1:0];

  always_comb begin
    sum      = '0;
    result_o = '0;
    carry_o  = 1'b0;

    unique case (op_i)
      ALU_ADD: begin
        sum      = {1'b0, a_i} + {1'b0, b_i};
        result_o = sum[Width-1:0];
        carry_o  = sum[Width];
      end

      ALU_SUB: begin
        sum      = {1'b0, a_i} - {1'b0, b_i};
        result_o = sum[Width-1:0];
        carry_o  = sum[Width];
      end

      ALU_AND: result_o = a_i & b_i;
      ALU_OR:  result_o = a_i | b_i;
      ALU_XOR: result_o = a_i ^ b_i;
      ALU_SLL: result_o = a_i << shamt;
      ALU_SRL: result_o = a_i >> shamt;
      ALU_SLT: result_o = {{(Width - 1){1'b0}}, (a_i < b_i)};

      default: result_o = '0;
    endcase
  end

  assign zero_o = (result_o == '0);

endmodule

`default_nettype wire
