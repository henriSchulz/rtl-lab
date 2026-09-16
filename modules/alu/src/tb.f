// ============================================================================
// tb.f  --  testbench sources (not synthesizable)
// ----------------------------------------------------------------------------
// The SystemVerilog side of verification: TB top, interfaces, assertion
// bindings, models. Classic testbenches created by `flow add tb --sv <name>`
// land here too.
//
// cocotb tests are Python and do NOT appear here -- they live in
// src/tb/cocotb/ and are listed in project.yaml under sim.modules.
// ============================================================================

+incdir+tb

// -- TB infrastructure ------------------------------------------------------
// tb/tb_pkg.sv
// tb/if_bus.sv

// -- TB top (framework: sv) -------------------------------------------------
// tb/tb_top.sv
tb/tb_alu.sv
