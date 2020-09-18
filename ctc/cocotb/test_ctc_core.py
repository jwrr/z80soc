
import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Edge
from cocotb.triggers import FallingEdge
from cocotb.triggers import RisingEdge
from cocotb.triggers import ClockCycles
from cocotb.triggers import ReadOnly
from utils.dvtest import DVTest

from cocotb.monitors import Monitor
from cocotb.drivers import BitDriver
from cocotb.binary import BinaryValue
from cocotb.regression import TestFactory
from cocotb.scoreboard import Scoreboard

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

# Timer
#     Start on TC Load
#     Read timer
#     Start on EDGE change
#     Start on CLK_TRIG re
#     Start on CLK_TRIG fe
# Counter
#     SW decrement
#     TRIG decrement

#   input                 clk,
#   input                 reset_n,
#   input                 ce_n,
#   input                 cs,
#   input                 m1_n,
#   input                 rd_n,
#   input                 iorq_n,
#   input      [DWID-1:0] din,
#   output     [DWID-1:0] dout,
#   output                oe_n,
#   input                 iei,
#   output                ieo,
#   output                int_n,
#
#   input                 clk_trg,
#   output                zc_to


async def z80write(dut, addr, wdata):
    await RisingEdge(dut.clk)
    dut.rd_n = 1
    dut.m1_n = 1
    dut.ce_n = 0
    dut.cs   = addr;
    await RisingEdge(dut.clk)
    dut.iorq_n = 0
    dut.din = wdata
    await RisingEdge(dut.clk)
    dut.din = 0x00
    await RisingEdge(dut.clk)
    dut.iorq_n = 1
    dut.rd_n = 1
    dut.m1_n = 1
    dut.ce_n = 1
    dut.cs   = 0
    await RisingEdge(dut.clk)


async def z80read(dut, addr):
    await RisingEdge(dut.clk)
    dut.rd_n = 1
    dut.m1_n = 1
    dut.ce_n = 0
    dut.cs   = addr;
    await RisingEdge(dut.clk)
    dut.iorq_n = 0
    dut.rd_n = 0
    await RisingEdge(dut.clk)
#     await FallingEdge(dut.clk)
    await ReadOnly()
    rdata = dut.dout.value.integer
    await RisingEdge(dut.clk)
    dut.iorq_n = 1
    dut.rd_n = 1
    dut.m1_n = 1
    dut.ce_n = 1
    dut.cs   = 0
    await RisingEdge(dut.clk)
    return rdata


#### @cocotb.test()
async def run_test(dut):

    en_reg_rw_test = True

    clk = Clock(dut.clk, 10, units="ns")  # Create a 10us period clock on port clk
    cocotb.fork(clk.start())  # Start the clock

    dut.reset_n = 0

    dut.ce_n = 1
    dut.m1_n = 1
    dut.rd_n = 1
    dut.iorq_n = 1
    dut.din = 0
    dut.iei = 0
    dut.clk_trg = 0

    await ClockCycles(dut.clk,100)

    dut.reset_n = 1

    await ClockCycles(dut.clk,100)

    ### =============================================================================================================
    ### Register RW TEST

    if en_reg_rw_test:
        dv = DVTest(dut, "CTC TIMER TEST", msg_lvl="All")

        for i in range(1, 101, 10):
            await z80write(dut, 0x1, 0x05)
            await z80write(dut, 0x1, i)

        for i in range(100):
            await ClockCycles(dut.clk,100)
            rdata = await z80read(dut, 0x1)
            print("cnt = {}".format(rdata))
        dv.done()
            
    await ClockCycles(dut.clk,100)

# Register the test.
factory = TestFactory(run_test)
factory.generate_tests()


