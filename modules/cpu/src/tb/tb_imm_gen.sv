// ---------------------------------------------------------------------------
// tb_imm_gen.sv  --  Tests for imm_gen
//
//   Workspace:  rtl-lab
//   Module:     cpu
//   Author:     Henri Schulz <henri.schulz.bs@icloud.com>
//   Created:    2026-09-21 20:32  (flow 0.1.0)
//
// Classic SystemVerilog testbench (framework: sv). `flow sim` compiles and
// runs it, and reads the verdict off these lines:
//
//   TEST PASSED   all good        TEST FAILED + $fatal   something broke
//
// Waveform: `flow sim` defines WAVES and WAVE_FILE while sim.waves is on.
// ---------------------------------------------------------------------------

`timescale 1ns/1ps
`default_nettype none

module tb_imm_gen;

  import cpu_pkg::*;

  localparam int unsigned Width = 32;

  logic [Width-1:0] instr_i;
  imm_type_e        imm_type_i;
  logic [Width-1:0] imm_o;

  int unsigned errors   = 0;
  string       testcase = "";                   // from +TESTCASE=<name>

  // -- DUT --------------------------------------------------------------
  imm_gen #(
      .Width (Width)
  ) dut (
      .instr_i    (instr_i),
      .imm_type_i (imm_type_i),
      .imm_o      (imm_o)
  );

  // -- Waveform ---------------------------------------------------------
`ifdef WAVES
  initial begin
    $dumpfile(`WAVE_FILE);
    $dumpvars(0, tb_imm_gen);
  end
`endif

  // -- Helpers ----------------------------------------------------------
  function automatic void check(bit condition, string message);
    if (!condition) begin
      errors++;
      $display("[%0t] ERROR: %s", $time, message);
    end
  endfunction

  // Without +TESTCASE everything runs, otherwise only the named test.
  function automatic bit selected(string name);
    return (testcase == "" || testcase == name);
  endfunction

  // Combinational: apply, settle, compare.
  task automatic check_imm(string asm, logic [31:0] instr, imm_type_e imm_type,
                           logic [31:0] expected);
    instr_i    = instr;
    imm_type_i = imm_type;
    #1ns;
    check(imm_o == expected,
          $sformatf("%-18s (%s) instr=0x%08X: expected 0x%08X, got 0x%08X",
                    asm, imm_type.name(), instr, expected, imm_o));
  endtask

  // -- Tests ------------------------------------------------------------
  // Encodings checked against llvm-mc -triple=riscv32 -show-encoding.
  // One positive and one negative immediate per format.
  task automatic test_formats();
    check_imm("addi x1, x0, 5",   32'h0050_0093, IMM_I, 32'h0000_0005);
    check_imm("addi x1, x0, -1",  32'hFFF0_0093, IMM_I, 32'hFFFF_FFFF);
    check_imm("sw x2, 8(x1)",     32'h0020_A423, IMM_S, 32'h0000_0008);
    check_imm("sw x2, -4(x1)",    32'hFE20_AE23, IMM_S, 32'hFFFF_FFFC);
    check_imm("beq x1, x2, 16",   32'h0020_8863, IMM_B, 32'h0000_0010);
    check_imm("beq x1, x2, -8",   32'hFE20_8CE3, IMM_B, 32'hFFFF_FFF8);
    check_imm("lui x1, 0x12345",  32'h1234_50B7, IMM_U, 32'h1234_5000);
    check_imm("lui x1, 0xFFFFF",  32'hFFFF_F0B7, IMM_U, 32'hFFFF_F000);
    check_imm("jal x1, 2048",     32'h0010_00EF, IMM_J, 32'h0000_0800);
    check_imm("jal x1, -4",       32'hFFDF_F0EF, IMM_J, 32'hFFFF_FFFC);
  endtask

  // -- Sequence ---------------------------------------------------------
  initial begin
    void'($value$plusargs("TESTCASE=%s", testcase));

    if (selected("test_formats")) test_formats();

    if (errors != 0) begin
      $display("TEST FAILED  (%0d error(s))", errors);
      $fatal(1);
    end
    $display("TEST PASSED");
    $finish;
  end

endmodule

`default_nettype wire
