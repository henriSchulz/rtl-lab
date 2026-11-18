// ---------------------------------------------------------------------------
// tb_branch_unit.sv  --  Tests for branch_unit
//
//   Workspace:  rtl-lab
//   Module:     cpu
//   Author:     Henri Schulz <henri.schulz.bs@icloud.com>
//   Created:    2026-09-21 21:08  (flow 0.1.0)
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

module tb_branch_unit;
  import cpu_pkg::*;

  localparam int unsigned Width     = 32;
  localparam time         ClkPeriod = 10ns;
  localparam int unsigned Timeout   = 10_000;   // clock cycles before giving up
  
  logic             clk;
  logic [Width-1:0] operand_a_i;
  logic [Width-1:0] operand_b_i;
  branch_op_e       branch_op_i;
  logic             branch_taken_o;



  int unsigned errors   = 0;
  string       testcase = "";                   // from +TESTCASE=<name>

  // -- DUT --------------------------------------------------------------
  branch_unit #(
      .Width (Width)
  ) dut (
    .operand_a_i(operand_a_i),
    .operand_b_i(operand_b_i),
    .branch_op_i(branch_op_i),
    .branch_taken_o(branch_taken_o)
  );

  // -- Clock ------------------------------------------------------------
  initial begin
    clk = 1'b0;
    forever #(ClkPeriod / 2) clk = ~clk;
  end

  // -- Waveform ---------------------------------------------------------
`ifdef WAVES
  initial begin
    $dumpfile(`WAVE_FILE);
    $dumpvars(0, tb_branch_unit);
  end
`endif

  // -- Helpers ----------------------------------------------------------
  // Stimulus is driven non-blocking: the DUT samples the old value at the
  // clock edge, the new one lands afterwards. Blocking assignments right at
  // the edge would race with the design.
  
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

  task automatic check_branch(string name, logic [Width-1:0] a, logic [Width-1:0] b,
                              branch_op_e op, logic expected);
    operand_a_i = a;
    operand_b_i = b;
    branch_op_i = op;
    #1ns;

    check(branch_taken_o == expected,
          $sformatf("%s (%s): expected %b, got %b", name, op.name(), expected, branch_taken_o));
  endtask

  task automatic check_all_ops(string name, logic [Width-1:0] a, logic [Width-1:0] b,
                               logic [5:0] expected);
    check_branch(name, a, b, BR_EQ,  expected[5]);
    check_branch(name, a, b, BR_NE,  expected[4]);
    check_branch(name, a, b, BR_LT,  expected[3]);
    check_branch(name, a, b, BR_GE,  expected[2]);
    check_branch(name, a, b, BR_LTU, expected[1]);
    check_branch(name, a, b, BR_GEU, expected[0]);
  endtask

  task automatic test_equal();
    check_all_ops("0 == 0",   32'h0000_0000, 32'h0000_0000, 6'b100101);
    check_all_ops("5 == 5",   32'h0000_0005, 32'h0000_0005, 6'b100101);
    check_all_ops("-1 == -1", 32'hFFFF_FFFF, 32'hFFFF_FFFF, 6'b100101);
  endtask

  task automatic test_positive();
    check_all_ops("1 vs 2", 32'h0000_0001, 32'h0000_0002, 6'b011010);
    check_all_ops("2 vs 1", 32'h0000_0002, 32'h0000_0001, 6'b010101);
  endtask

  task automatic test_mixed_sign();
    check_all_ops("-1 vs 1", 32'hFFFF_FFFF, 32'h0000_0001, 6'b011001);
    check_all_ops("1 vs -1", 32'h0000_0001, 32'hFFFF_FFFF, 6'b010110);
  endtask

  task automatic test_negative();
    check_all_ops("-2 vs -1", 32'hFFFF_FFFE, 32'hFFFF_FFFF, 6'b011010);
    check_all_ops("-1 vs -2", 32'hFFFF_FFFF, 32'hFFFF_FFFE, 6'b010101);
  endtask

  task automatic test_boundaries();
    check_all_ops("min vs max", 32'h8000_0000, 32'h7FFF_FFFF, 6'b011001);
    check_all_ops("max vs min", 32'h7FFF_FFFF, 32'h8000_0000, 6'b010110);
    check_all_ops("0 vs min",   32'h0000_0000, 32'h8000_0000, 6'b010110);
    check_all_ops("min vs 0",   32'h8000_0000, 32'h0000_0000, 6'b011001);
  endtask

  task automatic test_invalid_op();
    check_branch("invalid 010, a == b", 32'h0000_0005, 32'h0000_0005, branch_op_e'(3'b010), 1'b0);
    check_branch("invalid 011, a == b", 32'h0000_0005, 32'h0000_0005, branch_op_e'(3'b011), 1'b0);
    check_branch("invalid 010, a < b",  32'h0000_0001, 32'h0000_0002, branch_op_e'(3'b010), 1'b0);
    check_branch("invalid 011, a < b",  32'h0000_0001, 32'h0000_0002, branch_op_e'(3'b011), 1'b0);
  endtask

  


  // -- Sequence ---------------------------------------------------------
  initial begin
    void'($value$plusargs("TESTCASE=%s", testcase));

    if (selected("test_equal"))      test_equal();
    if (selected("test_positive"))   test_positive();
    if (selected("test_mixed_sign")) test_mixed_sign();
    if (selected("test_negative"))   test_negative();
    if (selected("test_boundaries")) test_boundaries();
    if (selected("test_invalid_op")) test_invalid_op();


    if (errors != 0) begin
      $display("TEST FAILED  (%0d error(s))", errors);
      $fatal(1);
    end
    $display("TEST PASSED");
    $finish;
  end

  // Emergency brake in case the design hangs.
  initial begin
    repeat (Timeout) @(posedge clk);
    $display("TEST FAILED  (timeout after %0d cycles)", Timeout);
    $fatal(1);
  end

endmodule

`default_nettype wire
