// Add blk1+blk2 memory blocks before seeding, then probe.
// @category Probe
// @runtime Java

import ghidra.app.script.GhidraScript;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.app.plugin.core.analysis.AutoAnalysisManager;
import ghidra.app.decompiler.*;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.mem.*;
import java.io.*;
import java.nio.file.*;

public class ProbeWithBanks extends GhidraScript {
    @Override
    public void run() throws Exception {
        Memory mem = currentProgram.getMemory();
        AddressSpace space = currentProgram.getAddressFactory().getDefaultAddressSpace();

        /* Add blk1 and blk2 as memory blocks loaded from file */
        long[][] extras = {
            { 0x00FD0000L, 65520L, -1L }, /* cal */
            { 0x10000400L, 3072L, -1L },
            { 0x20FF0000L, 327680L, -1L }
        };
        String[] paths = {
            "/tmp/pscm/Transit_AH.bin",
            "/tmp/pscm/transit_AH_blk1_0x10000400.bin",
            "/tmp/pscm/transit_AH_blk2_0x20FF0000.bin"
        };
        int startTxId = currentProgram.startTransaction("load blocks");
        try {
            for (int i = 0; i < extras.length; i++) {
                long base = extras[i][0];
                Address a = space.getAddress(base);
                if (mem.getBlock(a) != null) continue;  /* already loaded */
                byte[] data = Files.readAllBytes(Paths.get(paths[i]));
                MemoryBlock blk = mem.createInitializedBlock(
                    "blk_" + Long.toHexString(base), a, data.length, (byte)0, monitor, false);
                mem.setBytes(a, data);
                blk.setExecute(true); blk.setRead(true); blk.setWrite(false);
                println("loaded blk 0x" + Long.toHexString(base) + " (" + data.length + " B)");
            }
        } finally { currentProgram.endTransaction(startTxId, true); }

        /* Seed halfwords in the large flash block (blk0) */
        long FLASH_START = 0x01000000L, FLASH_END = 0x010FFFEFL;
        AddressSet seeds = new AddressSet();
        for (long off = FLASH_START; off < FLASH_END; off += 2) {
            Address a = space.getAddress(off);
            try {
                byte b0 = mem.getByte(a), b1 = mem.getByte(a.add(1));
                if ((b0 == (byte)0xFF && b1 == (byte)0xFF) || (b0 == 0 && b1 == 0)) continue;
                seeds.addRange(a, a);
            } catch (MemoryAccessException e) { }
        }
        println("seeding " + seeds.getNumAddresses() + " candidates");
        new DisassembleCommand(seeds, null, true).applyTo(currentProgram, monitor);

        AutoAnalysisManager mgr = AutoAnalysisManager.getAnalysisManager(currentProgram);
        mgr.reAnalyzeAll(null); mgr.startAnalysis(monitor);

        int total = currentProgram.getFunctionManager().getFunctionCount();
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);

        int sampled = 0, clean = 0, bad = 0;
        for (Function f : currentProgram.getFunctionManager().getFunctions(true)) {
            if (sampled >= 100) break;
            if (f.getBody().getNumAddresses() < 40) continue;
            sampled++;
            DecompileResults r = di.decompileFunction(f, 30, monitor);
            if (r == null || r.getDecompiledFunction() == null) { bad++; continue; }
            String code = r.getDecompiledFunction().getC();
            if (code.contains("halt_baddata") || code.contains("WARNING: Bad")) bad++;
            else clean++;
        }
        println("RESULT total_fns=" + total + " sampled=" + sampled + " clean=" + clean + " bad=" + bad);
    }
}
