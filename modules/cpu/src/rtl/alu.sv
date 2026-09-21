// ---------------------------------------------------------------------------
// alu.sv  --  RTL module alu
//
//   Workspace:  rtl-lab
//   Module:     cpu
//   Author:     Henri Schulz <henri.schulz.bs@icloud.com>
//   Created:    2026-09-21 12:24  (flow 0.1.0)
//
// This header was generated when the file was created; from here on the
// file is yours.
// ---------------------------------------------------------------------------

`default_nettype none



module alu 
import cpu_pkg::*;
#(
    parameter int unsigned Width = 32
) (
    

    input logic [Width-1:0]           operand_a_i,       // first alu operand
    input logic [Width-1:0]           operand_b_i,       // seoncd alu operand
    input alu_op_e                    op_i,             // alu op code  --> {instr[30], func3}

    output logic [Width-1:0]          result_o  // alu result

);

  //----------------------------------------
  // localparam
  //---------------------------------------

  localparam int unsigned ShamtW = $clog2(Width);

  //----------------------------------------
  // always_comb
  //----------------------------------------

  // Combinational alu block
  always_comb begin 

    case (op_i) 

      ALU_ADD:      result_o = operand_a_i + operand_b_i;
      ALU_SUB:      result_o = operand_a_i - operand_b_i;
      ALU_SLL:      result_o = operand_a_i << operand_b_i[ShamtW-1:0]; 
      ALU_SLT:      result_o = {{(Width-1){1'b0}}, $signed(operand_a_i) < $signed(operand_b_i)}; 
      ALU_SLTU:     result_o = {{(Width-1){1'b0}}, operand_a_i < operand_b_i};                   
      ALU_SRL:      result_o = operand_a_i >> operand_b_i[ShamtW-1:0];
      ALU_SRA:      result_o = $unsigned($signed(operand_a_i) >>> operand_b_i[ShamtW-1:0]);
      ALU_OR:       result_o = operand_a_i | operand_b_i;
      ALU_AND:      result_o = operand_a_i & operand_b_i;
      ALU_XOR:      result_o = operand_a_i ^ operand_b_i;
      default:      result_o = '0;
    endcase
    
  end

  



endmodule

`default_nettype wire


