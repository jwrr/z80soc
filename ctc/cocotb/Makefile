TOPLEVEL ?= ctc_core
MODULE ?= test_$(TOPLEVEL)

# SRC_PATH = ./$(TOPLEVEL)
SRC_PATH = ..
SRC  = $(SRC_PATH)/src/$(TOPLEVEL).v
# SRC += ../tinyfpga_bx_usbserial/usb/*.v
VERILOG_SOURCES = $(SRC)


# If WAVES is define then add waves.v to the compile list to set $dumpvars and
# $dumpfile. Also define the vcd filename if it has not been set yet.
WAVES ?= fst
ifneq ( $(WAVES),)
  SRC += ./waves.v
  ifeq ($(WAVES),fst)
    EXTENDED_ARGS += -fst
    WAVES_OUT ?= $(TOPLEVEL).fst
  endif
  PLUSARGS += +WAVES_ON
  WAVES_OUT ?= $(TOPLEVEL).vcd
  COMPILE_ARGS += -DWAVES_OUT=\"$(WAVES_OUT)\" -s waves
endif

# DEBUG, INFO, WARNING, ERROR, CRITICAL
export COCOTB_LOG_LEVEL ?= INFO
export COCOTB_REDUCED_LOG_FMT ?= 1
SIM ?= icarus
TOPLEVEL_LANG ?= verilog

include $(shell cocotb-config --makefiles)/Makefile.sim

