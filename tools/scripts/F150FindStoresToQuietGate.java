// Find every store instruction with a displacement that matches the
// quiet-gate RAM struct (0xfef26300..0xfef263fe). The reads in
// FUN_101a3b84 use `ld.h/ld.hu disp[rX]` where rX was loaded with a
// base pointer near 0xfef26300 — the writers likely use identical
// addressing. Ghidra's ReferenceManager doesn't track them because
// const-prop never resolved the base register.
//
// We work around that by matching only the displacement: any store
// with displacement in 0x6300..0x63FF is a candidate. Reads with that
// disp are expected (one per read site in the gate); anything else is
// a potential writer. Report writers separately.
// @category Transit
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.listing.Listing;
import ghidra.program.model.scalar.Scalar;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.Map;

public class F150FindStoresToQuietGate extends GhidraScript {
    @Override
    public void run() throws Exception {
        String outDir = "/tmp/pscm/f150_quietgate_writers";
        Files.createDirectories(Paths.get(outDir));
        FunctionManager fm = currentProgram.getFunctionManager();
        Listing listing = currentProgram.getListing();
        // Quiet-gate struct: 0x6300..0x63FF — ONE byte aligned, covers all fields
        long band_lo = 0x6300, band_hi = 0x6400;
        StringBuilder writes = new StringBuilder();
        StringBuilder reads  = new StringBuilder();
        Map<Function, Integer> writerFnCount = new HashMap<>();
        int nW = 0, nR = 0;
        InstructionIterator it = listing.getInstructions(true);
        while (it.hasNext()) {
            if (monitor.isCancelled()) break;
            Instruction ins = it.next();
            String mn = ins.getMnemonicString().toLowerCase();
            boolean isStore = mn.startsWith("st.") || mn.startsWith("sst");
            boolean isLoad = mn.startsWith("ld.") || mn.startsWith("sld");
            if (!isStore && !isLoad) continue;
            // look for a signed scalar in 0x6300..0x63FF
            Long hit = null;
            for (int op = 0; op < ins.getNumOperands(); op++) {
                for (Object o : ins.getOpObjects(op)) {
                    if (o instanceof Scalar) {
                        long v = ((Scalar) o).getSignedValue();
                        if (v < 0) v = ((Scalar) o).getUnsignedValue();
                        if (v >= band_lo && v < band_hi) { hit = v; break; }
                    }
                }
                if (hit != null) break;
            }
            if (hit == null) continue;
            Function f = fm.getFunctionContaining(ins.getAddress());
            String fn = f != null ? f.getName() : "<none>";
            long fe = f != null ? f.getEntryPoint().getOffset() : 0L;
            String line = String.format("  @0x%08x  %-12s  disp=0x%04x  fn=%s @0x%08x\n",
                ins.getAddress().getOffset(), ins.toString(), hit, fn, fe);
            if (isStore) {
                writes.append(line);
                nW++;
                if (f != null) writerFnCount.merge(f, 1, Integer::sum);
            } else {
                reads.append(line);
                nR++;
            }
        }
        StringBuilder out = new StringBuilder();
        out.append(String.format("=== Quiet-gate struct stores (potential writers) — %d sites ===\n", nW));
        out.append(writes);
        out.append(String.format("\n=== Writer function summary ===\n"));
        writerFnCount.entrySet().stream()
            .sorted((a, b) -> Integer.compare(b.getValue(), a.getValue()))
            .forEach(e -> out.append(String.format("  %s @ 0x%08x  stores=%d  body=%d\n",
                e.getKey().getName(), e.getKey().getEntryPoint().getOffset(),
                e.getValue(), e.getKey().getBody().getNumAddresses())));
        out.append(String.format("\n=== Quiet-gate struct loads (expected = reads from FUN_101a3b84) — %d sites ===\n", nR));
        out.append(reads);
        Files.writeString(Paths.get(outDir, "stores.txt"), out.toString());
        println("writes=" + nW + "  reads=" + nR + "  writer-fns=" + writerFnCount.size());
    }
}
