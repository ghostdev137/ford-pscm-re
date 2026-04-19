// Find functions that reference the live EPS context + 0x68 record.
// @category Pipeline
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.listing.Listing;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public class F150FindCtx68Users extends GhidraScript {
    @Override
    public void run() throws Exception {
        Listing listing = currentProgram.getListing();
        FunctionManager fm = currentProgram.getFunctionManager();
        Path out = Path.of(System.getenv().getOrDefault(
            "F150_CTX68_OUT", "/tmp/pscm/f150_lka/_ctx68_users.txt"));
        Files.createDirectories(out.getParent());

        Map<Function, List<String>> hits = new LinkedHashMap<>();
        InstructionIterator it = listing.getInstructions(true);
        while (it.hasNext() && !monitor.isCancelled()) {
            Instruction ins = it.next();
            String text = ins.toString().toLowerCase();

            boolean interesting =
                text.contains("-0x1574c[gp]") ||
                text.contains(" 0x68[") ||
                text.contains("0x68[ep]") ||
                text.contains("0x68[r");

            if (!interesting) {
                continue;
            }

            Function f = fm.getFunctionContaining(ins.getAddress());
            if (f == null) {
                continue;
            }

            List<String> lines = hits.computeIfAbsent(f, __ -> new ArrayList<>());
            lines.add(String.format("hit @ %s: %s", ins.getAddress(), ins));

            Instruction cur = ins;
            for (int i = 0; i < 5 && cur != null; i++) {
                cur = cur.getPrevious();
            }
            for (int i = 0; i < 12 && cur != null; i++) {
                lines.add(String.format("  %s: %s", cur.getAddress(), cur));
                cur = cur.getNext();
            }
            lines.add("");
        }

        StringBuilder sb = new StringBuilder();
        for (Map.Entry<Function, List<String>> e : hits.entrySet()) {
            Function f = e.getKey();
            sb.append(String.format("=== %s @ 0x%x size=%d ===\n",
                f.getName(), f.getEntryPoint().getOffset(), f.getBody().getNumAddresses()));
            for (String line : e.getValue()) {
                sb.append(line).append('\n');
            }
            sb.append('\n');
        }

        Files.writeString(out, sb.toString());
        println("wrote " + out + " (" + hits.size() + " functions)");
    }
}
