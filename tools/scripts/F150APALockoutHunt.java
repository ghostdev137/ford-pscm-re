// Hunt F150 APA lockout: find all store instructions with displacement -0x15083 relative to gp.
// That's the same slot the shim FUN_100978d4 reads. Whoever writes it with immediate 0x3 = overspeed lockout.
// @category Pipeline
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.scalar.Scalar;
import java.io.*;
import java.nio.file.*;
import java.util.*;

public class F150APALockoutHunt extends GhidraScript {
    @Override
    public void run() throws Exception {
        Path out = Paths.get("/tmp/pscm/f150_apa");
        Files.createDirectories(out);
        StringBuilder sb = new StringBuilder();
        Listing L = currentProgram.getListing();
        FunctionManager fm = currentProgram.getFunctionManager();

        String DISP = "-0x15083";  // displacement we care about
        List<Instruction> writes = new ArrayList<>();
        // Iterate ALL instructions across text segment
        InstructionIterator it = L.getInstructions(true);
        while (it.hasNext()) {
            Instruction ins = it.next();
            String m = ins.getMnemonicString().toLowerCase();
            if (!m.startsWith("st")) continue;
            String s = ins.toString();
            if (!s.contains("gp")) continue;
            if (!s.contains(DISP)) continue;
            writes.add(ins);
        }
        sb.append("=== Stores to [gp" + DISP + "] ===\n");
        Set<Function> fns = new LinkedHashSet<>();
        for (Instruction ins : writes) {
            Function f = fm.getFunctionContaining(ins.getAddress());
            if (f != null) fns.add(f);
            sb.append(String.format("  @0x%08x  %-40s  in %s\n",
                ins.getAddress().getOffset(), ins.toString(),
                f == null ? "?" : f.getName() + "@0x" + Long.toHexString(f.getEntryPoint().getOffset())));
        }

        // For each write site, dump 12 preceding instructions for context
        sb.append("\n=== Context around each store ===\n");
        for (Instruction ins : writes) {
            Address a = ins.getAddress();
            sb.append(String.format("\n-- @0x%08x --\n", a.getOffset()));
            Instruction cur = ins;
            List<Instruction> back = new ArrayList<>();
            for (int i = 0; i < 12; i++) {
                Instruction p = cur.getPrevious();
                if (p == null) break;
                back.add(p); cur = p;
            }
            Collections.reverse(back);
            for (Instruction p : back) sb.append(String.format("  %08x  %s\n", p.getAddress().getOffset(), p.toString()));
            sb.append(String.format(">>%08x  %s\n", ins.getAddress().getOffset(), ins.toString()));
        }

        // Decompile each writer
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        for (Function f : fns) {
            try {
                DecompileResults dr = di.decompileFunction(f, 90, monitor);
                if (dr != null && dr.getDecompiledFunction() != null) {
                    Path p = out.resolve(String.format("lockout_%x.c", f.getEntryPoint().getOffset()));
                    Files.writeString(p, dr.getDecompiledFunction().getC());
                }
            } catch (Exception e) {}
        }

        Files.writeString(out.resolve("_lockout_hunt.txt"), sb.toString());
        println("writers=" + writes.size() + " fns=" + fns.size());
    }
}
