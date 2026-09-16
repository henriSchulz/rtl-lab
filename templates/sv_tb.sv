// ---------------------------------------------------------------------------
// tb_{{name}}.sv  --  {{description}}
//
//   Workspace:  {{workspace}}
//   Module:     {{module}}
//   Author:     {{creator}}
//   Created:    {{date}} {{time}}  ({{tool}})
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

module tb_{{name}};

  localparam int unsigned Width     = 8;
  localparam time         ClkPeriod = 10ns;
  localparam int unsigned Timeout   = 10_000;   // clock cycles before giving up

  logic             clk;
  logic             rst_n;
  logic [Width-1:0] data_i;
  logic             valid_i;
  logic [Width-1:0] data_o;
  logic             valid_o;

  int unsigned errors   = 0;
  string       testcase = "";                   // from +TESTCASE=<name>

  // -- DUT --------------------------------------------------------------
  {{name}} #(
      .Width (Width)
  ) dut (
      .clk_i   (clk),
      .rst_ni  (rst_n),
      .data_i  (data_i),
      .valid_i (valid_i),
      .data_o  (data_o),
      .valid_o (valid_o)
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
    $dumpvars(0, tb_{{name}});
  end
`endif

  // -- Helpers ----------------------------------------------------------
  // Stimulus is driven non-blocking: the DUT samples the old value at the
  // clock edge, the new one lands afterwards. Blocking assignments right at
  // the edge would race with the design.
  task automatic reset(int unsigned cycles = 3);
    rst_n   <= 1'b0;
    data_i  <= '0;
    valid_i <= 1'b0;
    repeat (cycles) @(posedge clk);
    rst_n <= 1'b1;
    @(posedge clk);
  endtask

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
  task automatic test_reset();
    reset();
    @(negedge clk);                             // look away from the edge
    check(valid_o === 1'b0, $sformatf("valid_o after reset: %b", valid_o));
    check(data_o === '0, $sformatf("data_o after reset: %0h", data_o));
  endtask

  task automatic test_passthrough();
    logic [Width-1:0] value;
    reset();
    repeat (32) begin
      value = Width'($urandom());

      @(posedge clk);
      data_i  <= value;
      valid_i <= 1'b1;
      @(posedge clk);                           // the DUT samples here
      data_i  <= '0;
      valid_i <= 1'b0;

      @(negedge clk);
      check(data_o === value, $sformatf("expected %0h, got %0h", value, data_o));
      check(valid_o === 1'b1, "valid_o missing");
    end
  endtask

  // -- Sequence ---------------------------------------------------------
  initial begin
    void'($value$plusargs("TESTCASE=%s", testcase));

    if (selected("test_reset"))       test_reset();
    if (selected("test_passthrough")) test_passthrough();

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
