// Decompile functions whose body contains 0x3A8 raw bytes, using patched RH850 decoder.
// @category Probe
// @runtime Java

import ghidra.app.script.GhidraScript;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.app.plugin.core.analysis.AutoAnalysisManager;
import ghidra.app.decompiler.*;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.mem.*;
import java.util.*;

public class Dump3A8Funcs extends GhidraScript {
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

        /* Find all 0x3A8 byte hits */
        List<Long> hits = new ArrayList<>();
        byte b0 = (byte)0xA8, b1 = (byte)0x03;
        for (long off = FLASH_START; off < FLASH_END; off += 2) {
            try {
                if (mem.getByte(space.getAddress(off)) == b0 &&
                    mem.getByte(space.getAddress(off+1)) == b1) hits.add(off);
            } catch (Exception e) { }
        }
        FunctionManager fm = currentProgram.getFunctionManager();
        /* Which functions contain hits now */
        Map<Function, Integer> fc = new LinkedHashMap<>();
        for (long h : hits) {
            Function f = fm.getFunctionContaining(space.getAddress(h));
            if (f != null) fc.merge(f, 1, Integer::sum);
        }
        println("After patch: " + fc.size() + " functions contain 0x3A8 bytes (out of " + hits.size() + " total hits)");

        List<Map.Entry<Function,Integer>> sorted = new ArrayList<>(fc.entrySet());
        sorted.sort((a,b) -> Integer.compare(b.getValue(), a.getValue()));

        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        int dumped = 0;
        for (Map.Entry<Function,Integer> e : sorted) {
            if (dumped >= 3) break;
            Function f = e.getKey();
            DecompileResults r = di.decompileFunction(f, 30, monitor);
            if (r == null || r.getDecompiledFunction() == null) continue;
            String code = r.getDecompiledFunction().getC();
            if (code.contains("halt_baddata")) continue;  // skip still-broken
            println("\n===== " + f.getName() + " @ " + f.getEntryPoint() +
                    " (" + e.getValue() + " 0x3A8 hits, " + f.getBody().getNumAddresses() + " B) =====");
            String[] lines = code.split("\n");
            for (int i = 0; i < Math.min(60, lines.length); i++) println(lines[i]);
            dumped++;
        }
        if (dumped == 0) {
            println("No clean decompiles found among 3A8-containing functions; dumping BEST effort (even halt_baddata):");
            for (Map.Entry<Function,Integer> e : sorted) {
                if (dumped >= 2) break;
                Function f = e.getKey();
                DecompileResults r = di.decompileFunction(f, 30, monitor);
                if (r == null || r.getDecompiledFunction() == null) continue;
                println("\n===== " + f.getName() + " @ " + f.getEntryPoint() +
                    " (" + e.getValue() + " 0x3A8 hits, " + f.getBody().getNumAddresses() + " B) =====");
                String[] lines = r.getDecompiledFunction().getC().split("\n");
                for (int i = 0; i < Math.min(40, lines.length); i++) println(lines[i]);
                dumped++;
            }
        }
    }
}
