// Dump callers of FUN_10092bc4 and check for immediate 3 passed in r8 (param_3).
// @category Pipeline
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;

public class F150APACallers extends GhidraScript {
    @Override
    public void run() throws Exception {
        Path out = Paths.get("/tmp/pscm/f150_apa");
        StringBuilder sb = new StringBuilder();
        Listing L = currentProgram.getListing();
        FunctionManager fm = currentProgram.getFunctionManager();
        AddressFactory af = currentProgram.getAddressFactory();
        ReferenceManager rm = currentProgram.getReferenceManager();

        Address tgt = af.getDefaultAddressSpace().getAddress(0x10092bc4L);
        Function tgtF = fm.getFunctionAt(tgt);
        sb.append("target: " + tgtF + "\n");

        ReferenceIterator refs = rm.getReferencesTo(tgt);
        Set<Function> callers = new LinkedHashSet<>();
        while (refs.hasNext()) {
            Reference r = refs.next();
            if (!r.getReferenceType().isCall()) continue;
            Function c = fm.getFunctionContaining(r.getFromAddress());
            sb.append(String.format("  call @0x%08x from %s\n",
                r.getFromAddress().getOffset(),
                c == null ? "?" : c.getName() + "@0x" + Long.toHexString(c.getEntryPoint().getOffset())));
            if (c != null) callers.add(c);
        }

        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        for (Function f : callers) {
            sb.append(String.format("\n=== caller %s @0x%x ===\n", f.getName(), f.getEntryPoint().getOffset()));
            try {
                DecompileResults dr = di.decompileFunction(f, 120, monitor);
                if (dr != null && dr.getDecompiledFunction() != null) {
                    String c = dr.getDecompiledFunction().getC();
                    Path p = out.resolve(String.format("caller_%x.c", f.getEntryPoint().getOffset()));
                    Files.writeString(p, c);
                    sb.append("  wrote " + p.getFileName() + "\n");
                    // excerpt lines containing FUN_10092bc4
                    for (String line : c.split("\n")) {
                        if (line.contains("10092bc4")) sb.append("  " + line.trim() + "\n");
                    }
                }
            } catch (Exception e) { sb.append("  err " + e + "\n"); }
        }
        Files.writeString(out.resolve("_callers.txt"), sb.toString());
        println("callers=" + callers.size());
    }
}
