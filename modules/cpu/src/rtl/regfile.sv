// ---------------------------------------------------------------------------
// regfile.sv  --  RTL module regfile
//
//   Workspace:  rtl-lab
//   Module:     cpu
//   Author:     Henri Schulz <henri.schulz.bs@icloud.com>
//   Created:    2026-09-21 14:09  (flow 0.1.0)
//
// This header was generated when the file was created; from here on the
// file is yours.
// ---------------------------------------------------------------------------

`default_nettype none

module regfile #(
    parameter int unsigned Width = 32,
    parameter int unsigned Depth = 32,
    localparam int unsigned AddrW = $clog2(Depth)
) (
    input  logic             clk_i,
    input  logic             rst_ni,

    input  logic [AddrW-1:0] raddr_a_i, // rs1
    input  logic [AddrW-1:0] raddr_b_i, // rs2
    input logic [AddrW-1:0] waddr_i,    // rd
    input logic [Width-1:0] wdata_i,    // data to write
    input logic             wen_i,      // write enable

    output logic [Width-1:0] rdata_a_o, // data from rs1
    output logic [Width-1:0] rdata_b_o  // data from rs2
);



  //----------------------------------------
  // logic 
  //----------------------------------------

  logic [Width-1:0] regs [Depth-1:1];


  //----------------------------------------
  // combinational logic
  //----------------------------------------

  always_comb begin
    if(raddr_a_i == 0) begin
      rdata_a_o = '0;
    end else begin
      rdata_a_o = regs[raddr_a_i];
    end

    if(raddr_b_i == 0) begin
      rdata_b_o = '0;
    end else begin
      rdata_b_o = regs[raddr_b_i];
    end
  end


  //----------------------------------------
  // sequential logic
  //----------------------------------------

  // Register file sequential logic
  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      for (int i = 0; i < Depth; i++) begin
        regs[i] <= '0;
      end
    end else if (wen_i) begin
        regs[waddr_i] <= wdata_i;
    end
  end

endmodule

`default_nettype wire
