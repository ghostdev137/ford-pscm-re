// Find users of the gp-relative context pointer at -0x1574c[gp] and dump
// surrounding instructions so the config-struct initialization path can be traced.
// @category Pipeline
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import java.nio.file.*;
import java.io.*;
import java.util.*;

public class F150FindContextUsers extends GhidraScript {
    @Override
    public void run() throws Exception {
        Listing listing = currentProgram.getListing();
        FunctionManager fm = currentProgram.getFunctionManager();
        Path out = Paths.get("/tmp/pscm/f150_lka/_context_users.txt");
        Files.createDirectories(out.getParent());

        Map<Function, List<String>> hits = new LinkedHashMap<>();
        InstructionIterator it = listing.getInstructions(true);
        while (it.hasNext() && !monitor.isCancelled()) {
            Instruction ins = it.next();
            String text = ins.toString();
            if (!text.contains("-0x1574c[gp]")) {
                continue;
            }

            Function f = fm.getFunctionContaining(ins.getAddress());
            if (f == null) {
                continue;
            }

            List<String> lines = hits.computeIfAbsent(f, k -> new ArrayList<>());
            lines.add(String.format("hit @ %s: %s", ins.getAddress(), text));

            Instruction cur = ins;
            for (int i = 0; i < 6 && cur != null; i++) {
                cur = cur.getPrevious();
            }
            for (int i = 0; i < 14 && cur != null; i++) {
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
