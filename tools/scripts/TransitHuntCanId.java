// Hunt Transit functions that reference CAN ID 0x3CA (Lane_Assist_Data1,
// sent by IPMA to PSCM). This is definitionally LKA code. Each hit is
// either the message receiver or the state-machine gated on that msg.
//
// Also hunts other LKA-adjacent CAN IDs to build the LKA call graph:
//   0x3CA  Lane_Assist_Data1         (IPMA -> PSCM  - LKA command)
//   0x3CB  Lane_Assist_Data2         (IPMA -> PSCM)
//   0x3B7  LateralMotionControl      (IPMA -> PSCM  - LKA intervention)
//   0x3B8  LateralMotionControl2     (IPMA -> PSCM  - CAN-FD)
//   0x070  ParkAid_Data              (IPMA -> PSCM  - APA)
//   0x083  SteeringWheelAngle
//   0x165  Brake_Data                (ABS  -> PSCM)
//   0x04F  EngineData                (PCM  -> PSCM)
// We'll also catch any 16-bit immediate in the 0x3BX/0x3CX range to
// surface adjacent IDs we didn't list.
//
// Emits per-CAN-ID lists of hit functions + immediate-usage sites.
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
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

public class TransitHuntCanId extends GhidraScript {
    private static long[] LKA_IDS = {
        0x3CAL, 0x3CBL, 0x3B7L, 0x3B8L, 0x070L, 0x165L
    };

    @Override
    public void run() throws Exception {
        String outDir = "/tmp/pscm/transit_lka_canids";
        Files.createDirectories(Paths.get(outDir));
        FunctionManager fm = currentProgram.getFunctionManager();
        Listing listing = currentProgram.getListing();

        // Map: canId -> (function -> [sites])
        Map<Long, Map<Function, List<String>>> byId = new TreeMap<>();
        for (long id : LKA_IDS) byId.put(id, new LinkedHashMap<>());

        // Also track 16-bit immediates 0x3B0..0x3CF as "LKA-adjacent"
        Map<Long, Map<Function, Integer>> adj = new TreeMap<>();

        int totalInstructions = 0;
        InstructionIterator it = listing.getInstructions(true);
        while (it.hasNext()) {
            if (monitor.isCancelled()) break;
            Instruction ins = it.next();
            totalInstructions++;
            Function f = fm.getFunctionContaining(ins.getAddress());
            for (int op = 0; op < ins.getNumOperands(); op++) {
                for (Object o : ins.getOpObjects(op)) {
                    if (!(o instanceof Scalar)) continue;
                    long v = ((Scalar) o).getUnsignedValue() & 0xFFFFFFFFL;
                    // exact LKA hits
                    for (long id : LKA_IDS) {
                        if (v == id && f != null) {
                            byId.get(id).computeIfAbsent(f, k -> new ArrayList<>()).add(
                                String.format("0x%08x  %s", ins.getAddress().getOffset(), ins.toString()));
                        }
                    }
                    // adjacent
                    if (v >= 0x3B0 && v <= 0x3CF && f != null) {
                        adj.computeIfAbsent(v, k -> new LinkedHashMap<>())
                           .merge(f, 1, Integer::sum);
                    }
                }
            }
        }

        StringBuilder out = new StringBuilder();
        out.append(String.format("Scanned %d instructions\n\n", totalInstructions));
        for (Map.Entry<Long, Map<Function, List<String>>> e : byId.entrySet()) {
            out.append(String.format("=== CAN ID 0x%03x  (%d distinct functions) ===\n",
                e.getKey(), e.getValue().size()));
            for (Map.Entry<Function, List<String>> fe : e.getValue().entrySet()) {
                Function f = fe.getKey();
                out.append(String.format("  %s @ 0x%08x  hits=%d  body=%d\n",
                    f.getName(), f.getEntryPoint().getOffset(),
                    fe.getValue().size(), f.getBody().getNumAddresses()));
                for (String s : fe.getValue()) {
                    out.append("    ").append(s).append('\n');
                }
            }
            out.append('\n');
        }
        out.append("=== Adjacent CAN-ID-range immediates 0x3B0..0x3CF ===\n");
        adj.entrySet().stream()
            .sorted((a, b) -> Long.compare(a.getKey(), b.getKey()))
            .forEach(e -> {
                int total = e.getValue().values().stream().mapToInt(Integer::intValue).sum();
                out.append(String.format("\n  0x%03x  functions=%d  total_refs=%d\n",
                    e.getKey(), e.getValue().size(), total));
                e.getValue().entrySet().stream()
                    .sorted((a, b) -> Integer.compare(b.getValue(), a.getValue()))
                    .limit(8)
                    .forEach(fe -> out.append(String.format("    %s @ 0x%08x  refs=%d\n",
                        fe.getKey().getName(),
                        fe.getKey().getEntryPoint().getOffset(),
                        fe.getValue())));
            });

        Files.writeString(Paths.get(outDir, "canid_hits.txt"), out.toString());
        println("Wrote " + outDir + "/canid_hits.txt");
        // Summary to console
        for (long id : LKA_IDS) {
            println(String.format("  0x%03x -> %d functions", id, byId.get(id).size()));
        }
    }
}
