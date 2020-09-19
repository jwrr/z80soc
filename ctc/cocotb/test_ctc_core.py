
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


async def timer_reset(dv, din):
    dut = dv.dut
    dv.info("Reset Timer")
    await z80write(dut, 0x1, din | 0x03)

async def timer_poll(dv, nn, din, msg):
    dut = dv.dut
    dv.info(msg)
    dut.din = din
    for i in range(nn):
        await ClockCycles(dut.clk, 100)
        rdata = await z80read(dut, 0x1)
        dv.info("Read Timer - cnt = {}".format(rdata))

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

        # Verify auto trigger (trig immediately after the time const is loaded)
        dv.info("Test auto trigger")
        for i in range(1, 101, 10):
            await z80write(dut, 0x1, 0x05)
            await z80write(dut, 0x1, i)
        await timer_poll(dv, 20, 0x88, "After Loading Time Constant - Timer should decrement (din=0x88)")

        # Reset timer, Configure it to start on with sw edge change 
        dv.info("Test software trigger")
        await timer_reset(dv, 0x03)
        await timer_poll(dv, 5, 0x97, "After Reset - Timer should NOT decrement (din=0x98)")
        await z80write(dut, 0x1, 0x0d) # control word, ext trigger
        await z80write(dut, 0x1, 0x80) # time constant
        await timer_poll(dv, 5, 0x98, "After loading Time Constant but before Software Trigger - Timer should NOT decrement (din=0x98)")
        await z80write(dut, 0x1, 0x19) # control word
        await timer_poll(dv, 5, 0x99, "After Software Trigger - Timer should decrement (din=0x99)")

        # Verify falling edge external trigger
        dv.info("Test falling edge trigger")
        await timer_reset(dv,0x0B)
        await timer_poll(dv, 5, 0xAA, "After Reset - The timer should stay 0 (din=0xAA)")
        await z80write(dut, 0x1, 0x0d) # control word, ext trigger
        await z80write(dut, 0x1, 0x20) # time constant
        await timer_poll(dv, 5, 0xBB, "Before External Trigger - The timer should NOT decrement (din=0xBB)")

        dut.clk_trg = 1
        await timer_poll(dv, 5, 0xCC, "After Rising Edge - The timer should NOT trigger (din=0xCC)")
        
        dut.clk_trg = 0
        await timer_poll(dv, 5, 0xDD, "After Falling Edge - The timer should  trigger (din=0xDD)")
        
        # Verify rising edge external trigger
        dv.info("Test rising edge trigger")
        await timer_reset(dv,0x1B)
        await timer_poll(dv, 5, 0xE0, "After Reset - The timer should stay 0 (din=0xE0)")
        await z80write(dut, 0x1, 0x1d) # control word, ext trigger
        await z80write(dut, 0x1, 0x20) # time constant
        await timer_poll(dv, 5, 0xE1, "Before External Trigger - The timer should NOT decrement (din=0xE1)")

        dut.clk_trg = 1
        await timer_poll(dv, 5, 0xE2, "After Rising Edge - The timer should trigger (din=0xE2)")
        
        
        dv.done()
            
    await ClockCycles(dut.clk, 100)

# Register the test.
factory = TestFactory(run_test)
factory.generate_tests()


