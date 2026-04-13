// Dump every clean-decompiling function to /tmp/pscm/decompiles_clean/<addr>.c
// Skip stubs (<40B) and skip functions whose decompile contains halt_baddata/WARNING.
// @category Pipeline
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

public class DumpDecomps extends GhidraScript {
    @Override
    public void run() throws Exception {
        Memory mem = currentProgram.getMemory();
        AddressSpace space = currentProgram.getAddressFactory().getDefaultAddressSpace();
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
        new DisassembleCommand(seeds, null, true).applyTo(currentProgram, monitor);
        AutoAnalysisManager mgr = AutoAnalysisManager.getAnalysisManager(currentProgram);
        mgr.reAnalyzeAll(null); mgr.startAnalysis(monitor);

        Path outDir = Paths.get("/tmp/pscm/decompiles_clean");
        Files.createDirectories(outDir);

        FunctionManager fm = currentProgram.getFunctionManager();
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);

        int dumped = 0, skipped_small = 0, skipped_bad = 0, total = 0;
        for (Function f : fm.getFunctions(true)) {
            total++;
            if (f.getBody().getNumAddresses() < 40) { skipped_small++; continue; }
            DecompileResults r = di.decompileFunction(f, 30, monitor);
            if (r == null || r.getDecompiledFunction() == null) { skipped_bad++; continue; }
            String code = r.getDecompiledFunction().getC();
            if (code.contains("halt_baddata") || code.contains("WARNING: Bad")) { skipped_bad++; continue; }
            String addr = String.format("%08x", f.getEntryPoint().getOffset());
            Path p = outDir.resolve(addr + ".c");
            Files.writeString(p, code);
            dumped++;
        }
        println("DUMP total=" + total + " dumped=" + dumped + " small=" + skipped_small + " bad=" + skipped_bad);
        println("output: " + outDir);
    }
}
