// Hunt Transit APA lockout: find functions matching the F150 fingerprint:
//  - Call two small functions (jarl x2)
//  - Compare against small imms (1, 0)
//  - End with TWO st.b writing SAME register to TWO different [gp] displacements (the mirror pattern)
// @category Pipeline
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.lang.Register;
import ghidra.program.model.scalar.Scalar;
import java.io.*;
import java.nio.file.*;
import java.util.*;

public class TransitAPAHunt extends GhidraScript {
    @Override
    public void run() throws Exception {
        Path out = Paths.get("/tmp/pscm/transit_apa");
        Files.createDirectories(out);
        StringBuilder sb = new StringBuilder();
        Listing L = currentProgram.getListing();
        FunctionManager fm = currentProgram.getFunctionManager();

        int total = 0;
        int candidates = 0;
        List<String> hits = new ArrayList<>();

        // Iterate functions
        for (Function f : fm.getFunctions(true)) {
            total++;
            if (f.getBody() == null) continue;
            long size = f.getBody().getMaxAddress().getOffset() - f.getEntryPoint().getOffset();
            if (size > 200 || size < 16) continue; // small function

            InstructionIterator it = L.getInstructions(f.getBody(), true);
            int jarlCount = 0;
            List<long[]> gpStoresBList = new ArrayList<>(); // [addr, disp, regIdx]
            while (it.hasNext()) {
                Instruction ins = it.next();
                String m = ins.getMnemonicString().toLowerCase();
                if (m.equals("jarl")) jarlCount++;
                if (m.equals("st.b") || m.equals("sst.b")) {
                    String rep = ins.toString();
                    if (rep.contains("[gp]") || rep.contains(",gp]")) {
                        // parse displacement as scalar from operand 1 (second)
                        long disp = 0;
                        int regIdx = -1;
                        try {
                            Object[] ops0 = ins.getOpObjects(0); // source reg
                            Object[] ops1 = ins.getOpObjects(1); // [disp, gp]
                            for (Object o : ops0) if (o instanceof Register) regIdx = ((Register)o).getOffset();
                            for (Object o : ops1) if (o instanceof Scalar) disp = ((Scalar)o).getSignedValue();
                        } catch (Exception e) {}
                        gpStoresBList.add(new long[]{ins.getAddress().getOffset(), disp, regIdx});
                    }
                }
            }
            // Look for TWO st.b with SAME regIdx but DIFFERENT disps
            for (int i = 0; i < gpStoresBList.size(); i++) {
                for (int j = i + 1; j < gpStoresBList.size(); j++) {
                    long[] a = gpStoresBList.get(i);
                    long[] b = gpStoresBList.get(j);
                    if (a[2] == b[2] && a[2] >= 0 && a[1] != b[1]
                        && Math.abs(a[0] - b[0]) <= 24   // within 24 bytes
                        && jarlCount >= 2) {
                        candidates++;
                        String line = String.format("%s @0x%x  jarls=%d  stB(r%d)@0x%x [gp%s0x%x]  stB@0x%x [gp%s0x%x]\n",
                            f.getName(), f.getEntryPoint().getOffset(), jarlCount, a[2],
                            a[0], a[1]<0?"-":"+", Math.abs(a[1]),
                            b[0], b[1]<0?"-":"+", Math.abs(b[1]));
                        hits.add(line);
                        sb.append(line);
                    }
                }
            }
        }
        sb.insert(0, String.format("total funcs=%d, candidates=%d\n\n", total, candidates));

        // Decompile the top candidates
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        Set<String> seen = new HashSet<>();
        for (String h : hits) {
            String name = h.split(" @")[0];
            if (!seen.add(name)) continue;
            // Parse entry addr from line
            int idx = h.indexOf("@0x");
            int end = h.indexOf("  ", idx);
            long addr = Long.parseLong(h.substring(idx + 3, end), 16);
            Function f = fm.getFunctionAt(toAddr(addr));
            if (f == null) continue;
            try {
                DecompileResults dr = di.decompileFunction(f, 90, monitor);
                if (dr != null && dr.getDecompiledFunction() != null) {
                    Path p = out.resolve(String.format("cand_%x.c", addr));
                    Files.writeString(p, dr.getDecompiledFunction().getC());
                }
            } catch (Exception e) {}
        }

        Files.writeString(out.resolve("_hunt.txt"), sb.toString());
        println("total=" + total + " candidates=" + candidates);
    }
}
