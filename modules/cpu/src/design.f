// ============================================================================
// design.f  --  synthesizable RTL sources
// ----------------------------------------------------------------------------
// Order: packages -> interfaces -> leaf modules -> top.
// Only files that also go through synthesis. Nothing from src/tb/.
// ============================================================================

+incdir+rtl

// -- Packages ---------------------------------------------------------------
// rtl/pkg_common.sv
rtl/cpu_pkg.sv

// -- Modules ----------------------------------------------------------------
// rtl/fifo.sv
rtl/alu.sv

// -- Top --------------------------------------------------------------------
// rtl/top.sv
rtl/cpu.sv


rtl/regfile.sv
rtl/imm_gen.sv
rtl/branch_unit.sv
