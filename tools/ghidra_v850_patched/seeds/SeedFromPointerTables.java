// Seed functions from pointer tables embedded in flash.
//
// Transit AUTOSAR builds keep large arrays of function pointers (Rte_*,
// Dem_*, Dcm_*, ISR dispatch) in rodata regions. These are prime
// function-start candidates that Ghidra's Function Start Search
// analyzer often misses because the callsites go through indirect
// loads rather than direct `jarl` relocations.
//
// This script walks every 4-byte-aligned word in the code/flash image,
// accepts values that fall inside executable memory blocks, and
// creates function starts at those addresses (if not already seeded).
// Applies a simple sanity filter: the target's first byte must be
// even (V850 instructions are 2-byte aligned) and the address must
// be inside a block marked executable.
//
// Usage: run as post-script after import. Idempotent.
// @category Transit
// @runtime Java

import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.app.cmd.function.CreateFunctionCmd;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSpace;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.mem.MemoryAccessException;
import ghidra.program.model.mem.MemoryBlock;

import java.util.HashSet;
import java.util.Set;

public class SeedFromPointerTables extends GhidraScript {

    // Only accept pointer values inside these executable flash bands.
    // Extend here when adding memory blocks for block2 / SBL.
    private static final long[][] EXEC_BANDS = {
        { 0x01000000L, 0x01100000L },   // strategy
        { 0x20FF0000L, 0x21050000L },   // block2 extended
        { 0x00F9C000L, 0x00FD0000L },   // SBL bootloader (if loaded)
    };

    private boolean isExecutableTarget(long va) {
        for (long[] band : EXEC_BANDS) {
            if (va >= band[0] && va < band[1]) return true;
        }
        return false;
    }

    @Override
    public void run() throws Exception {
        Memory mem = currentProgram.getMemory();
        FunctionManager fm = currentProgram.getFunctionManager();
        AddressSpace sp = currentProgram.getAddressFactory().getDefaultAddressSpace();
        Set<Long> seen = new HashSet<>();

        long scanned = 0, candidates = 0, seeded = 0, skippedExisting = 0, skippedOddAlign = 0;

        for (MemoryBlock blk : mem.getBlocks()) {
            if (!blk.isInitialized()) continue;
            long startOff = blk.getStart().getOffset();
            long endOff = blk.getEnd().getOffset();
            if (endOff - startOff > 0x01000000L) continue;  // skip huge blocks
            for (long a = startOff; a + 4 <= endOff; a += 4) {
                if (monitor.isCancelled()) break;
                scanned++;
                Address src = sp.getAddress(a);
                int v;
                try {
                    // Little-endian 32-bit value
                    int b0 = mem.getByte(src) & 0xFF;
                    int b1 = mem.getByte(src.add(1)) & 0xFF;
                    int b2 = mem.getByte(src.add(2)) & 0xFF;
                    int b3 = mem.getByte(src.add(3)) & 0xFF;
                    v = b0 | (b1 << 8) | (b2 << 16) | (b3 << 24);
                } catch (MemoryAccessException ex) {
                    continue;
                }
                long va = ((long) v) & 0xFFFFFFFFL;
                if (!isExecutableTarget(va)) continue;
                candidates++;
                if ((va & 1) != 0) { skippedOddAlign++; continue; }
                if (seen.contains(va)) continue;
                seen.add(va);

                Address target = sp.getAddress(va);
                Function existing = fm.getFunctionAt(target);
                if (existing != null) { skippedExisting++; continue; }

                // Disassemble then create function.
                DisassembleCommand dc = new DisassembleCommand(target, null, true);
                dc.applyTo(currentProgram, monitor);
                CreateFunctionCmd cfc = new CreateFunctionCmd(target);
                if (cfc.applyTo(currentProgram, monitor)) {
                    seeded++;
                    if ((seeded % 200) == 0) {
                        println(String.format("seeded %d (scanned %d candidates=%d)",
                            seeded, scanned, candidates));
                    }
                }
            }
        }

        println(String.format(
            "SeedFromPointerTables: scanned=%d candidates=%d seeded=%d existing=%d oddAlign=%d",
            scanned, candidates, seeded, skippedExisting, skippedOddAlign));
    }
}
