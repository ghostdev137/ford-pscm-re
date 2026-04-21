// Transit PSCM — MDX-driven DID / routine / DTC locator.
//
// Transit stores the DID-ID array as BE u16 values starting at flash
// address 0x0100DB7C (discovered by structural scan of the firmware
// binary). The DCM dispatcher loads that base address via V850
// movhi+movea/addi, adds an index, and fetches the DID code.
//
// What this script does:
//   1. Loads DID/routine/DTC tables from analysis/transit/diagnostics/*.json.
//   2. Scans every instruction for:
//        a) direct scalar immediates matching a known code
//        b) reconstructed movhi+movea/addi 32-bit pointers pointing into
//           the DID-ID / metadata region (0x0100DB60..0x0100DC10 band)
//   3. Emits per-code and per-function summaries to /tmp/pscm/transit_mdx/.
//   4. Labels leaf handler candidates (one DID, one cmp) and bookmarks
//      the dispatcher(s).
//   5. Dumps the DID ID table from memory so the raw table layout is
//      preserved alongside the function-side evidence.
// @category Transit
// @runtime Java

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressFactory;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.listing.Listing;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.mem.MemoryAccessException;
import ghidra.program.model.scalar.Scalar;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceManager;
import ghidra.program.model.symbol.SourceType;
import ghidra.program.model.symbol.SymbolTable;

import java.io.BufferedReader;
import java.io.FileReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;

public class TransitMdxLabel extends GhidraScript {

    private static final String DIAG_DIR =
        "/Users/rossfisher/ford-pscm-re/analysis/transit/diagnostics";
    private static final String OUT_DIR = "/tmp/pscm/transit_mdx";

    // Dispatch-region band. Discovered via raw-byte scan of the AM strategy;
    // the DID ID array sits at 0x0100DB7C and the metadata that follows runs
    // to ~0x0100DD00. We widen slightly at both ends for safety.
    private static final long DISP_LO = 0x0100DB60L;
    private static final long DISP_HI = 0x0100DD00L;

    // Address where DID ID table begins (BE u16 array).
    private static final long DID_TABLE_START = 0x0100DB7CL;
    private static final int  DID_TABLE_ENTRIES = 80;  // slight overread ok

    private static class Entry {
        final long code;
        final String name;
        Entry(long c, String n) { code = c; name = n; }
    }

    private static class FuncHit {
        final Map<Long, Integer> didCounts = new LinkedHashMap<>();
        final Map<Long, Integer> routineCounts = new LinkedHashMap<>();
        final Map<Long, Integer> dtcCounts = new LinkedHashMap<>();
        final List<Long> dispRefs = new ArrayList<>();   // reconstructed ptr into DISP band
        int cmpInstrCount = 0;
        int totalInstr = 0;
    }

    // ---- JSON mini-parser (hex + name per object) -------------------------
    private List<Entry> loadEntries(String jsonPath) throws Exception {
        List<Entry> out = new ArrayList<>();
        StringBuilder sb = new StringBuilder();
        try (BufferedReader br = new BufferedReader(new FileReader(jsonPath))) {
            String line;
            while ((line = br.readLine()) != null) sb.append(line).append('\n');
        }
        String s = sb.toString();
        int i = 0;
        while ((i = s.indexOf("\"hex\"", i)) >= 0) {
            int colon = s.indexOf(':', i);
            int q1 = s.indexOf('"', colon + 1);
            int q2 = s.indexOf('"', q1 + 1);
            String hex = s.substring(q1 + 1, q2).trim();
            long code = Long.parseLong(hex.replace("0x", "").replace("0X", ""), 16);
            int nameIdx = s.indexOf("\"name\"", q2);
            String name = "?";
            if (nameIdx >= 0 && (nameIdx - q2) < 400) {
                int nc = s.indexOf(':', nameIdx);
                int nq1 = s.indexOf('"', nc + 1);
                if (nq1 >= 0 && s.charAt(nq1 - 1) != 'n') {
                    int nq2 = s.indexOf('"', nq1 + 1);
                    while (nq2 > 0 && s.charAt(nq2 - 1) == '\\') nq2 = s.indexOf('"', nq2 + 1);
                    if (nq2 > nq1) name = s.substring(nq1 + 1, nq2);
                }
            }
            out.add(new Entry(code, name));
            i = q2 + 1;
        }
        return out;
    }

    private String sanitize(String s) {
        StringBuilder out = new StringBuilder();
        for (char c : s.toCharArray()) {
            if (Character.isLetterOrDigit(c)) out.append(c);
            else if (c == ' ' || c == '/' || c == '-' || c == '_') out.append('_');
        }
        String t = out.toString().replaceAll("_+", "_").replaceAll("^_|_$", "");
        return t.length() > 60 ? t.substring(0, 60) : t;
    }

    private long firstScalar(Instruction ins) {
        for (int op = 0; op < ins.getNumOperands(); op++) {
            for (Object o : ins.getOpObjects(op)) {
                if (o instanceof Scalar) return ((Scalar) o).getUnsignedValue();
            }
        }
        return Long.MIN_VALUE;
    }

    @Override
    public void run() throws Exception {
        Files.createDirectories(Paths.get(OUT_DIR));

        List<Entry> dids     = loadEntries(DIAG_DIR + "/transit_pscm_dids.json");
        List<Entry> routines = loadEntries(DIAG_DIR + "/transit_pscm_routines.json");
        List<Entry> dtcs     = loadEntries(DIAG_DIR + "/transit_pscm_dtcs.json");

        Map<Long, Entry> didMap = new HashMap<>();
        for (Entry e : dids)     didMap.put(e.code, e);
        Map<Long, Entry> rtnMap = new HashMap<>();
        for (Entry e : routines) rtnMap.put(e.code, e);
        Map<Long, Entry> dtcMap = new HashMap<>();
        for (Entry e : dtcs)     dtcMap.put(e.code, e);

        println(String.format("Loaded %d DIDs, %d routines, %d DTCs",
            dids.size(), routines.size(), dtcs.size()));

        FunctionManager fm = currentProgram.getFunctionManager();
        Listing listing = currentProgram.getListing();
        SymbolTable syms = currentProgram.getSymbolTable();

        // ---- Dump DID table from memory --------------------------------
        Memory mem = currentProgram.getMemory();
        AddressFactory af = currentProgram.getAddressFactory();
        StringBuilder tableDump = new StringBuilder();
        tableDump.append(String.format("DID ID table @ 0x%08x (BE u16 entries):\n", DID_TABLE_START));
        Map<Long, Integer> didToTableIdx = new LinkedHashMap<>();
        for (int i = 0; i < DID_TABLE_ENTRIES; i++) {
            Address a = af.getDefaultAddressSpace().getAddress(DID_TABLE_START + i * 2L);
            try {
                int hi = mem.getByte(a) & 0xFF;
                int lo = mem.getByte(a.add(1)) & 0xFF;
                int v = (hi << 8) | lo;
                if (didMap.containsKey((long) v)) {
                    tableDump.append(String.format("  [%02d] 0x%08x  0x%04x  %s\n",
                        i, a.getOffset(), v, didMap.get((long) v).name));
                    didToTableIdx.put((long) v, i);
                } else {
                    tableDump.append(String.format("  [%02d] 0x%08x  0x%04x  (unknown)\n",
                        i, a.getOffset(), v));
                }
            } catch (MemoryAccessException ex) {
                tableDump.append(String.format("  [%02d] 0x%08x  <no-memory>\n", i, a.getOffset()));
                break;
            }
        }
        Files.writeString(Paths.get(OUT_DIR, "did_table_dump.txt"), tableDump.toString());
        println("DID table dump: " + didToTableIdx.size() + " known entries matched");

        // ---- Xrefs to DID table from Ghidra's ReferenceManager --------
        ReferenceManager rm = currentProgram.getReferenceManager();
        StringBuilder xrefOut = new StringBuilder();
        xrefOut.append("=== Ghidra-tracked xrefs TO the DID dispatch region ===\n");
        Map<Function, Integer> xrefFuncs = new LinkedHashMap<>();
        for (long a = DISP_LO; a < DISP_HI; a += 2) {
            Address addr = af.getDefaultAddressSpace().getAddress(a);
            for (Reference r : rm.getReferencesTo(addr)) {
                Address src = r.getFromAddress();
                Function f = fm.getFunctionContaining(src);
                String fname = f != null ? f.getName() : "<no-func>";
                long fentry = f != null ? f.getEntryPoint().getOffset() : 0L;
                xrefOut.append(String.format("  to=0x%08x  from=0x%08x  %s  @0x%08x  type=%s\n",
                    a, src.getOffset(), fname, fentry, r.getReferenceType()));
                if (f != null) xrefFuncs.merge(f, 1, Integer::sum);
            }
        }
        xrefOut.append("\n=== Xref summary by function ===\n");
        xrefFuncs.entrySet().stream()
            .sorted((a, b) -> Integer.compare(b.getValue(), a.getValue()))
            .forEach(e -> xrefOut.append(String.format("  %s @ 0x%08x  xrefs=%d\n",
                e.getKey().getName(), e.getKey().getEntryPoint().getOffset(), e.getValue())));
        Files.writeString(Paths.get(OUT_DIR, "xrefs_to_did_table.txt"), xrefOut.toString());
        println("Xrefs-to-table: " + xrefFuncs.size() + " functions reference the band");

        // ---- Instruction-stream-level scan for movhi+movea into DISP --
        // (Catches callers where the dispatcher isn't yet a defined function)
        StringBuilder instrScan = new StringBuilder();
        instrScan.append("=== movhi+movea/addi pairs pointing into DISP band (all instructions) ===\n");
        InstructionIterator allIt = listing.getInstructions(true);
        Instruction prevI = null;
        int globalPtrHits = 0;
        while (allIt.hasNext()) {
            if (monitor.isCancelled()) break;
            Instruction ins = allIt.next();
            if (prevI != null
                && "movhi".equalsIgnoreCase(prevI.getMnemonicString())
                && ("movea".equalsIgnoreCase(ins.getMnemonicString())
                    || "addi".equalsIgnoreCase(ins.getMnemonicString()))) {
                long hi = firstScalar(prevI);
                long lo = firstScalar(ins);
                if (hi != Long.MIN_VALUE && lo != Long.MIN_VALUE) {
                    long v = ((hi & 0xffffL) << 16) + (short) (lo & 0xffffL);
                    v &= 0xffffffffL;
                    if (DISP_LO <= v && v < DISP_HI) {
                        Function f = fm.getFunctionContaining(ins.getAddress());
                        String fn = f != null ? f.getName() : "<none>";
                        long fe = f != null ? f.getEntryPoint().getOffset() : 0L;
                        instrScan.append(String.format("  @0x%08x  movhi+%s  ptr=0x%08x  fn=%s @0x%08x\n",
                            prevI.getAddress().getOffset(), ins.getMnemonicString(), v, fn, fe));
                        globalPtrHits++;
                    }
                }
            }
            prevI = ins;
        }
        Files.writeString(Paths.get(OUT_DIR, "instr_scan_disp_ptrs.txt"), instrScan.toString());
        println("Global movhi+movea pairs into DISP: " + globalPtrHits);

        // ---- Function scan ----------------------------------------------
        Map<Function, FuncHit> hits = new LinkedHashMap<>();

        int totalFuncs = 0;
        for (Function f : fm.getFunctions(true)) {
            if (monitor.isCancelled()) break;
            totalFuncs++;
            FuncHit fh = new FuncHit();

            InstructionIterator it = listing.getInstructions(f.getBody(), true);
            Instruction prev = null;

            while (it.hasNext()) {
                Instruction ins = it.next();
                fh.totalInstr++;
                String mn = ins.getMnemonicString().toLowerCase();
                if (mn.startsWith("cmp") || mn.startsWith("subr") || mn.startsWith("tst")) {
                    fh.cmpInstrCount++;
                }

                // Direct scalar immediates
                for (int op = 0; op < ins.getNumOperands(); op++) {
                    for (Object o : ins.getOpObjects(op)) {
                        if (o instanceof Scalar) {
                            long v = ((Scalar) o).getUnsignedValue() & 0xffffffffL;
                            if (didMap.containsKey(v)) fh.didCounts.merge(v, 1, Integer::sum);
                            if (rtnMap.containsKey(v)) fh.routineCounts.merge(v, 1, Integer::sum);
                            if (dtcMap.containsKey(v)) fh.dtcCounts.merge(v, 1, Integer::sum);
                        }
                    }
                }

                // movhi + movea/addi ptr reconstruction
                if (prev != null
                    && "movhi".equalsIgnoreCase(prev.getMnemonicString())
                    && ("movea".equalsIgnoreCase(ins.getMnemonicString())
                        || "addi".equalsIgnoreCase(ins.getMnemonicString()))) {
                    long hi = firstScalar(prev);
                    long lo = firstScalar(ins);
                    if (hi != Long.MIN_VALUE && lo != Long.MIN_VALUE) {
                        long v = ((hi & 0xffffL) << 16) + (short) (lo & 0xffffL);
                        v &= 0xffffffffL;
                        if (DISP_LO <= v && v < DISP_HI) {
                            fh.dispRefs.add(v);
                        }
                        if (didMap.containsKey(v)) fh.didCounts.merge(v, 1, Integer::sum);
                        if (rtnMap.containsKey(v)) fh.routineCounts.merge(v, 1, Integer::sum);
                        if (dtcMap.containsKey(v)) fh.dtcCounts.merge(v, 1, Integer::sum);
                    }
                }

                prev = ins;
            }

            if (!fh.didCounts.isEmpty() || !fh.routineCounts.isEmpty()
                || !fh.dtcCounts.isEmpty() || !fh.dispRefs.isEmpty()) {
                hits.put(f, fh);
            }
        }
        println("Scanned " + totalFuncs + " functions; hits=" + hits.size());

        // ---- Summaries --------------------------------------------------
        Map<Long, List<Function>> didToFuncs = new TreeMap<>();
        Map<Long, List<Function>> rtnToFuncs = new TreeMap<>();
        Map<Long, List<Function>> dtcToFuncs = new TreeMap<>();

        for (Map.Entry<Function, FuncHit> e : hits.entrySet()) {
            Function f = e.getKey();
            FuncHit fh = e.getValue();
            for (Long c : fh.didCounts.keySet())     didToFuncs.computeIfAbsent(c, k -> new ArrayList<>()).add(f);
            for (Long c : fh.routineCounts.keySet()) rtnToFuncs.computeIfAbsent(c, k -> new ArrayList<>()).add(f);
            for (Long c : fh.dtcCounts.keySet())     dtcToFuncs.computeIfAbsent(c, k -> new ArrayList<>()).add(f);
        }

        // ---- DID by code ------------------------------------------------
        StringBuilder didSummary = new StringBuilder();
        didSummary.append("=== DID → functions referencing it ===\n");
        for (Entry did : dids) {
            List<Function> fs = didToFuncs.getOrDefault(did.code, List.of());
            didSummary.append(String.format("\n0x%04x  %s   (%d refs)\n",
                did.code, did.name, fs.size()));
            for (Function f : fs) {
                FuncHit fh = hits.get(f);
                int c = fh.didCounts.getOrDefault(did.code, 0);
                didSummary.append(String.format("  %s @ 0x%08x  hits=%d  total_did=%d  cmp=%d  instr=%d\n",
                    f.getName(), f.getEntryPoint().getOffset(), c,
                    fh.didCounts.size(), fh.cmpInstrCount, fh.totalInstr));
            }
        }
        Files.writeString(Paths.get(OUT_DIR, "dids_by_code.txt"), didSummary.toString());

        // ---- Dispatcher candidates --------------------------------------
        StringBuilder dispSummary = new StringBuilder();
        dispSummary.append("=== Functions referencing DID dispatch region (0x")
            .append(String.format("%08x..%08x", DISP_LO, DISP_HI))
            .append(") ===\n");
        hits.entrySet().stream()
            .filter(e -> !e.getValue().dispRefs.isEmpty())
            .sorted((a, b) -> Integer.compare(b.getValue().dispRefs.size(), a.getValue().dispRefs.size()))
            .forEach(e -> {
                Function f = e.getKey();
                FuncHit fh = e.getValue();
                dispSummary.append(String.format("\n%s @ 0x%08x  disp_refs=%d  instr=%d  cmp=%d\n",
                    f.getName(), f.getEntryPoint().getOffset(),
                    fh.dispRefs.size(), fh.totalInstr, fh.cmpInstrCount));
                for (Long r : fh.dispRefs) {
                    dispSummary.append(String.format("  ref=0x%08x\n", r));
                }
            });
        Files.writeString(Paths.get(OUT_DIR, "dispatcher_candidates.txt"), dispSummary.toString());

        // ---- Functions-by-hits ------------------------------------------
        StringBuilder funcSummary = new StringBuilder();
        funcSummary.append("=== Functions, ranked by DID breadth ===\n");
        hits.entrySet().stream()
            .sorted((a, b) -> Integer.compare(b.getValue().didCounts.size(), a.getValue().didCounts.size()))
            .limit(120)
            .forEach(e -> {
                Function f = e.getKey();
                FuncHit fh = e.getValue();
                funcSummary.append(String.format("\n%s @ 0x%08x  dids=%d  rtns=%d  dtcs=%d  dispRefs=%d  cmp=%d  instr=%d\n",
                    f.getName(), f.getEntryPoint().getOffset(),
                    fh.didCounts.size(), fh.routineCounts.size(),
                    fh.dtcCounts.size(), fh.dispRefs.size(),
                    fh.cmpInstrCount, fh.totalInstr));
                if (!fh.didCounts.isEmpty()) {
                    funcSummary.append("  DIDs: ");
                    fh.didCounts.keySet().stream().sorted().forEach(c ->
                        funcSummary.append(String.format("0x%04x ", c)));
                    funcSummary.append('\n');
                }
                if (!fh.routineCounts.isEmpty()) {
                    funcSummary.append("  RTNS: ");
                    fh.routineCounts.keySet().stream().sorted().forEach(c ->
                        funcSummary.append(String.format("0x%04x ", c)));
                    funcSummary.append('\n');
                }
            });
        Files.writeString(Paths.get(OUT_DIR, "functions_by_hits.txt"), funcSummary.toString());

        // ---- Routines ---------------------------------------------------
        StringBuilder rtnSummary = new StringBuilder();
        rtnSummary.append("=== Routine → functions ===\n");
        for (Entry r : routines) {
            List<Function> fs = rtnToFuncs.getOrDefault(r.code, List.of());
            rtnSummary.append(String.format("\n0x%04x  %s  (%d refs)\n",
                r.code, r.name, fs.size()));
            for (Function f : fs) {
                FuncHit fh = hits.get(f);
                int c = fh.routineCounts.getOrDefault(r.code, 0);
                rtnSummary.append(String.format("  %s @ 0x%08x  hits=%d  total_rtn=%d  instr=%d\n",
                    f.getName(), f.getEntryPoint().getOffset(), c,
                    fh.routineCounts.size(), fh.totalInstr));
            }
        }
        Files.writeString(Paths.get(OUT_DIR, "routines_by_code.txt"), rtnSummary.toString());

        // ---- DTCs -------------------------------------------------------
        StringBuilder dtcSummary = new StringBuilder();
        dtcSummary.append("=== DTC → functions ===\n");
        for (Entry d : dtcs) {
            List<Function> fs = dtcToFuncs.getOrDefault(d.code, List.of());
            dtcSummary.append(String.format("\n0x%04x  %s  (%d refs)\n",
                d.code, d.name, fs.size()));
            for (Function f : fs) {
                FuncHit fh = hits.get(f);
                int c = fh.dtcCounts.getOrDefault(d.code, 0);
                dtcSummary.append(String.format("  %s @ 0x%08x  hits=%d\n",
                    f.getName(), f.getEntryPoint().getOffset(), c));
            }
        }
        Files.writeString(Paths.get(OUT_DIR, "dtcs_by_code.txt"), dtcSummary.toString());

        // ---- Label application -----------------------------------------
        int labelsAdded = 0;
        int bookmarksAdded = 0;
        Set<String> usedNames = new HashSet<>();

        for (Map.Entry<Function, FuncHit> e : hits.entrySet()) {
            Function f = e.getKey();
            FuncHit fh = e.getValue();

            if (fh.didCounts.size() == 1 && fh.cmpInstrCount > 0) {
                long didCode = fh.didCounts.keySet().iterator().next();
                Entry d = didMap.get(didCode);
                if (d == null) continue;
                String base = String.format("did_%04X_%s", didCode, sanitize(d.name));
                String label = base;
                int n = 2;
                while (usedNames.contains(label)) label = base + "_" + (n++);
                usedNames.add(label);
                try {
                    syms.createLabel(f.getEntryPoint(), label, SourceType.ANALYSIS);
                    labelsAdded++;
                } catch (Exception ex) {}
            }
        }

        Set<String> usedRtn = new HashSet<>();
        for (Map.Entry<Function, FuncHit> e : hits.entrySet()) {
            Function f = e.getKey();
            FuncHit fh = e.getValue();
            if (fh.routineCounts.size() == 1 && fh.cmpInstrCount > 0 && fh.totalInstr < 2000) {
                long code = fh.routineCounts.keySet().iterator().next();
                Entry r = rtnMap.get(code);
                if (r == null) continue;
                String base = String.format("rtn_%04X_%s", code, sanitize(r.name));
                String label = base;
                int n = 2;
                while (usedRtn.contains(label)) label = base + "_" + (n++);
                usedRtn.add(label);
                try {
                    syms.createLabel(f.getEntryPoint(), label, SourceType.ANALYSIS);
                    labelsAdded++;
                } catch (Exception ex) {}
            }
        }

        // Dispatcher bookmarks
        for (Map.Entry<Function, FuncHit> e : hits.entrySet()) {
            Function f = e.getKey();
            FuncHit fh = e.getValue();
            if (!fh.dispRefs.isEmpty() || fh.didCounts.size() >= 5) {
                createBookmark(f.getEntryPoint(),
                    "MDX_DCM_DISPATCHER",
                    String.format("DCM candidate: disp_refs=%d dids=%d cmp=%d",
                        fh.dispRefs.size(), fh.didCounts.size(), fh.cmpInstrCount));
                bookmarksAdded++;
            }
        }

        println(String.format("Applied %d labels, %d bookmarks. Outputs in %s",
            labelsAdded, bookmarksAdded, OUT_DIR));

        int didsSeen = didToFuncs.size();
        int rtnsSeen = rtnToFuncs.size();
        int dtcsSeen = dtcToFuncs.size();
        int dispFns = (int) hits.values().stream().filter(fh -> !fh.dispRefs.isEmpty()).count();
        println(String.format("Coverage: DIDs %d/%d, routines %d/%d, DTCs %d/%d, disp-ref fns %d",
            didsSeen, dids.size(), rtnsSeen, routines.size(),
            dtcsSeen, dtcs.size(), dispFns));
    }
}
