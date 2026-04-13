// Find all Transit functions referencing 0x3A8 / 0x3CA / 0x213 via instruction
// scalar operand OR raw byte inside function body.
// @category Probe
// @runtime Java

import ghidra.app.script.GhidraScript;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.app.plugin.core.analysis.AutoAnalysisManager;
import ghidra.app.decompiler.*;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.mem.*;
import ghidra.program.model.scalar.Scalar;
import java.util.*;

public class HuntLKA2 extends GhidraScript {
    @Override
    public void run() throws Exception {
        Memory mem = currentProgram.getMemory();
        AddressSpace space = currentProgram.getAddressFactory().getDefaultAddressSpace();
        long FLASH_START = 0x01000000L, FLASH_END = 0x010FFFEFL;

        /* Seed + analyze */
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

        FunctionManager fm = currentProgram.getFunctionManager();
        Listing listing = currentProgram.getListing();
        int[] canIds = {0x3A8, 0x3CA, 0x213};
        String[] names = {"0x3A8 (APA)", "0x3CA (LKA)", "0x213 (DesTorq)"};

        /* Gather function scalar operand matches */
        for (int i = 0; i < canIds.length; i++) {
            Map<Function, Integer> counts = new LinkedHashMap<>();
            int id = canIds[i];
            for (Function f : fm.getFunctions(true)) {
                int hits = 0;
                InstructionIterator it = listing.getInstructions(f.getBody(), true);
                while (it.hasNext()) {
                    Instruction ins = it.next();
                    for (int op = 0; op < ins.getNumOperands(); op++) {
                        for (Object o : ins.getOpObjects(op)) {
                            if (o instanceof Scalar && ((Scalar)o).getUnsignedValue() == id) hits++;
                        }
                    }
                }
                if (hits > 0) counts.put(f, hits);
            }
            List<Map.Entry<Function,Integer>> sorted = new ArrayList<>(counts.entrySet());
            sorted.sort((a,b) -> Integer.compare(b.getValue(), a.getValue()));
            println("\n=== " + names[i] + ": " + counts.size() + " functions match ===");
            int shown = 0;
            for (Map.Entry<Function,Integer> e : sorted) {
                if (shown++ >= 20) break;
                Function f = e.getKey();
                println(String.format("  %3dx %s @ 0x%08X (size=%d)",
                    e.getValue(), f.getName(), f.getEntryPoint().getOffset(), f.getBody().getNumAddresses()));
            }
        }
    }
}
