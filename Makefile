PYTHON ?= python3
GHIDRA_LIFT ?= $(PYTHON) tools/ghidra_lift_regression.py

TRANSIT_BLOCK0 ?= firmware/Transit_2025/decompressed/AM/block0_strategy.bin
F150_ELF ?= firmware/F150_2021_Lariat_BlueCruise/f150_pscm_full.elf

.PHONY: lift-check transit-lift-check f150-lift-check

lift-check:
	$(GHIDRA_LIFT) --transit-block0 $(TRANSIT_BLOCK0) --f150-elf $(F150_ELF)

transit-lift-check:
	$(GHIDRA_LIFT) --transit-block0 $(TRANSIT_BLOCK0) --skip-f150

f150-lift-check:
	$(GHIDRA_LIFT) --f150-elf $(F150_ELF) --skip-transit
