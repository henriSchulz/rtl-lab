// ---------------------------------------------------------------------------
// tb_regfile.sv  --  Tests for regfile
//
//   Workspace:  rtl-lab
//   Module:     cpu
//   Author:     Henri Schulz <henri.schulz.bs@icloud.com>
//   Created:    2026-09-21 14:23  (flow 0.1.0)
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

module tb_regfile;

  localparam int unsigned Width     = 32;
  localparam int unsigned Depth     = 32;
  localparam int unsigned AddrW     = $clog2(Depth);
  localparam time         ClkPeriod = 10ns;
  localparam int unsigned Timeout   = 10_000;   // clock cycles before giving up

  logic             clk;
  logic             rst_n;
  logic [AddrW-1:0] raddr_a_i;
  logic [AddrW-1:0] raddr_b_i;
  logic [AddrW-1:0] waddr_i;
  logic [Width-1:0] wdata_i;
  logic             wen_i;
  logic [Width-1:0] rdata_a_o;
  logic [Width-1:0] rdata_b_o;
  

  int unsigned errors   = 0;
  string       testcase = "";                   // from +TESTCASE=<name>

  // -- DUT --------------------------------------------------------------
  regfile #(
      .Width (Width)
  ) dut (
      .clk_i   (clk),
      .rst_ni  (rst_n),
      .raddr_a_i (raddr_a_i),
      .raddr_b_i (raddr_b_i),
      .waddr_i  (waddr_i),
      .wdata_i  (wdata_i),
      .wen_i    (wen_i),
      .rdata_a_o (rdata_a_o),
      .rdata_b_o (rdata_b_o)
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
    $dumpvars(0, tb_regfile);
  end
`endif

  // -- Helpers ----------------------------------------------------------
  // Stimulus is driven non-blocking: the DUT samples the old value at the
  // clock edge, the new one lands afterwards. Blocking assignments right at
  // the edge would race with the design.
  task automatic reset(int unsigned cycles = 3);
    rst_n   <= 1'b0;
    raddr_a_i <= '0;
    raddr_b_i <= '0;
    waddr_i   <= '0;
    wdata_i   <= '0;
    wen_i     <= 1'b0;
    repeat (cycles) @(posedge clk);
    rst_n <= 1'b1;
    @(posedge clk);
  endtask

  task automatic write_reg(logic [AddrW-1:0] addr, logic [Width-1:0] data);
    waddr_i <= addr;
    wdata_i <= data;
    wen_i   <= 1'b1;
    @(posedge clk);
    wen_i   <= 1'b0;
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
    @(posedge clk);
    check(rdata_a_o == '0, "rdata_a_o not reset");
    check(rdata_b_o == '0, "rdata_b_o not reset");  
    
  endtask

  task automatic test_regfile();
    reset();

    @(posedge clk);

    // Write to register 5 and read it back
    write_reg(5, 32'hDEADBEEF);

   @(posedge clk);
    raddr_a_i <= 5;
    @(negedge clk);                             // let the address settle
    check(rdata_a_o == 32'hDEADBEEF, "Read back value from register 5 does not match written value");

    // Write to register 1 , then to register 2, and read both back
    write_reg(1, 32'h12345678);
    //@(posedge clk);
    write_reg(2, 32'h87654321);

    raddr_a_i <= 1;
    raddr_b_i <= 2;
    @(negedge clk);                             // let the address settle

    check(rdata_a_o == 32'h12345678, "Read back value from register 1 does not match written value");
    check(rdata_b_o == 32'h87654321, "Read back value from register 2 does not match written value");
    
    

  endtask

  // -- Sequence ---------------------------------------------------------
  initial begin
    void'($value$plusargs("TESTCASE=%s", testcase));

    if (selected("test_reset"))       test_reset();
    if (selected("test_regfile"))     test_regfile();

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
