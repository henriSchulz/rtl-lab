// ---------------------------------------------------------------------------
// imm_gen.sv  --  RTL module imm_gen
//
//   Workspace:  rtl-lab
//   Module:     cpu
//   Author:     Henri Schulz <henri.schulz.bs@icloud.com>
//   Created:    2026-09-21 20:31  (flow 0.1.0)
//
// This header was generated when the file was created; from here on the
// file is yours.
// ---------------------------------------------------------------------------

`default_nettype none

module imm_gen 
import cpu_pkg::*;
#(
    parameter int unsigned Width = 32
) (
    input logic [Width-1:0] instr_i,
    input imm_type_e imm_type_i,
    output logic [Width-1:0] imm_o
);

  always_comb begin
    case (imm_type_i)
      IMM_I: imm_o = {{20{instr_i[31]}}, instr_i[31:20]};
      IMM_S: imm_o = {{20{instr_i[31]}}, instr_i[31:25], instr_i[11:7]};
      IMM_B: imm_o = {{19{instr_i[31]}}, instr_i[31], instr_i[7], instr_i[30:25], instr_i[11:8], 1'b0};
      IMM_U: imm_o = {instr_i[31:12], 12'b0};
      IMM_J: imm_o = {{11{instr_i[31]}}, instr_i[31], instr_i[19:12], instr_i[20], instr_i[30:21], 1'b0};
      default: imm_o = 0;
    endcase
  end

  

endmodule

`default_nettype wire
