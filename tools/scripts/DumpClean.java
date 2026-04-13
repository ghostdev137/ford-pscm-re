// Dump a clean decompile to verify quality
// @category Probe
// @runtime Java

import ghidra.app.script.GhidraScript;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.app.decompiler.*;
import ghidra.app.plugin.core.analysis.AutoAnalysisManager;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.mem.*;

public class DumpClean extends GhidraScript {
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
        mgr.reAnalyzeAll(null);
        mgr.startAnalysis(monitor);

        FunctionManager fm = currentProgram.getFunctionManager();
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);

        int dumped = 0;
        for (Function f : fm.getFunctions(true)) {
            if (dumped >= 3) break;
            if (f.getBody().getNumAddresses() < 100) continue;
            DecompileResults r = di.decompileFunction(f, 30, monitor);
            if (r == null || r.getDecompiledFunction() == null) continue;
            String code = r.getDecompiledFunction().getC();
            if (code.contains("halt_baddata") || code.contains("WARNING")) continue;
            println("====== " + f.getName() + " @ " + f.getEntryPoint() + " (" + f.getBody().getNumAddresses() + " B) ======");
            println(code);
            dumped++;
        }
    }
}
