// Hunt Transit functions that reference the Lane_Assist_Data1 PDU/buffer
// index 0x117 (279), and derived offsets 0x8B8 (×8), 0x45C (×4).
// @category Transit
// @runtime Java
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.listing.Listing;
import ghidra.program.model.scalar.Scalar;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

public class TransitHuntIndex extends GhidraScript {
    // Lane_Assist_Data1 dispatcher index from CAN RX table 0x01002c88
    // plus common derived offsets.
    private static long[] TARGETS = {
        0x0117,       // raw index
        0x0118,       // next message (0x3B3)
        0x045C,       // 0x117 * 4 (buffer stride 4)
        0x08B8,       // 0x117 * 8 (buffer stride 8)
        0x1170,       // 0x117 * 16 (buffer stride 16)
        0x02E0,       // ×2 — offset in table-of-16-bit-handlers
    };

    @Override
    public void run() throws Exception {
        String outDir = "/tmp/pscm/transit_lka_index";
        Files.createDirectories(Paths.get(outDir));
        FunctionManager fm = currentProgram.getFunctionManager();
        Listing listing = currentProgram.getListing();

        // map target -> fn -> hits
        Map<Long, Map<Function, List<String>>> byT = new TreeMap<>();
        for (long t : TARGETS) byT.put(t, new LinkedHashMap<>());

        InstructionIterator it = listing.getInstructions(true);
        while (it.hasNext()) {
            if (monitor.isCancelled()) break;
            Instruction ins = it.next();
            Function f = fm.getFunctionContaining(ins.getAddress());
            if (f == null) continue;
            for (int op = 0; op < ins.getNumOperands(); op++) {
                for (Object o : ins.getOpObjects(op)) {
                    if (!(o instanceof Scalar)) continue;
                    long v = ((Scalar) o).getUnsignedValue() & 0xFFFFFFFFL;
                    for (long t : TARGETS) {
                        if (v == t) {
                            byT.get(t).computeIfAbsent(f, k -> new ArrayList<>()).add(
                                String.format("0x%08x %s", ins.getAddress().getOffset(), ins.toString()));
                        }
                    }
                }
            }
        }

        StringBuilder out = new StringBuilder();
        for (long t : TARGETS) {
            out.append(String.format("\n=== Immediate 0x%x (dec %d)  functions=%d ===\n",
                t, t, byT.get(t).size()));
            byT.get(t).entrySet().stream()
                .sorted((a, b) -> Integer.compare(b.getValue().size(), a.getValue().size()))
                .limit(15)
                .forEach(e -> {
                    out.append(String.format("  %s @ 0x%08x  hits=%d  body=%d\n",
                        e.getKey().getName(), e.getKey().getEntryPoint().getOffset(),
                        e.getValue().size(), e.getKey().getBody().getNumAddresses()));
                    for (String s : e.getValue()) out.append("    ").append(s).append('\n');
                });
        }
        Files.writeString(Paths.get(outDir, "hits.txt"), out.toString());
        println("Wrote " + outDir + "/hits.txt");

        // Decompile the top candidates for each target
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        for (long t : TARGETS) {
            int n = 0;
            for (Map.Entry<Function, List<String>> e : byT.get(t).entrySet()) {
                if (n++ >= 8) break;
                try {
                    DecompileResults r = di.decompileFunction(e.getKey(), 60, monitor);
                    if (r.getDecompiledFunction() == null) continue;
                    String fn = String.format("idx_%x_%08x_%s.c",
                        t, e.getKey().getEntryPoint().getOffset(),
                        e.getKey().getName().replaceAll("[^A-Za-z0-9_]", "_"));
                    Files.writeString(Paths.get(outDir, fn), r.getDecompiledFunction().getC());
                } catch (Exception ex) {}
            }
        }
        di.dispose();
        println("Done");
    }
}
