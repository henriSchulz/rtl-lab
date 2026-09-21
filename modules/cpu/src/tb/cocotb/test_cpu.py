"""cocotb tests for cpu.

SystemVerilog module cpu

Workspace:  rtl-lab
Module:     cpu
Author:     Henri Schulz <henri.schulz.bs@icloud.com>
Created:    2026-09-21 12:23  (flow 0.1.0)

This header was generated when the file was created; from here on the file
is yours.
"""

import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge

CLK_PERIOD_NS = 10


async def start_clock(dut):
    """Get the clock going."""
    cocotb.start_soon(Clock(dut.clk_i, CLK_PERIOD_NS, "ns").start())


async def reset(dut, cycles: int = 3):
    """Assert synchronously, release asynchronously."""
    dut.rst_ni.value = 0
    dut.data_i.value = 0
    dut.valid_i.value = 0
    await ClockCycles(dut.clk_i, cycles)
    await RisingEdge(dut.clk_i)
    dut.rst_ni.value = 1
    await RisingEdge(dut.clk_i)


@cocotb.test()
async def test_reset(dut):
    """After reset the outputs sit at their idle value."""
    await start_clock(dut)
    await reset(dut)

    assert dut.valid_o.value == 0, f"valid_o after reset: {dut.valid_o.value}"
    assert dut.data_o.value == 0, f"data_o after reset: {dut.data_o.value}"


@cocotb.test()
async def test_passthrough(dut):
    """Data shows up at the output one clock later."""
    await start_clock(dut)
    await reset(dut)

    width = len(dut.data_i)
    for _ in range(32):
        value = random.randrange(0, 2**width)

        dut.data_i.value = value
        dut.valid_i.value = 1
        await RisingEdge(dut.clk_i)
        dut.valid_i.value = 0
        await RisingEdge(dut.clk_i)

        assert dut.data_o.value == value, (
            f"expected {value:#x}, got {int(dut.data_o.value):#x}"
        )
        assert dut.valid_o.value == 1, "valid_o missing"
