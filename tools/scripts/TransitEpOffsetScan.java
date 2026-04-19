// Scan Transit block0 for exact EP-relative offset uses and group them by function.
// @category Pipeline
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public class TransitEpOffsetScan extends GhidraScript {
    private static final String[] NEEDLES = {
        "0x7c[ep]",
        "0x7d[ep]",
        "0xfa[ep]",
        "0xfc[ep]"
    };

    @Override
    public void run() throws Exception {
        Path out = Paths.get(System.getProperty(
            "transit.epscan.out",
            "/tmp/pscm/transit_ep_offset_scan.txt"));

        Map<String, List<String>> hits = new LinkedHashMap<>();
        InstructionIterator it = currentProgram.getListing().getInstructions(true);
        while (it.hasNext()) {
            Instruction ins = it.next();
            String text = ins.toString();
            for (String needle : NEEDLES) {
                if (!text.contains(needle)) {
                    continue;
                }
                Function f = getFunctionContaining(ins.getAddress());
                String key = f == null
                    ? String.format("(no_func) @ 0x%08x", ins.getAddress().getOffset())
                    : String.format("%s @ 0x%08x size=%d",
                        f.getName(), f.getEntryPoint().getOffset(), f.getBody().getNumAddresses());
                hits.computeIfAbsent(key, k -> new ArrayList<>())
                    .add(String.format("0x%08x  %s", ins.getAddress().getOffset(), text));
            }
        }

        StringBuilder sb = new StringBuilder();
        sb.append("Transit EP offset scan\n\n");
        for (Map.Entry<String, List<String>> e : hits.entrySet()) {
            sb.append("== ").append(e.getKey()).append(" ==\n");
            for (String line : e.getValue()) {
                sb.append(line).append("\n");
            }
            sb.append("\n");
        }

        Files.writeString(out, sb.toString());
        println("wrote EP offset scan to " + out);
    }
}
