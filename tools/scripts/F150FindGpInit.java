// Hunt gp/r4 initialization sequences in F150 strategy.
// Find: movhi imm_hi, r0, r4 ; followed by addi/movea imm_lo, r4, r4 (or similar pairs producing a cal-looking address).
// @category Pipeline
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.app.plugin.core.analysis.AutoAnalysisManager;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.mem.*;
import ghidra.program.model.lang.*;

public class F150FindGpInit extends GhidraScript {
    @Override
    public void run() throws Exception {
        Memory mem = currentProgram.getMemory();
        AddressSpace sp = currentProgram.getAddressFactory().getDefaultAddressSpace();
        long lo = 0x10040000L, hi = 0x101BFC00L;
        AddressSet seeds = new AddressSet();
        for (long off = lo; off < hi; off += 2) {
            Address a = sp.getAddress(off);
            try {
                byte b0 = mem.getByte(a), b1 = mem.getByte(a.add(1));
                if ((b0 == (byte)0xFF && b1 == (byte)0xFF) || (b0 == 0 && b1 == 0)) continue;
                seeds.addRange(a, a);
            } catch (MemoryAccessException e) { }
        }
        new DisassembleCommand(seeds, null, true).applyTo(currentProgram, monitor);
        AutoAnalysisManager mgr = AutoAnalysisManager.getAnalysisManager(currentProgram);
        mgr.reAnalyzeAll(null); mgr.startAnalysis(monitor);

        println("Analysis done. Funcs: " + currentProgram.getFunctionManager().getFunctionCount());

        // Scan listing for `movhi <x>, r0, r4` then `addi/movea <y>, r4, r4`
        Listing L = currentProgram.getListing();
        InstructionIterator it = L.getInstructions(true);
        int found = 0;
        Instruction prev = null;
        while (it.hasNext() && !monitor.isCancelled()) {
            Instruction ins = it.next();
            String m = ins.getMnemonicString();
            if ("movhi".equalsIgnoreCase(m)) {
                if (ins.getNumOperands() >= 3) {
                    String lastOp = ins.getDefaultOperandRepresentation(2);
                    if (lastOp != null && (lastOp.equals("gp") || lastOp.equals("r4"))) {
                        prev = ins;
                        continue;
                    }
                }
            }
            if (prev != null && ("addi".equalsIgnoreCase(m) || "movea".equalsIgnoreCase(m))) {
                String lastOp = ins.getDefaultOperandRepresentation(2);
                if (lastOp != null && (lastOp.equals("gp") || lastOp.equals("r4"))) {
                    println(String.format("  %s: %s  |  %s: %s",
                        prev.getAddress(), prev, ins.getAddress(), ins));
                    found++;
                }
            }
            prev = null;
        }
        println("Found " + found + " gp-init candidate pairs");
    }
}
