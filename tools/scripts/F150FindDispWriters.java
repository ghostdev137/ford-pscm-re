// Scan for all store insns that target [gp-0x150a9] (the APA mode flag).
// Also scan insns that store immediate 3 with gp-offsets near -0x150a9.
// @category Pipeline
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;

public class F150FindDispWriters extends GhidraScript {
    @Override
    public void run() throws Exception {
        Path out = Paths.get("/tmp/pscm/f150_apa");
        StringBuilder sb = new StringBuilder();
        Listing L = currentProgram.getListing();
        FunctionManager fm = currentProgram.getFunctionManager();

        String disp = "-0x150a9";
        List<Instruction> stores = new ArrayList<>();
        InstructionIterator it = L.getInstructions(true);
        while (it.hasNext()) {
            Instruction ins = it.next();
            String m = ins.getMnemonicString().toLowerCase();
            String s = ins.toString();
            if (m.startsWith("st") && s.contains("gp") && s.contains(disp)) stores.add(ins);
        }
        sb.append("=== Stores to [gp" + disp + "] ===\n");
        Set<Function> callers = new LinkedHashSet<>();
        for (Instruction ins : stores) {
            Function f = fm.getFunctionContaining(ins.getAddress());
            if (f != null) callers.add(f);
            sb.append(String.format("  @0x%08x  %-40s  in %s\n", ins.getAddress().getOffset(), ins.toString(),
                f==null?"?":f.getName()+"@0x"+Long.toHexString(f.getEntryPoint().getOffset())));
            // Dump 10 prev instructions
            Instruction cur = ins;
            List<Instruction> back = new ArrayList<>();
            for (int i=0;i<10;i++){ Instruction p=cur.getPrevious(); if (p==null) break; back.add(p); cur=p; }
            Collections.reverse(back);
            for (Instruction p : back) sb.append(String.format("    ctx %08x  %s\n", p.getAddress().getOffset(), p.toString()));
        }

        // Decompile writers
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        for (Function f : callers) {
            try {
                DecompileResults dr = di.decompileFunction(f, 120, monitor);
                if (dr!=null && dr.getDecompiledFunction()!=null) {
                    Path p = out.resolve(String.format("modewr_%x.c", f.getEntryPoint().getOffset()));
                    Files.writeString(p, dr.getDecompiledFunction().getC());
                }
            } catch(Exception e){}
        }

        // Also decompile FUN_100bfe80 (probably memset)
        try {
            Function f = fm.getFunctionAt(toAddr(0x100bfe80L));
            if (f != null) {
                DecompileResults dr = di.decompileFunction(f, 60, monitor);
                if (dr!=null) Files.writeString(out.resolve("bfe80_memset.c"), dr.getDecompiledFunction().getC());
            }
        } catch(Exception e){}

        Files.writeString(out.resolve("_modewr.txt"), sb.toString());
        println("stores=" + stores.size() + " fns=" + callers.size());
    }
}
