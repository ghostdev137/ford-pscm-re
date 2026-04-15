// Delete auto-functions sitting on 0xFFFF flash padding, clear listing,
// re-run analysis, then dump clean decompiles.
// @category Pipeline
// @runtime Java

import ghidra.app.script.GhidraScript;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.app.plugin.core.analysis.AutoAnalysisManager;
import ghidra.app.decompiler.*;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.mem.*;
import ghidra.program.model.symbol.SourceType;
import java.io.*;
import java.nio.file.*;
import java.util.*;

public class CleanupPaddingFuncs extends GhidraScript {
    @Override
    public void run() throws Exception {
        Memory mem = currentProgram.getMemory();
        Listing listing = currentProgram.getListing();
        FunctionManager fm = currentProgram.getFunctionManager();
        AddressSpace space = currentProgram.getAddressFactory().getDefaultAddressSpace();

        // Seed: every non-padding halfword as a disassembly start
        long FLASH_LO = 0x01000000L, FLASH_HI = 0x010FFFEFL;
        AddressSet seeds = new AddressSet();
        for (long off = FLASH_LO; off < FLASH_HI; off += 2) {
            Address a = space.getAddress(off);
            try {
                byte b0 = mem.getByte(a), b1 = mem.getByte(a.add(1));
                if ((b0 == (byte)0xFF && b1 == (byte)0xFF) || (b0 == 0 && b1 == 0)) continue;
                seeds.addRange(a, a);
            } catch (MemoryAccessException e) { }
        }
        new DisassembleCommand(seeds, null, true).applyTo(currentProgram, monitor);
        AutoAnalysisManager mgr0 = AutoAnalysisManager.getAnalysisManager(currentProgram);
        mgr0.reAnalyzeAll(null); mgr0.startAnalysis(monitor);
        println("Seed+initial-analysis done; funcs=" + fm.getFunctionCount());

        int deletedFuncs = 0, clearedRanges = 0;
        List<Function> toDelete = new ArrayList<>();
        for (Function f : fm.getFunctions(true)) {
            Address entry = f.getEntryPoint();
            try {
                byte b0 = mem.getByte(entry);
                byte b1 = mem.getByte(entry.add(1));
                byte b2 = mem.getByte(entry.add(2));
                byte b3 = mem.getByte(entry.add(3));
                // Entry is 0xFFFF padding OR 0x0000
                if ((b0 == (byte)0xFF && b1 == (byte)0xFF && b2 == (byte)0xFF && b3 == (byte)0xFF) ||
                    (b0 == 0 && b1 == 0 && b2 == 0 && b3 == 0)) {
                    toDelete.add(f);
                }
            } catch (MemoryAccessException e) { }
        }
        for (Function f : toDelete) {
            fm.removeFunction(f.getEntryPoint());
            deletedFuncs++;
        }
        println("Deleted " + deletedFuncs + " padding-entry functions");

        // Find runs of 0xFFFF >= 16 bytes, clear code units there
        long FLASH_START = 0x01000000L, FLASH_END = 0x01100000L;
        long runStart = -1;
        for (long off = FLASH_START; off < FLASH_END; off++) {
            Address a = space.getAddress(off);
            byte b;
            try { b = mem.getByte(a); } catch (MemoryAccessException e) { runStart = -1; continue; }
            if (b == (byte)0xFF) {
                if (runStart < 0) runStart = off;
            } else {
                if (runStart >= 0 && off - runStart >= 16) {
                    Address s = space.getAddress(runStart);
                    Address e = space.getAddress(off - 1);
                    try {
                        listing.clearCodeUnits(s, e, false);
                        clearedRanges++;
                    } catch (Exception ex) { }
                }
                runStart = -1;
            }
        }
        println("Cleared " + clearedRanges + " padding runs");

        // Re-run analysis
        AutoAnalysisManager mgr = AutoAnalysisManager.getAnalysisManager(currentProgram);
        mgr.reAnalyzeAll(null);
        mgr.startAnalysis(monitor);
        println("Re-analysis done");

        // Dump clean decompiles
        Path outDir = Paths.get("/tmp/pscm/decompiles_clean2");
        Files.createDirectories(outDir);
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);

        int dumped = 0, skippedSmall = 0, skippedBad = 0, total = 0;
        for (Function f : fm.getFunctions(true)) {
            total++;
            if (f.getBody().getNumAddresses() < 40) { skippedSmall++; continue; }
            DecompileResults r = di.decompileFunction(f, 30, monitor);
            if (r == null || r.getDecompiledFunction() == null) { skippedBad++; continue; }
            String code = r.getDecompiledFunction().getC();
            if (code.contains("halt_baddata") || code.contains("WARNING: Bad")) { skippedBad++; continue; }
            String addr = String.format("%08x", f.getEntryPoint().getOffset());
            Files.writeString(outDir.resolve(addr + ".c"), code);
            dumped++;
        }
        println("DUMP total=" + total + " dumped=" + dumped + " small=" + skippedSmall + " bad=" + skippedBad);
        println("output: " + outDir);
    }
}
