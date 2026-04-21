// Build a map of every resolvable RAM write in the Transit program:
//   addr -> list of (function, instruction, write-size, is-boolean-write).
//
// Goal: find the LKA override gate flag. Pattern to detect:
//   - A RAM address written with both immediate 0 and immediate 1 (flag)
//   - The containing function also reads another RAM address and does
//     integer compares against threshold constants (threshold + gate).
//
// Resolution strategy: Ghidra's ReferenceManager already tracks most
// resolved WRITE references when const-propagation figured out the
// target. We also walk instructions manually for `st.w`, `st.h`,
// `st.b`, `sst.*` with scalar displacement + known base-register value.
//
// Transit RH850 has workspace at ~0xFEDF... to 0xFEFF... (internal RAM)
// and peripheral RAM at 0xFFFE... In this firmware the LKA code writes
// to addresses in the 0xFEDF0000..0xFEFFFFFF band. We filter aggressively
// to that band to keep the output tractable.
// @category Transit
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSpace;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.listing.Listing;
import ghidra.program.model.scalar.Scalar;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceManager;
import ghidra.program.model.symbol.RefType;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;

public class TransitRamWriteMap extends GhidraScript {

    // Transit RAM workspace band (empirically the LKA state lives in
    // 0xFEDF0000..0xFEFFFFFF on RH850 Ford PSCM).
    private static final long RAM_LO = 0xFEDF0000L;
    private static final long RAM_HI = 0xFF000000L;
    private static final String OUT_DIR = "/tmp/pscm/transit_ram_map";

    // Per-address write metadata
    private static class WriteSite {
        Function fn;
        Address insAddr;
        String mnemonic;
        long immediateWritten;    // Long.MIN_VALUE when not an immediate
        int sizeBytes;             // 1 / 2 / 4
    }

    @Override
    public void run() throws Exception {
        Files.createDirectories(Paths.get(OUT_DIR));
        FunctionManager fm = currentProgram.getFunctionManager();
        Listing listing = currentProgram.getListing();
        ReferenceManager rm = currentProgram.getReferenceManager();
        AddressSpace sp = currentProgram.getAddressFactory().getDefaultAddressSpace();

        Map<Long, List<WriteSite>> writes = new TreeMap<>();
        int totalXrefs = 0;

        // Method A: Ghidra's tracked references (already-resolved writes).
        // Iterate WRITE references whose target lies in our band.
        for (long a = RAM_LO; a < RAM_HI; a += 4) {
            if (monitor.isCancelled()) break;
            Address target = sp.getAddress(a);
            for (Reference r : rm.getReferencesTo(target)) {
                if (!r.getReferenceType().isWrite()) continue;
                Function f = fm.getFunctionContaining(r.getFromAddress());
                if (f == null) continue;
                Instruction ins = listing.getInstructionAt(r.getFromAddress());
                if (ins == null) continue;
                WriteSite ws = new WriteSite();
                ws.fn = f;
                ws.insAddr = r.getFromAddress();
                ws.mnemonic = ins.getMnemonicString();
                ws.immediateWritten = extractImmediateWritten(ins);
                ws.sizeBytes = mnemonicSize(ws.mnemonic);
                writes.computeIfAbsent(a, k -> new ArrayList<>()).add(ws);
                totalXrefs++;
            }
        }
        println("Tracked writes: " + totalXrefs + " sites across "
            + writes.size() + " distinct RAM addresses");

        // ----- Gate candidate scoring -----
        // Score = 10 for both 0 AND 1 written to same address; +1 per additional writer;
        //        +5 if writers include a short function (likely leaf setter)
        Map<Long, Integer> gateScore = new HashMap<>();
        for (Map.Entry<Long, List<WriteSite>> e : writes.entrySet()) {
            Set<Long> imms = new HashSet<>();
            for (WriteSite w : e.getValue()) imms.add(w.immediateWritten);
            int score = e.getValue().size();
            if (imms.contains(0L) && imms.contains(1L)) score += 20;
            if (imms.contains(0L) && imms.contains(0xFFL)) score += 10;  // bool-byte false/true
            gateScore.put(e.getKey(), score);
        }

        // ----- Emit reports -----
        StringBuilder addrReport = new StringBuilder();
        addrReport.append("=== RAM write hotspots (sorted by gate-score) ===\n");
        List<Map.Entry<Long, Integer>> ranked = new ArrayList<>(gateScore.entrySet());
        ranked.sort((a, b) -> Integer.compare(b.getValue(), a.getValue()));
        for (Map.Entry<Long, Integer> entry : ranked) {
            if (entry.getValue() < 3) break;
            long a = entry.getKey();
            List<WriteSite> sites = writes.get(a);
            addrReport.append(String.format("\n0x%08x  score=%d  writers=%d\n",
                a, entry.getValue(), sites.size()));
            Set<Long> imms = new HashSet<>();
            for (WriteSite w : sites) imms.add(w.immediateWritten);
            if (!imms.isEmpty() && !imms.contains(Long.MIN_VALUE)) {
                StringBuilder s = new StringBuilder("  imms: ");
                for (Long imm : imms) s.append("0x").append(Long.toHexString(imm)).append(" ");
                addrReport.append(s).append('\n');
            }
            for (WriteSite w : sites) {
                addrReport.append(String.format("  @0x%08x  %s  fn=%s @0x%08x  imm=%s sz=%d\n",
                    w.insAddr.getOffset(), w.mnemonic, w.fn.getName(),
                    w.fn.getEntryPoint().getOffset(),
                    w.immediateWritten == Long.MIN_VALUE ? "?"
                        : String.format("0x%x", w.immediateWritten),
                    w.sizeBytes));
            }
        }
        Files.writeString(Paths.get(OUT_DIR, "addr_hotspots.txt"), addrReport.toString());

        // Also produce a per-function summary: how many RAM writes does each fn do?
        Map<Function, Integer> fnWrites = new HashMap<>();
        Map<Function, Set<Long>> fnTargets = new HashMap<>();
        for (List<WriteSite> sites : writes.values()) {
            for (WriteSite w : sites) {
                fnWrites.merge(w.fn, 1, Integer::sum);
                fnTargets.computeIfAbsent(w.fn, k -> new HashSet<>()).add(w.insAddr.getOffset());
            }
        }
        StringBuilder fnReport = new StringBuilder();
        fnReport.append("=== Functions by # RAM writes ===\n");
        fnWrites.entrySet().stream()
            .sorted((a, b) -> Integer.compare(b.getValue(), a.getValue()))
            .limit(60)
            .forEach(e -> fnReport.append(String.format(
                "  %s @ 0x%08x  writes=%d  distinct_targets=%d  body=%d\n",
                e.getKey().getName(), e.getKey().getEntryPoint().getOffset(),
                e.getValue(), fnTargets.get(e.getKey()).size(),
                e.getKey().getBody().getNumAddresses())));
        Files.writeString(Paths.get(OUT_DIR, "functions_by_writes.txt"), fnReport.toString());

        println("Wrote " + OUT_DIR + "/addr_hotspots.txt and functions_by_writes.txt");
    }

    private int mnemonicSize(String mn) {
        String m = mn.toLowerCase();
        if (m.endsWith(".b") || m.endsWith(".bu")) return 1;
        if (m.endsWith(".h") || m.endsWith(".hu")) return 2;
        if (m.endsWith(".w") || m.endsWith(".dw")) return 4;
        return 0;
    }

    // Attempt to extract the source-side immediate if the instruction is
    // "st.b/h/w imm, [addr]" or "mov imm, rX; st.w rX, [addr]"-ish. Very
    // coarse — covers the simple `mov 0, rX; st.h rX, disp[rY]` and
    // `mov 1, rX; st.h rX, disp[rY]` patterns inside 1 instruction by
    // looking for scalar operand matching 0 / 1 / small-int.
    private long extractImmediateWritten(Instruction ins) {
        // If the 2nd-previous instruction was a mov-imm into the source
        // register of this store, we'd need full dataflow — too expensive
        // for this first pass. Just try direct scalar operand.
        for (int op = 0; op < ins.getNumOperands(); op++) {
            for (Object o : ins.getOpObjects(op)) {
                if (o instanceof Scalar) {
                    long v = ((Scalar) o).getUnsignedValue();
                    if (v <= 0xFFFF) return v;
                }
            }
        }
        return Long.MIN_VALUE;
    }
}
