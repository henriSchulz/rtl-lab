// ---------------------------------------------------------------------------
// cpu.sv  --  SystemVerilog module cpu
//
//   Workspace:  rtl-lab
//   Module:     cpu
//   Author:     Henri Schulz <henri.schulz.bs@icloud.com>
//   Created:    2026-09-21 12:23  (flow 0.1.0)
//
// This header was generated when the file was created; from here on the
// file is yours.
// ---------------------------------------------------------------------------

`default_nettype none

module cpu #(
    parameter int unsigned Width = 8
) (
    input  logic             clk_i,
    input  logic             rst_ni,

    input  logic [Width-1:0] data_i,
    input  logic             valid_i,

    output logic [Width-1:0] data_o,
    output logic             valid_o
);

  // Placeholder behaviour: a single register stage. Replace with the real design.
  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      data_o  <= '0;
      valid_o <= 1'b0;
    end else begin
      data_o  <= data_i;
      valid_o <= valid_i;
    end
  end

endmodule

`default_nettype wire
