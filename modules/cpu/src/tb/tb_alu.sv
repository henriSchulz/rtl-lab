// ---------------------------------------------------------------------------
// tb_alu.sv  --  Tests for alu
//
//   Workspace:  rtl-lab
//   Module:     cpu
//   Author:     Henri Schulz <henri.schulz.bs@icloud.com>
//   Created:    2026-09-21 13:33  (flow 0.1.0)
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

module tb_alu;

  import cpu_pkg::*;

  localparam int unsigned Width     = 32;
 

  logic [Width-1:0] operand_a_i;
  logic [Width-1:0] operand_b_i;
  alu_op_e          op_i;
  logic [Width-1:0] result_o;

  int unsigned errors   = 0;
  string       testcase = "";                   // from +TESTCASE=<name>

  // -- DUT --------------------------------------------------------------
  alu #(
      .Width (Width)
  ) dut (
      .operand_a_i (operand_a_i),
      .operand_b_i (operand_b_i),
      .op_i        (op_i),
      .result_o    (result_o)
  );


  // -- Waveform ---------------------------------------------------------
`ifdef WAVES
  initial begin
    $dumpfile(`WAVE_FILE);
    $dumpvars(0, tb_alu);
  end
`endif

  // -- Helpers ----------------------------------------------------------
  // Stimulus is driven non-blocking: the DUT samples the old value at the
  // clock edge, the new one lands afterwards. Blocking assignments right at
  // the edge would race with the design.
  function automatic void drive(logic [Width-1:0] a, logic [Width-1:0] b, alu_op_e op);
    operand_a_i <= a;
    operand_b_i <= b;
    op_i        <= op;
  endfunction

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

  // -- Tests ------------------------------------------------------------

  task automatic test_addition();

    // Test addition
    drive(32'h0000_0001, 32'h0000_0002, ALU_ADD);
    #1ns;
    check(result_o == 32'h0000_0003, "Addition failed: 1 + 2 != 3");

    // Test addition with overflow
    drive(32'hFFFF_FFFF, 32'h0000_0001, ALU_ADD);
    #1ns;
    check(result_o == 32'h0000_0000, "Addition with overflow failed: 0xFFFFFFFF + 1 != 0");

    // Test addition with negative numbers

    drive(32'hFFFF_FFFF, 32'hFFFF_FFFE, ALU_ADD);
    #1ns;
    check(result_o == 32'hFFFF_FFFD, "Addition with negative numbers failed: -1 + -2 != -3"); 
  endtask

  task automatic test_subtraction();

    // Test subtraction
    drive(32'h0000_0005, 32'h0000_0003, ALU_SUB);
    #1ns;
    op_i        = ALU_SUB;
    #1ns;
    check(result_o == 32'h0000_0002, "Subtraction failed: 5 - 3 != 2");

    // Test subtraction with negative result
    drive(32'h0000_0003, 32'h0000_0005, ALU_SUB);
    #1ns;
    check(result_o == 32'hFFFF_FFFE, "Subtraction with negative result failed: 3 - 5 != -2");

  endtask


  task automatic test_shift_left_logical();

    // Test shift left logical
    drive(32'h0000_0001, 32'h0000_0002, ALU_SLL);
    #1ns;
    check(result_o == 32'h0000_0004, "Shift left logical failed: 1 << 2 != 4");

    // Test shift left logical with zero
    drive(32'h0000_0000, 32'h0000_0003, ALU_SLL);
    #1ns;
    check(result_o == 32'h0000_0000, "Shift left logical with zero failed: 0 << 3 != 0");

  endtask

  task automatic test_set_on_less_than();

    // Test set on less than
    drive(32'h0000_0002, 32'h0000_0003, ALU_SLT);
    #1ns;
    check(result_o == 32'h0000_0001, "Set on less than failed: 2 < 3 != 1");

    // Test set on less than with equal values
    drive(32'h0000_0003, 32'h0000_0003, ALU_SLT);
    #1ns;
    check(result_o == 32'h0000_0000, "Set on less than with equal values failed: 3 < 3 != 0");

  endtask

  task automatic test_set_on_less_than_unsigned();

    // Test set on less than unsigned
    drive(32'h0000_0002, 32'h0000_0003, ALU_SLTU);
    #1ns;
    check(result_o == 32'h0000_0001, "Set on less than unsigned failed: 2 < 3 != 1");

    // Test set on less than unsigned with equal values
    drive(32'h0000_0003, 32'h0000_0003, ALU_SLTU);
    #1ns;
    check(result_o == 32'h0000_0000, "Set on less than unsigned with equal values failed: 3 < 3 != 0");

  endtask


  task automatic test_shift_right_logical();

    // Test shift right logical
    drive(32'h0000_0004, 32'h0000_0002, ALU_SRL);
    #1ns;
    check(result_o == 32'h0000_0001, "Shift right logical failed: 4 >> 2 != 1");

    // Test shift right logical with zero
    drive(32'h0000_0000, 32'h0000_0003, ALU_SRL);
    #1ns;
    check(result_o == 32'h0000_0000, "Shift right logical with zero failed: 0 >> 3 != 0");

  endtask

  task automatic test_shift_right_arithmetic();

    // Test shift right arithmetic
    drive(32'hFFFF_FFFC, 32'h0000_0002, ALU_SRA);
    #1ns;
    check(result_o == 32'hFFFF_FFFF, "Shift right arithmetic failed: -4 >>> 2 != -1");

    // Test shift right arithmetic with zero
    drive(32'h0000_0000, 32'h0000_0003, ALU_SRA);
    #1ns;
    check(result_o == 32'h0000_0000, "Shift right arithmetic with zero failed: 0 >>> 3 != 0");

  endtask

  task automatic test_and();

    // Test AND
    drive(32'h0000_000F, 32'h0000_00F0, ALU_AND);
    #1ns;
    check(result_o == 32'h0000_0000, "AND failed: 0xF & 0xF0 != 0");

    // Test AND with non-zero result
    drive(32'h0000_00FF, 32'h0000_0F0F, ALU_AND);
    #1ns;
    check(result_o == 32'h0000_000F, "AND with non-zero result failed: 0xFF & 0xF0F != 0xF");

  endtask

  task automatic test_or();

    // Test OR
    drive(32'h0000_000F, 32'h0000_00F0, ALU_OR);
    #1ns;
    check(result_o == 32'h0000_00FF, "OR failed: 0xF | 0xF0 != 0xFF");

    // Test OR with zero
    drive(32'h0000_0000, 32'h0000_0000, ALU_OR);
    #1ns;
    check(result_o == 32'h0000_0000, "OR with zero failed: 0 | 0 != 0");

  endtask

  task automatic test_xor();

    // Test XOR
    drive(32'h0000_000F, 32'h0000_00F0, ALU_XOR);
    #1ns;
    check(result_o == 32'h0000_00FF,
      $sformatf("XOR failed: 0x0F ^ 0xF0 != 0xFF, got 0x%032X", result_o));

    // Test XOR with zero
    drive(32'h0000_0000, 32'h0000_0000, ALU_XOR);
    #1ns;
    check(result_o == 32'h0000_0000, "XOR with zero failed: 0 ^ 0 != 0");

  endtask


  // -- Sequence ---------------------------------------------------------
  initial begin
    void'($value$plusargs("TESTCASE=%s", testcase));

    if (selected("test_addition")) test_addition();
    if (selected("test_subtraction")) test_subtraction();
    if (selected("test_shift_left_logical")) test_shift_left_logical();
    if (selected("test_set_on_less_than")) test_set_on_less_than();
    if (selected("test_set_on_less_than_unsigned")) test_set_on_less_than_unsigned();
    if (selected("test_shift_right_logical")) test_shift_right_logical();
    if (selected("test_shift_right_arithmetic")) test_shift_right_arithmetic();
    if (selected("test_and")) test_and();
    if (selected("test_or")) test_or();
    if (selected("test_xor")) test_xor();
    
  

    if (errors != 0) begin
      $display("TEST FAILED  (%0d error(s))", errors);
      $fatal(1);
    end
    $display("TEST PASSED");
    $finish;
  end

  

endmodule

`default_nettype wire
