// Dump selected Transit jump tables and summarize target functions.
// @category Pipeline
// @runtime Java
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;

public class TransitJumpTableProbe extends GhidraScript {
    private static class TableSpec {
        final long insn;
        final long base;
        final int entries;
        final int scale;
        final String name;
        TableSpec(long insn, long base, int entries, int scale, String name) {
            this.insn = insn;
            this.base = base;
            this.entries = entries;
            this.scale = scale;
            this.name = name;
        }
    }

    private static final TableSpec[] TABLES = {
        new TableSpec(0x010CE636L, 0x010CE638L, 6, 2, "ce636_state_dispatch"),
        new TableSpec(0x010B4A0EL, 0x010B4A10L, 5, 2, "b4a0e_dispatch"),
        new TableSpec(0x010B4AD4L, 0x010B4AD6L, 5, 2, "b4ad4_dispatch"),
        new TableSpec(0x010B4B10L, 0x010B4B12L, 5, 2, "b4b10_dispatch"),
        new TableSpec(0x010BF258L, 0x010BF25EL, 3, 2, "bf258_to_b4caa"),
    };

    @Override
    public void run() throws Exception {
        DecompInterface ifc = new DecompInterface();
        ifc.openProgram(currentProgram);

        for (TableSpec spec : TABLES) {
            println(String.format("== %s insn=0x%08x base=0x%08x entries=%d scale=%d ==",
                spec.name, spec.insn, spec.base, spec.entries, spec.scale));
            for (int i = 0; i < spec.entries; i++) {
                Address slot = toAddr(spec.base + i * 2L);
                short rel = currentProgram.getMemory().getShort(slot);
                long targetOff = spec.base + i * 2L + ((long) rel * spec.scale);
                Address target = toAddr(targetOff);
                Function f = getFunctionContaining(target);
                Instruction ins = getInstructionAt(target);
                println(String.format("[%d] slot=%s rel=%d target=%s func=%s",
                    i,
                    slot,
                    (int) rel,
                    target,
                    f == null ? "(none)" :
                        f.getEntryPoint().toString() + " " + f.getName() + " size=" + f.getBody().getNumAddresses()));

                if (ins == null) {
                    println("  no instruction at target");
                } else {
                    println("  first instructions:");
                    InstructionIterator it = currentProgram.getListing().getInstructions(target, true);
                    for (int n = 0; n < 6 && it.hasNext(); n++) {
                        Instruction cur = it.next();
                        println(String.format("    %s  %s", cur.getAddress(), cur));
                    }
                }

                if (f != null) {
                    println("  callers:");
                    for (Function caller : f.getCallingFunctions(monitor)) {
                        println(String.format("    %s %s size=%d",
                            caller.getEntryPoint(), caller.getName(), caller.getBody().getNumAddresses()));
                    }
                    DecompileResults res = ifc.decompileFunction(f, 30, monitor);
                    if (res != null && res.decompileCompleted() && res.getDecompiledFunction() != null) {
                        String[] lines = res.getDecompiledFunction().getC().split("\n");
                        println("  decompile:");
                        for (int n = 0; n < Math.min(lines.length, 16); n++) {
                            println("    " + lines[n]);
                        }
                    } else if (res != null) {
                        println("  decompile failed: " + res.getErrorMessage());
                    }
                }
            }
            println("");
        }
    }
}
