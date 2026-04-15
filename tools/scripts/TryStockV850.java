// Quick test: load Transit as stock V850 (not V850E3), seed entries, count clean decompiles.
// @category Pipeline
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.app.plugin.core.analysis.AutoAnalysisManager;
import ghidra.app.decompiler.*;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.mem.*;

public class TryStockV850 extends GhidraScript {
    @Override
    public void run() throws Exception {
        Memory mem = currentProgram.getMemory();
        AddressSpace space = currentProgram.getAddressFactory().getDefaultAddressSpace();
        FunctionManager fm = currentProgram.getFunctionManager();
        println("Language: " + currentProgram.getLanguage().getLanguageID());

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
        AutoAnalysisManager mgr = AutoAnalysisManager.getAnalysisManager(currentProgram);
        mgr.reAnalyzeAll(null); mgr.startAnalysis(monitor);

        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        int total=0, ok=0, warning=0, baddata=0;
        for (Function f : fm.getFunctions(true)) {
            total++;
            DecompileResults r = di.decompileFunction(f, 30, monitor);
            if (r == null || r.getDecompiledFunction() == null) continue;
            String c = r.getDecompiledFunction().getC();
            if (c.contains("halt_baddata")) baddata++;
            else if (c.contains("WARNING")) warning++;
            else ok++;
        }
        println("STOCK V850: total="+total+" ok="+ok+" warning="+warning+" baddata="+baddata);
    }
}
