// ---------------------------------------------------------------------------
// branch_unit.sv  --  RTL module branch_unit
//
//   Workspace:  rtl-lab
//   Module:     cpu
//   Author:     Henri Schulz <henri.schulz.bs@icloud.com>
//   Created:    2026-09-21 21:08  (flow 0.1.0)
//
// This header was generated when the file was created; from here on the
// file is yours.
// ---------------------------------------------------------------------------

`default_nettype none

module branch_unit 
  import cpu_pkg::*;
#(
    parameter int unsigned Width = 32
) (

  input logic [Width-1:0] operand_a_i, // rs1
  input logic [Width-1:0] operand_b_i, // rs2
  input branch_op_e        branch_op_i,
  output logic             branch_taken_o
);


  always_comb begin
    case (branch_op_i)
      BR_EQ:  branch_taken_o = (operand_a_i == operand_b_i);
      BR_NE:  branch_taken_o = (operand_a_i != operand_b_i);
      BR_LT:  branch_taken_o = ($signed(operand_a_i) < $signed(operand_b_i));
      BR_GE:  branch_taken_o = ($signed(operand_a_i) >= $signed(operand_b_i));
      BR_LTU: branch_taken_o = (operand_a_i < operand_b_i);
      BR_GEU: branch_taken_o = (operand_a_i >= operand_b_i);
      default: branch_taken_o = 1'b0;
    endcase
  end




 

endmodule

`default_nettype wire
