// LCA/BlueCruise pipeline mapper for F150 PSCM
// Goal: find caller of FUN_10186afa, call order, clamps, output global
// @category Pipeline
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import ghidra.program.model.scalar.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;

public class F150LCAMap extends GhidraScript {
    @Override
    public void run() throws Exception {
        Path out = Paths.get("/tmp/pscm/f150_lca");
        Files.createDirectories(out);
        StringBuilder sb = new StringBuilder();

        AddressFactory af = currentProgram.getAddressFactory();
        AddressSpace asp = af.getDefaultAddressSpace();
        ReferenceManager rm = currentProgram.getReferenceManager();
        FunctionManager fm = currentProgram.getFunctionManager();
        Listing L = currentProgram.getListing();
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);

        // ── 1. Find callers of FUN_10186afa ─────────────────────────────────────
        long bigAddr = 0x10186afaL;
        sb.append("=== CALLERS OF FUN_10186afa ===\n");
        Address bigA = asp.getAddress(bigAddr);
        Function bigF = fm.getFunctionAt(bigA);
        if (bigF == null) {
            sb.append("  ERROR: function not found at 0x10186afa\n");
        } else {
            sb.append(String.format("  size=%d\n", bigF.getBody().getNumAddresses()));
            ReferenceIterator refs = rm.getReferencesTo(bigA);
            while (refs.hasNext()) {
                Reference r = refs.next();
                if (r.getReferenceType().isCall() || r.getReferenceType().isJump()) {
                    Function caller = fm.getFunctionContaining(r.getFromAddress());
                    sb.append(String.format("  called from 0x%08x  in %s @ 0x%x\n",
                        r.getFromAddress().getOffset(),
                        caller != null ? caller.getName() : "?",
                        caller != null ? caller.getEntryPoint().getOffset() : 0L));
                }
            }
        }

        // ── 2. Disasm scan of FUN_10186afa: calls + clamp immediates ────────────
        sb.append("\n=== FUN_10186afa CALL GRAPH (in order) ===\n");
        if (bigF != null) {
            InstructionIterator it = L.getInstructions(bigF.getBody(), true);
            // track calls in order (dedupe)
            List<Long> callTargets = new ArrayList<>();
            Set<Long> seen = new LinkedHashSet<>();
            Map<Long, Integer> clamps = new TreeMap<>();
            while (it.hasNext()) {
                Instruction ins = it.next();
                String mnem = ins.getMnemonicString().toLowerCase();
                // calls
                if (mnem.startsWith("call") || mnem.equals("jarl") || mnem.equals("jal")) {
                    Reference[] frefs = ins.getReferencesFrom();
                    for (Reference r : frefs) {
                        if (r.getReferenceType().isCall()) {
                            long t = r.getToAddress().getOffset();
                            if (!seen.contains(t)) {
                                seen.add(t);
                                callTargets.add(t);
                            }
                        }
                    }
                }
                // clamp constants: look for signed immediates in "interesting" range
                for (int op = 0; op < ins.getNumOperands(); op++) {
                    for (Object o : ins.getOpObjects(op)) {
                        if (o instanceof Scalar) {
                            long v = ((Scalar)o).getSignedValue();
                            if (Math.abs(v) >= 0x400 && Math.abs(v) <= 0x10000) {
                                clamps.merge(v, 1, Integer::sum);
                            }
                        }
                    }
                }
            }
            // print call targets with function names
            for (long t : callTargets) {
                Function f = fm.getFunctionAt(asp.getAddress(t));
                String name = f != null ? f.getName() : "?";
                long size = f != null ? f.getBody().getNumAddresses() : 0;
                sb.append(String.format("  CALL 0x%08x  %s  size=%d\n", t, name, size));
            }

            // print top clamp values
            sb.append("\n=== FUN_10186afa TOP CLAMP IMMEDIATES ===\n");
            clamps.entrySet().stream()
                .sorted((a,b)->b.getValue()-a.getValue())
                .limit(30)
                .forEach(e -> sb.append(String.format("  imm 0x%x (%d): %d times\n",
                    e.getKey(), e.getKey(), e.getValue())));

            // Writes to fef238/9/a/b/c/d range from bigF
            sb.append("\n=== FUN_10186afa WRITES TO fef2xxxx ===\n");
            Set<Long> writtenGlobals = new TreeSet<>();
            InstructionIterator it2 = L.getInstructions(bigF.getBody(), true);
            while (it2.hasNext()) {
                Instruction ins = it2.next();
                Reference[] frefs = ins.getReferencesFrom();
                for (Reference r : frefs) {
                    if (r.getReferenceType().isWrite()) {
                        long a = r.getToAddress().getOffset();
                        if (a >= 0xfef20000L && a < 0xfef30000L) writtenGlobals.add(a);
                    }
                }
            }
            sb.append(String.format("  count=%d\n", writtenGlobals.size()));
            int n = 0;
            for (long a : writtenGlobals) {
                sb.append(String.format("  0x%x\n", a));
                if (++n >= 60) { sb.append("  ... more\n"); break; }
            }
        }

        // ── 3. Decompile each of the 10 sub-functions + find their callers ─────
        long[] lcaFuncs = {
            0x101ab934L, 0x101ae572L, 0x101ac6a8L, 0x101af182L,
            0x101b000cL, 0x101ad5a4L, 0x101aaf16L, 0x101aef34L,
            0x101aa05eL, 0x101ad86cL
        };

        sb.append("\n=== LCA SUB-FUNCTION CALLERS (who calls each?) ===\n");
        for (long t : lcaFuncs) {
            Address a = asp.getAddress(t);
            Function f = fm.getFunctionAt(a);
            if (f == null) { sb.append(String.format("  0x%x: not found\n", t)); continue; }
            sb.append(String.format("\n  FUN_%08x size=%d:\n", t, f.getBody().getNumAddresses()));
            ReferenceIterator refs = rm.getReferencesTo(a);
            int cnt = 0;
            while (refs.hasNext() && cnt < 5) {
                Reference r = refs.next();
                if (r.getReferenceType().isCall() || r.getReferenceType().isJump()) {
                    Function caller = fm.getFunctionContaining(r.getFromAddress());
                    sb.append(String.format("    <- 0x%08x in %s @ 0x%x\n",
                        r.getFromAddress().getOffset(),
                        caller != null ? caller.getName() : "?",
                        caller != null ? caller.getEntryPoint().getOffset() : 0L));
                    cnt++;
                }
            }
        }

        // ── 4. Find the single-write LCA output global ─────────────────────────
        // Analogous to LKA's FUN_101a4e4a which writes _DAT_fef21a78 once.
        // We look for: any function with exactly 1 write to fef238xx..fef23dxx
        // AND also has read refs into that same range (final output)
        sb.append("\n=== CANDIDATES FOR LCA OUTPUT FUNCTION (few writes, LCA range) ===\n");
        // Re-check FUN_101ad86c for writes to LCA range
        for (long t : lcaFuncs) {
            Address a = asp.getAddress(t);
            Function f = fm.getFunctionAt(a);
            if (f == null) continue;
            Set<Long> writes = new TreeSet<>();
            InstructionIterator it3 = L.getInstructions(f.getBody(), true);
            while (it3.hasNext()) {
                Instruction ins = it3.next();
                for (Reference r : ins.getReferencesFrom()) {
                    if (r.getReferenceType().isWrite()) {
                        long addr = r.getToAddress().getOffset();
                        if (addr >= 0xfef238f0L && addr < 0xfef23d00L) writes.add(addr);
                    }
                }
            }
            // Also check for calls to Com_Send shims
            List<Long> callees = new ArrayList<>();
            InstructionIterator it4 = L.getInstructions(f.getBody(), true);
            while (it4.hasNext()) {
                Instruction ins = it4.next();
                for (Reference r : ins.getReferencesFrom()) {
                    if (r.getReferenceType().isCall()) callees.add(r.getToAddress().getOffset());
                }
            }
            sb.append(String.format("  FUN_%08x: LCA-range writes=%d, calls=%d\n",
                t, writes.size(), callees.size()));
            if (writes.size() <= 3) {
                for (long w : writes) sb.append(String.format("    writes 0x%x\n", w));
            }
        }

        // ── 5. Find functions that READ fef238xx..fef23dxx and CALL Com_Send ─
        // These are potential output writers
        sb.append("\n=== FUNCTIONS THAT READ LCA RANGE AND LOOK LIKE OUTPUT (call external xmit) ===\n");
        // look for functions with reads in LCA range but NO writes (or few writes)
        Map<Function, int[]> funcRW = new LinkedHashMap<>();
        for (long a = 0xfef238f0L; a < 0xfef23d00L; a += 2) {
            Address addr = asp.getAddress(a);
            ReferenceIterator refs = rm.getReferencesTo(addr);
            while (refs.hasNext()) {
                Reference r = refs.next();
                Function f = fm.getFunctionContaining(r.getFromAddress());
                if (f == null) continue;
                int[] rw = funcRW.computeIfAbsent(f, k -> new int[]{0,0});
                if (r.getReferenceType().isWrite()) rw[1]++;
                else rw[0]++;
            }
        }
        funcRW.entrySet().stream()
            .filter(e -> e.getValue()[1] == 0 && e.getValue()[0] >= 2) // reads but no writes
            .sorted((a,b) -> b.getValue()[0] - a.getValue()[0])
            .limit(10)
            .forEach(e -> sb.append(String.format("  %s @ 0x%x  reads=%d writes=%d size=%d\n",
                e.getKey().getName(), e.getKey().getEntryPoint().getOffset(),
                e.getValue()[0], e.getValue()[1], e.getKey().getBody().getNumAddresses())));

        // ── 6. Decompile FUN_101ad5a4 (26 writes, unknown role) ────────────────
        sb.append("\n=== FUN_101ad5a4 DECOMPILE ===\n");
        Function f101ad5a4 = fm.getFunctionAt(asp.getAddress(0x101ad5a4L));
        if (f101ad5a4 != null) {
            DecompileResults dr = di.decompileFunction(f101ad5a4, 60, monitor);
            if (dr != null && dr.getDecompiledFunction() != null) {
                sb.append(dr.getDecompiledFunction().getC());
            } else {
                sb.append("  decomp failed\n");
            }
        }

        // ── 7. Decompile FUN_101aef34 (24 writes, unknown) ────────────────────
        sb.append("\n=== FUN_101aef34 DECOMPILE ===\n");
        Function f101aef34 = fm.getFunctionAt(asp.getAddress(0x101aef34L));
        if (f101aef34 != null) {
            DecompileResults dr = di.decompileFunction(f101aef34, 60, monitor);
            if (dr != null && dr.getDecompiledFunction() != null) {
                sb.append(dr.getDecompiledFunction().getC());
            } else {
                sb.append("  decomp failed\n");
            }
        }

        // ── 8. Decompile FUN_101aaf16 (22 writes, 4x -32768) ──────────────────
        sb.append("\n=== FUN_101aaf16 DECOMPILE ===\n");
        Function f101aaf16 = fm.getFunctionAt(asp.getAddress(0x101aaf16L));
        if (f101aaf16 != null) {
            DecompileResults dr = di.decompileFunction(f101aaf16, 60, monitor);
            if (dr != null && dr.getDecompiledFunction() != null) {
                sb.append(dr.getDecompiledFunction().getC());
            } else {
                sb.append("  decomp failed\n");
            }
        }

        Files.writeString(out.resolve("_lca_map_raw.txt"), sb.toString());
        println("wrote _lca_map_raw.txt (" + sb.length() + " bytes)");
    }
}
