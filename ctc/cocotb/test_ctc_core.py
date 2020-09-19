
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


async def ctc_write(dut, addr, wdata):
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


async def ctc_read(dut, addr):
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


async def ctc_hw_reset(dv):
    dut = dv.dut
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


async def ctc_sw_reset(dv, din):
    dut = dv.dut
    dv.dbg("    " + "Reset Timer")
    await ctc_write(dut, 0x1, din | 0x03)


async def ctc_poll(dv, nn, din, exp, msg):
    dut = dv.dut
    dv.info("    " + msg)
    dut.din = din
    prev = 257
    for i in range(nn):
        await ClockCycles(dut.clk, 100)
        rdata = await ctc_read(dut, 0x1)
        if exp == 0:
            dv.eq(rdata, 0, "Timer should be off")
        else:
            dv.neq(rdata, prev, "Timer should be decrementing")
        prev = rdata

# =============================================================================
# =============================================================================

### ===========================================================================
### CTC TIMER TEST

async def run_ctc_timer_test(dut):

    clk = Clock(dut.clk, 10, units="ns")  # Create a 10us period clock on port clk
    cocotb.fork(clk.start())  # Start the clock
    await ClockCycles(dut.clk,2)

#   dv = DVTest(dut, "CTC TIMER TEST", msg_lvl="All")
    dv = DVTest(dut, "CTC TIMER TEST", msg_lvl="Fail")

    await ctc_hw_reset(dv)

    # Verify auto trigger (trig immediately after the time const is loaded)
    dv.notice("Test auto trigger")
    for i in range(1, 101, 10):
        await ctc_write(dut, 0x1, 0x05)
        await ctc_write(dut, 0x1, i)
    await ctc_poll(dv, 20, 0x88, -1, "After Loading Time Constant - Timer should decrement (din=0x88)")

    # Reset timer, Configure it to start on with sw edge change 
    dv.notice("Test software trigger")
    await ctc_sw_reset(dv, 0x03)
    await ctc_poll(dv, 5, 0x97, 0, "After Reset - Timer should NOT decrement (din=0x98)")
    await ctc_write(dut, 0x1, 0x0d) # control word, ext trigger
    await ctc_write(dut, 0x1, 0x80) # time constant
    await ctc_poll(dv, 5, 0x98, 0, "After loading Time Constant but before Software Trigger - Timer should NOT decrement (din=0x98)")
    await ctc_write(dut, 0x1, 0x19) # control word
    await ctc_poll(dv, 5, 0x99, -1, "After Software Trigger - Timer should decrement (din=0x99)")

    # Verify falling edge external trigger
    dv.notice("Test falling edge trigger")
    await ctc_sw_reset(dv,0x0B)
    await ctc_poll(dv, 5, 0xAA, 0, "After Reset - The timer should stay 0 (din=0xAA)")
    await ctc_write(dut, 0x1, 0x0d) # control word, ext trigger
    await ctc_write(dut, 0x1, 0x20) # time constant
    await ctc_poll(dv, 5, 0xBB, 0, "Before External Trigger - The timer should NOT decrement (din=0xBB)")

    dut.clk_trg = 1
    await ctc_poll(dv, 5, 0xCC, 0, "After Rising Edge - The timer should NOT trigger (din=0xCC)")
    
    dut.clk_trg = 0
    await ctc_poll(dv, 5, 0xDD, -1, "After Falling Edge - The timer should  trigger (din=0xDD)")
    
    # Verify rising edge external trigger
    dv.notice("Test rising edge trigger")
    await ctc_sw_reset(dv,0x1B)
    await ctc_poll(dv, 5, 0xE0, 0, "After Reset - The timer should stay 0 (din=0xE0)")
    await ctc_write(dut, 0x1, 0x1d) # control word, ext trigger
    await ctc_write(dut, 0x1, 0x20) # time constant
    await ctc_poll(dv, 5, 0xE1, 0, "Before External Trigger - The timer should NOT decrement (din=0xE1)")

    dut.clk_trg = 1
    await ctc_poll(dv, 5, 0xE2, -1, "After Rising Edge - The timer should trigger (din=0xE2)")

    dv.done()
    await ClockCycles(dut.clk, 100)
            

### ===========================================================================
### CTC COUNTER TEST

async def run_ctc_counter_test(dut):
    clk = Clock(dut.clk, 10, units="ns")  # Create a 10us period clock on port clk
    cocotb.fork(clk.start())  # Start the clock
    await ClockCycles(dut.clk,2)

#     dv = DVTest(dut, "CTC COUNTER TEST", msg_lvl="All")
    dv = DVTest(dut, "CTC COUNTER TEST", msg_lvl="Fail")

    # -------------------------------------------------------------------------
    
    await ctc_hw_reset(dv)
    dv.notice("Test software trigger")
    await ctc_sw_reset(dv, 0x73)
    await ctc_write(dut, 0x1, 0x75) # channel control word
    await ctc_write(dut, 0x1, 0x10) # time constant
    await ctc_poll(dv, 5, 0xF0, 0, "After Reset - Counter should NOT decrement (din=0xF0)")
    
    exp = 0x10
    for i in range(100):
        await ctc_write(dut, 0x1, 0x61) # channel control word
        cnt = await ctc_read(dut, 0x1)
        exp = 0xF if exp==0 else exp - 1
        dv.eq(cnt, exp, "cnt should decrement on software falling edge")
        await ctc_write(dut, 0x1, 0x71) # channel control word
        cnt = await ctc_read(dut, 0x1)
        exp = 0xF if exp==0 else exp - 1
        dv.eq(cnt, exp, "cnt should decrement on software rising edge")

    # -------------------------------------------------------------------------
    
    await ctc_hw_reset(dv)
    dv.notice("Test Rising Edge trigger")
    await ctc_sw_reset(dv, 0x73)
    await ctc_write(dut, 0x1, 0x75) # channel control word
    await ctc_write(dut, 0x1, 0x10) # time constant
    await ctc_poll(dv, 5, 0xF0, 0, "After Reset - Counter should NOT decrement (din=0xF0)")
    
    exp = 0x0
    dut.din = 0xF1
    for i in range(100):
#       await ctc_write(dut, 0x1, 0x61) # channel control word
        exp = 0xF if exp==0 else exp - 1
        dut.clk_trg = 1
        await RisingEdge(dut.clk)
        cnt = await ctc_read(dut, 0x1)
        dv.eq(cnt, exp, "cnt should decrement on clk_trg rising edge")
        dut.clk_trg = 0
        await RisingEdge(dut.clk)
        cnt = await ctc_read(dut, 0x1)
        dv.eq(cnt, exp, "cnt should NOT decrement on software falling edge")
        
    # -------------------------------------------------------------------------
    
    await ctc_hw_reset(dv)
    dv.notice("Test Falling Edge trigger")
    await ctc_sw_reset(dv, 0x63)
    await ctc_write(dut, 0x1, 0x65) # channel control word
    await ctc_write(dut, 0x1, 0x10) # time constant
    await ctc_poll(dv, 5, 0xF0, 0, "After Reset - Counter should NOT decrement (din=0xF0)")
    
    exp = 0x0
    dut.din = 0xF1
    for i in range(100):
        dut.clk_trg = 1
        await RisingEdge(dut.clk)
        cnt = await ctc_read(dut, 0x1)
        dv.eq(cnt, exp, "cnt should NOT decrement on clk_trg rising edge")
        dut.clk_trg = 0
        await RisingEdge(dut.clk)
        exp = 0xF if exp==0 else exp - 1
        cnt = await ctc_read(dut, 0x1)
        dv.eq(cnt, exp, "cnt should decrement on software falling edge")
        


    dv.done()
    await ClockCycles(dut.clk, 100)


# =============================================================================
# =============================================================================

enable_ctc_timer_test   = True
enable_ctc_counter_test = True

async def run_test_suite(dut):
    if enable_ctc_timer_test:   await run_ctc_timer_test(dut)
    if enable_ctc_counter_test: await run_ctc_counter_test(dut)

# Register the test.
factory = TestFactory(run_test_suite)
factory.generate_tests()


