// Headless: seed call targets from a scan, disassemble, then measure decompile quality.
// @category Probe
// @runtime Java

import ghidra.app.script.GhidraScript;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.app.decompiler.*;
import ghidra.app.plugin.core.analysis.AutoAnalysisManager;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.mem.*;
import java.util.*;

public class ProbeWithSeed extends GhidraScript {
    @Override
    public void run() throws Exception {
        Memory mem = currentProgram.getMemory();
        FunctionManager fm = currentProgram.getFunctionManager();
        AddressSpace space = currentProgram.getAddressFactory().getDefaultAddressSpace();

        // Flash block: we imported at 0x01000000
        long FLASH_START = 0x01000000L;
        long FLASH_END = 0x010FFFEFL;
        Address start = space.getAddress(FLASH_START);
        Address end = space.getAddress(FLASH_END);

        // Seed 1: every 2-byte aligned offset as potential instruction start
        // (TriCore insns are 2 or 4 bytes, aligned to 2).
        AddressSet seeds = new AddressSet();
        long probes = 0;
        for (long off = FLASH_START; off < FLASH_END; off += 2) {
            Address a = space.getAddress(off);
            try {
                byte b0 = mem.getByte(a);
                byte b1 = mem.getByte(a.add(1));
                if (b0 == (byte)0xFF && b1 == (byte)0xFF) continue;
                if (b0 == 0 && b1 == 0) continue;
                seeds.addRange(a, a);
                probes++;
            } catch (MemoryAccessException e) { }
        }
        println("seeding " + probes + " candidates");

        DisassembleCommand cmd = new DisassembleCommand(seeds, null, true);
        cmd.applyTo(currentProgram, monitor);

        AutoAnalysisManager mgr = AutoAnalysisManager.getAnalysisManager(currentProgram);
        mgr.reAnalyzeAll(null);
        mgr.startAnalysis(monitor);

        int total = fm.getFunctionCount();

        // Measure decompile quality: sample 100 non-trivial functions
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);

        int sampled = 0, clean = 0, bad = 0;
        for (Function f : fm.getFunctions(true)) {
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
