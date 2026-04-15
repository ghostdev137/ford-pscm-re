// LCA pipeline chain: decompile wrappers, find execution order, output global
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

public class F150LCAChain extends GhidraScript {
    @Override
    public void run() throws Exception {
        Path out = Paths.get("/tmp/pscm/f150_lca");
        Files.createDirectories(out);
        StringBuilder sb = new StringBuilder();

        AddressFactory af = currentProgram.getAddressFactory();
        AddressSpace asp = af.getDefaultAddressSpace();
        FunctionManager fm = currentProgram.getFunctionManager();
        ReferenceManager rm = currentProgram.getReferenceManager();
        Listing L = currentProgram.getListing();
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);

        // Decompile the top-level LCA task caller (calls FUN_10186afa)
        long[] toDecompile = {
            0x101a392aL,   // calls FUN_10186afa
            0x101aa042L,   // calls FUN_101ab934 (RX unpacker)
            0x101aa026L,   // calls FUN_101aa05e
            0x101a9fa2L,   // calls FUN_101ad86c and FUN_101aef34
            0x101aa034L,   // might be the chain dispatcher (find it)
            0x101aa380L,   // calls FUN_101ac6a8 and FUN_101aaf16
            0x101aa34eL,   // calls FUN_101b000c
            0x101ad020L,   // calls FUN_101af182, FUN_101ae572, FUN_101ad5a4
            // Also decompile the small output-read functions
            0x101aa530L,
            0x101aa5a4L,
            0x101aa66eL,
            0x101aa626L,
        };

        for (long t : toDecompile) {
            Address a = asp.getAddress(t);
            Function f = fm.getFunctionAt(a);
            if (f == null) {
                sb.append(String.format("\n// NO FUNCTION AT 0x%08x\n", t));
                continue;
            }
            sb.append(String.format("\n// === FUN_%08x size=%d ===\n", t, f.getBody().getNumAddresses()));
            // show callers
            sb.append("// CALLERS:\n");
            ReferenceIterator refs = rm.getReferencesTo(a);
            int n = 0;
            while (refs.hasNext() && n < 5) {
                Reference r = refs.next();
                if (r.getReferenceType().isCall() || r.getReferenceType().isJump()) {
                    Function caller = fm.getFunctionContaining(r.getFromAddress());
                    sb.append(String.format("//   from 0x%08x in %s @ 0x%x\n",
                        r.getFromAddress().getOffset(),
                        caller != null ? caller.getName() : "?",
                        caller != null ? caller.getEntryPoint().getOffset() : 0L));
                    n++;
                }
            }
            DecompileResults dr = di.decompileFunction(f, 60, monitor);
            if (dr != null && dr.getDecompiledFunction() != null) {
                sb.append(dr.getDecompiledFunction().getC());
            } else {
                sb.append("// decomp failed\n");
            }
        }

        // Also: find caller of FUN_101a392a to get the full LCA task root
        sb.append("\n\n// === CALLERS OF FUN_101a392a ===\n");
        Address a392a = asp.getAddress(0x101a392aL);
        ReferenceIterator refs392a = rm.getReferencesTo(a392a);
        while (refs392a.hasNext()) {
            Reference r = refs392a.next();
            if (r.getReferenceType().isCall() || r.getReferenceType().isJump()) {
                Function caller = fm.getFunctionContaining(r.getFromAddress());
                sb.append(String.format("//   from 0x%08x in %s @ 0x%x  size=%d\n",
                    r.getFromAddress().getOffset(),
                    caller != null ? caller.getName() : "?",
                    caller != null ? caller.getEntryPoint().getOffset() : 0L,
                    caller != null ? caller.getBody().getNumAddresses() : 0));
            }
        }

        // Decompile FUN_10186a86 (the last call in big function, size=42)
        sb.append("\n// === FUN_10186a86 (last call in 10186afa, possible output) ===\n");
        Function f86 = fm.getFunctionAt(asp.getAddress(0x10186a86L));
        if (f86 != null) {
            DecompileResults dr = di.decompileFunction(f86, 60, monitor);
            if (dr != null && dr.getDecompiledFunction() != null)
                sb.append(dr.getDecompiledFunction().getC());
            else sb.append("// decomp failed\n");
        }

        // Decompile FUN_100bfbc4 and FUN_100bf8e6 (output-like, called from big func)
        for (long t : new long[]{0x100bfbc4L, 0x100bf8e6L, 0x100bf7c8L}) {
            Function f = fm.getFunctionAt(asp.getAddress(t));
            if (f == null) continue;
            sb.append(String.format("\n// === FUN_%08x size=%d ===\n", t, f.getBody().getNumAddresses()));
            DecompileResults dr = di.decompileFunction(f, 60, monitor);
            if (dr != null && dr.getDecompiledFunction() != null)
                sb.append(dr.getDecompiledFunction().getC());
            else sb.append("// decomp failed\n");
        }

        // Scan FUN_101aef34 for Com_Send calls / output globals
        // Also: find what FUN_10097c28 is (called from 101aef34 with torque arg)
        sb.append("\n// === FUN_10097c28 (called from FUN_101aef34 with final torque) ===\n");
        Function fc28 = fm.getFunctionAt(asp.getAddress(0x10097c28L));
        if (fc28 != null) {
            sb.append(String.format("// size=%d\n", fc28.getBody().getNumAddresses()));
            DecompileResults dr = di.decompileFunction(fc28, 30, monitor);
            if (dr != null && dr.getDecompiledFunction() != null)
                sb.append(dr.getDecompiledFunction().getC());
            else sb.append("// decomp failed\n");
            // Callers
            sb.append("// CALLERS of FUN_10097c28:\n");
            ReferenceIterator refs = rm.getReferencesTo(fc28.getEntryPoint());
            int cnt = 0;
            while (refs.hasNext() && cnt < 10) {
                Reference r = refs.next();
                if (r.getReferenceType().isCall()) {
                    Function caller = fm.getFunctionContaining(r.getFromAddress());
                    sb.append(String.format("//   0x%08x in %s @ 0x%x\n",
                        r.getFromAddress().getOffset(),
                        caller != null ? caller.getName() : "?",
                        caller != null ? caller.getEntryPoint().getOffset() : 0L));
                    cnt++;
                }
            }
        }

        // Find functions writing to LCA range with EXACTLY 1 write (output writer candidate)
        sb.append("\n// === SINGLE-WRITE LCA GLOBAL CANDIDATES ===\n");
        // Scan fef238f0..fef23d00 for addresses with only 1 writer function
        Map<Long, Set<Function>> writers = new TreeMap<>();
        for (long addr = 0xfef238f0L; addr < 0xfef23d00L; addr += 2) {
            Address a2 = asp.getAddress(addr);
            ReferenceIterator refs = rm.getReferencesTo(a2);
            while (refs.hasNext()) {
                Reference r = refs.next();
                if (r.getReferenceType().isWrite()) {
                    Function wf = fm.getFunctionContaining(r.getFromAddress());
                    if (wf != null) {
                        writers.computeIfAbsent(addr, k -> new HashSet<>()).add(wf);
                    }
                }
            }
        }
        // Find globals written by exactly 1 function, and that function is NOT 10186afa
        long bigEntry = 0x10186afaL;
        int shown = 0;
        for (Map.Entry<Long, Set<Function>> e : writers.entrySet()) {
            Set<Function> wfuncs = e.getValue();
            if (wfuncs.size() == 1) {
                Function wf = wfuncs.iterator().next();
                if (wf.getEntryPoint().getOffset() != bigEntry) {
                    sb.append(String.format("  Global 0x%x: sole writer=%s @ 0x%x\n",
                        e.getKey(), wf.getName(), wf.getEntryPoint().getOffset()));
                    shown++;
                    if (shown >= 30) { sb.append("  ... more\n"); break; }
                }
            }
        }

        Files.writeString(out.resolve("_lca_chain.txt"), sb.toString());
        println("wrote _lca_chain.txt (" + sb.length() + " bytes)");
    }
}
