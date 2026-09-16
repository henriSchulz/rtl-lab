// ---------------------------------------------------------------------------
// tb_alu.sv  --  Combinational ALU: arithmetic, logic, shift and compare
//
//   Workspace:  rtl-lab
//   Module:     alu
//   Author:     Henri Schulz <henri.schulz.bs@icloud.com>
//   Created:    2026-09-10 22:04  (rtl 0.1.0)
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

  import alu_pkg::*;

  localparam int unsigned Width   = 8;
  localparam time         Settle  = 1ns;    // let the combinational logic settle
  localparam time         Timeout = 1us;    // emergency brake

  alu_op_e          op;
  logic [Width-1:0] a;
  logic [Width-1:0] b;
  logic [Width-1:0] result;
  logic             zero;
  logic             carry;

  int unsigned errors   = 0;
  string       testcase = "";               // from +TESTCASE=<name>

  // -- DUT --------------------------------------------------------------
  alu #(
      .Width (Width)
  ) dut (
      .op_i     (op),
      .a_i      (a),
      .b_i      (b),
      .result_o (result),
      .zero_o   (zero),
      .carry_o  (carry)
  );

  // -- Waveform ---------------------------------------------------------
`ifdef WAVES
  initial begin
    $dumpfile(`WAVE_FILE);
    $dumpvars(0, tb_alu);
  end
`endif

  // -- Helpers ----------------------------------------------------------
  task automatic apply(alu_op_e operation, logic [Width-1:0] lhs,
                       logic [Width-1:0] rhs);
    op = operation;
    a  = lhs;
    b  = rhs;
    #Settle;
  endtask

  function automatic void check(bit condition, string message);
    if (!condition) begin
      errors++;
      $display("[%0t] ERROR: %s", $time, message);
    end
  endfunction

  // Compares against the expected result and reports what was seen.
  task automatic expect_result(alu_op_e operation, logic [Width-1:0] lhs,
                               logic [Width-1:0] rhs, logic [Width-1:0] expected);
    apply(operation, lhs, rhs);
    check(result === expected,
          $sformatf("%s %0h, %0h: expected %0h, got %0h",
                    operation.name(), lhs, rhs, expected, result));
  endtask

  // Without +TESTCASE everything runs, otherwise only the named test.
  function automatic bit selected(string name);
    return (testcase == "" || testcase == name);
  endfunction

  // -- Tests ------------------------------------------------------------
  task automatic test_arith();
    expect_result(ALU_ADD, 8'd10, 8'd7, 8'd17);
    check(carry === 1'b0, "unexpected carry on 10 + 7");
    check(zero === 1'b0, "unexpected zero on 10 + 7");

    expect_result(ALU_ADD, 8'hff, 8'h01, 8'h00);
    check(carry === 1'b1, "carry missing on ff + 01");
    check(zero === 1'b1, "zero missing on ff + 01");

    expect_result(ALU_SUB, 8'd10, 8'd7, 8'd3);
    check(carry === 1'b0, "unexpected borrow on 10 - 7");

    expect_result(ALU_SUB, 8'd7, 8'd10, 8'hfd);
    check(carry === 1'b1, "borrow missing on 7 - 10");
  endtask

  task automatic test_logic();
    expect_result(ALU_AND, 8'hf0, 8'h3c, 8'h30);
    expect_result(ALU_OR,  8'hf0, 8'h3c, 8'hfc);
    expect_result(ALU_XOR, 8'hf0, 8'h3c, 8'hcc);

    expect_result(ALU_XOR, 8'haa, 8'haa, 8'h00);
    check(zero === 1'b1, "zero missing on aa ^ aa");
  endtask

  task automatic test_shift();
    expect_result(ALU_SLL, 8'h01, 8'd3, 8'h08);
    expect_result(ALU_SLL, 8'h81, 8'd1, 8'h02);   // the top bit drops out
    expect_result(ALU_SRL, 8'h80, 8'd3, 8'h10);
    expect_result(ALU_SRL, 8'h01, 8'd1, 8'h00);
  endtask

  task automatic test_compare();
    expect_result(ALU_SLT, 8'd7, 8'd10, 8'd1);
    expect_result(ALU_SLT, 8'd10, 8'd7, 8'd0);
    expect_result(ALU_SLT, 8'd10, 8'd10, 8'd0);
  endtask

  // Add against a golden model, a few dozen random operand pairs.
  task automatic test_random_add();
    logic [Width-1:0] lhs;
    logic [Width-1:0] rhs;
    logic [Width:0]   expected;

    repeat (64) begin
      lhs      = Width'($urandom());
      rhs      = Width'($urandom());
      expected = {1'b0, lhs} + {1'b0, rhs};

      apply(ALU_ADD, lhs, rhs);
      check(result === expected[Width-1:0],
            $sformatf("%0h + %0h: expected %0h, got %0h",
                      lhs, rhs, expected[Width-1:0], result));
      check(carry === expected[Width],
            $sformatf("%0h + %0h: carry expected %b, got %b",
                      lhs, rhs, expected[Width], carry));
    end
  endtask

  // -- Sequence ---------------------------------------------------------
  initial begin
    void'($value$plusargs("TESTCASE=%s", testcase));

    if (selected("test_arith"))      test_arith();
    if (selected("test_logic"))      test_logic();
    if (selected("test_shift"))      test_shift();
    if (selected("test_compare"))    test_compare();
    if (selected("test_random_add")) test_random_add();

    if (errors != 0) begin
      $display("TEST FAILED  (%0d error(s))", errors);
      $fatal(1);
    end
    $display("TEST PASSED");
    $finish;
  end

  // Emergency brake in case something never returns.
  initial begin
    #Timeout;
    $display("TEST FAILED  (timeout after %0t)", Timeout);
    $fatal(1);
  end

endmodule

`default_nettype wire
