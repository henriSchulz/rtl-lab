// ---------------------------------------------------------------------------
// cpu_pkg.sv  --  RTL module cpu_pkg
//
//   Workspace:  rtl-lab
//   Module:     cpu
//   Author:     Henri Schulz <henri.schulz.bs@icloud.com>
//   Created:    2026-09-21 12:37  (flow 0.1.0)
//
// This header was generated when the file was created; from here on the
// file is yours.
// ---------------------------------------------------------------------------

`default_nettype none

package cpu_pkg;

    typedef enum logic [3:0] {
        ALU_ADD  = 4'b0000, // Addition (a+b)
        ALU_SUB  = 4'b1000, // Subtraction (a-b)
        ALU_SLL  = 4'b0001, // Shift Left Logical (a << b)
        ALU_SLT  = 4'b0010, // Set on Less Than (a < b)
        ALU_SLTU = 4'b0011, // Set on Less Than Unsigned (a < b)
        ALU_XOR  = 4'b0100, // Exclusive OR (a ^ b)
        ALU_SRL  = 4'b0101, // Shift Right Logical (a >> b)
        ALU_SRA  = 4'b1101, // Shift Right Arithmetic (a >>> b)
        ALU_OR   = 4'b0110, // Inclusive OR (a | b)
        ALU_AND  = 4'b0111 // AND (a & b)
    } alu_op_e;

endpackage

`default_nettype wire
