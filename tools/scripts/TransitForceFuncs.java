// Aggressive function discovery for Transit ELF.
// Step 1: disassemble all of blk0 code region.
// Step 2: for every instruction that's a jarl call, create a function at target.
// Step 3: for every instruction that's a function start pattern (prologue), create function.
// @category Pipeline
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.mem.MemoryBlock;
import java.util.*;

public class TransitForceFuncs extends GhidraScript {
    @Override
    public void run() throws Exception {
        AddressFactory af = currentProgram.getAddressFactory();
        FunctionManager fm = currentProgram.getFunctionManager();
        Listing L = currentProgram.getListing();
        Memory mem = currentProgram.getMemory();

        // 1) Disassemble entire blk0 range (0x01002000..end of non-FF)
        Address start = af.getDefaultAddressSpace().getAddress(0x01002000L);
        Address end = af.getDefaultAddressSpace().getAddress(0x010FFFFFL);
        println("Disassembling " + start + " to " + end);
        DisassembleCommand cmd = new DisassembleCommand(new AddressSet(start, end), null, true);
        cmd.applyTo(currentProgram, monitor);
        println("Disasm done.");

        // 2) Walk all instructions; for every jarl target, mark as function
        Set<Long> callTargets = new HashSet<>();
        InstructionIterator it = L.getInstructions(new AddressSet(start, end), true);
        while (it.hasNext()) {
            Instruction ins = it.next();
            String m = ins.getMnemonicString().toLowerCase();
            if (m.equals("jarl")) {
                Address[] flows = ins.getFlows();
                if (flows != null) for (Address f : flows) callTargets.add(f.getOffset());
            }
        }
        println("Found " + callTargets.size() + " unique call targets");

        int created = 0;
        for (long t : callTargets) {
            Address a = af.getDefaultAddressSpace().getAddress(t);
            if (fm.getFunctionAt(a) != null) continue;
            try {
                Function f = createFunction(a, null);
                if (f != null) created++;
            } catch (Exception e) {}
        }
        println("Created " + created + " functions from jarl targets");

        // 3) Also scan for common prologue: "prepare {...}" instruction
        int proCreated = 0;
        it = L.getInstructions(new AddressSet(start, end), true);
        while (it.hasNext()) {
            Instruction ins = it.next();
            if (ins.getMnemonicString().toLowerCase().startsWith("prepare")) {
                Address a = ins.getAddress();
                if (fm.getFunctionContaining(a) == null || !fm.getFunctionContaining(a).getEntryPoint().equals(a)) {
                    try {
                        Function f = createFunction(a, null);
                        if (f != null) proCreated++;
                    } catch (Exception e) {}
                }
            }
        }
        println("Created " + proCreated + " funcs from prepare prologue");
        println("Total functions: " + fm.getFunctionCount());
    }
}
