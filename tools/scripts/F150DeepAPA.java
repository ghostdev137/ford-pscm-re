// Deep-dive F150 APA: decompile flag-readers + verify patch encoding + trace more
// @category Pipeline
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.app.plugin.assembler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import ghidra.program.model.mem.Memory;
import java.io.*;
import java.nio.file.*;
import java.util.*;

public class F150DeepAPA extends GhidraScript {
    @Override
    public void run() throws Exception {
        Path out = Paths.get("/tmp/pscm/f150_apa");
        StringBuilder sb = new StringBuilder();
        Listing L = currentProgram.getListing();
        FunctionManager fm = currentProgram.getFunctionManager();
        ReferenceManager rm = currentProgram.getReferenceManager();
        Memory mem = currentProgram.getMemory();
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);

        // Decompile flag readers + neighbors + trace through
        long[] toDec = {
            0x1005cb10L,  // flag A reader
            0x1005cb26L,  // flag B reader
            0x100a7838L,  // lockout writer (again for completeness)
            0x10092c8aL,  // dispatcher
            0x100bfe80L,  // memset
            0x10092b4aL,  // normal-path populator
            0x100906fcL,  // fallback reader
        };
        for (long a : toDec) {
            Function f = fm.getFunctionAt(toAddr(a));
            if (f == null) { sb.append(String.format("no func @%08x\n", a)); continue; }
            try {
                DecompileResults dr = di.decompileFunction(f, 120, monitor);
                if (dr != null && dr.getDecompiledFunction() != null) {
                    String c = dr.getDecompiledFunction().getC();
                    Path p = out.resolve(String.format("deep_%x.c", a));
                    Files.writeString(p, c);
                    sb.append(String.format("wrote deep_%x.c (%d B)\n", a, c.length()));
                }
            } catch (Exception e) { sb.append("err " + a + ": " + e + "\n"); }
        }

        // For FUN_1005cb10 and FUN_1005cb26, also dump disassembly (small funcs)
        for (long a : new long[]{0x1005cb10L, 0x1005cb26L}) {
            Function f = fm.getFunctionAt(toAddr(a));
            if (f == null) continue;
            sb.append(String.format("\n=== disasm %s @%x ===\n", f.getName(), a));
            InstructionIterator it = L.getInstructions(f.getBody(), true);
            while (it.hasNext()) {
                Instruction ins = it.next();
                sb.append(String.format("  %08x  %s\n", ins.getAddress().getOffset(), ins.toString()));
            }
        }

        // Verify patch byte encoding using Ghidra assembler
        sb.append("\n=== Assembler verification ===\n");
        try {
            Assembler asm = Assemblers.getAssembler(currentProgram);
            String[] tries = {"nop", "mov 0x1, r18", "mov 1, r18"};
            for (String s : tries) {
                try {
                    byte[] b = asm.assembleLine(toAddr(0x100a7858L), s);
                    StringBuilder hex = new StringBuilder();
                    for (byte x : b) hex.append(String.format("%02x ", x & 0xff));
                    sb.append(String.format("  %-20s -> %s\n", s, hex.toString().trim()));
                } catch (Exception e) { sb.append(String.format("  %-20s -> err %s\n", s, e.getMessage())); }
            }
        } catch (Exception e) { sb.append("assembler err: " + e + "\n"); }

        // Also scan for any OTHER speed-related checks that might run in parallel — look for
        // writers of gp-0xc59d (mirror of 0x150a9) and callers of FUN_100a7838
        sb.append("\n=== Callers of FUN_100a7838 (lockout writer) ===\n");
        ReferenceIterator refs = rm.getReferencesTo(toAddr(0x100a7838L));
        while (refs.hasNext()) {
            Reference r = refs.next();
            if (!r.getReferenceType().isCall()) continue;
            Function c = fm.getFunctionContaining(r.getFromAddress());
            sb.append(String.format("  @%08x from %s\n", r.getFromAddress().getOffset(),
                c==null?"?":c.getName()+"@0x"+Long.toHexString(c.getEntryPoint().getOffset())));
        }

        // Find file offset of patch site
        sb.append("\n=== Patch site file offsets (strat blk0 @ 0x10040000) ===\n");
        long base = 0x10040000L;
        long[] sites = {0x100a7852L, 0x100a7858L, 0x100a785cL};
        for (long s : sites) sb.append(String.format("  0x%08x -> blk0 +0x%x\n", s, s - base));

        Files.writeString(out.resolve("_deep.txt"), sb.toString());
        println("deep dump done");
    }
}
