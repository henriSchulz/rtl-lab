// ---------------------------------------------------------------------------
// alu_pkg.sv  --  Opcodes shared by the alu and its testbench
//
//   Workspace:  rtl-lab
//   Module:     alu
//   Author:     Henri Schulz <henri.schulz.bs@icloud.com>
//   Created:    2026-09-10 22:04  (rtl 0.1.0)
//
// This header was generated when the file was created; from here on the
// file is yours.
// ---------------------------------------------------------------------------

package alu_pkg;

  // Width of the opcode field; keep ALU_* and this in sync.
  localparam int unsigned OpWidth = 3;

  typedef enum logic [OpWidth-1:0] {
    ALU_ADD = 3'd0,   // a + b, carry out
    ALU_SUB = 3'd1,   // a - b, borrow out
    ALU_AND = 3'd2,
    ALU_OR  = 3'd3,
    ALU_XOR = 3'd4,
    ALU_SLL = 3'd5,   // a << b[$clog2(Width)-1:0]
    ALU_SRL = 3'd6,   // a >> b[$clog2(Width)-1:0]
    ALU_SLT = 3'd7    // unsigned a < b, result 0 or 1
  } alu_op_e;

endpackage
