// Trace callers of the Transit Q15 torque reader FUN_010babf2 (0x010babf8
// mulhi 0x67c2) and decompile them. Score each caller for override-gate
// signatures: abs() computation + threshold compare + gate flag write +
// hysteresis structure. Top-scoring candidate(s) are the LKA quiet-gate
// analog of F-150 FUN_101a3b84.
// @category Transit
// @runtime Java
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSpace;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceManager;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

public class TransitTraceTorqueConsumers extends GhidraScript {
    // Seeds: known Q15/Q-format reader entry points we trust
    private static final long[] TORQUE_READERS = {
        0x010BABF2L,   // mulhi 0x67c2 at +6 — torque_angle_reader_Q15
    };
    private static final int TRANSITIVE_DEPTH = 2;   // walk callers up to depth 2
    private static final String OUT_DIR = "/tmp/pscm/transit_gate_hunt";

    private Set<Function> collectCallers(FunctionManager fm, ReferenceManager rm,
                                          AddressSpace sp, long[] seeds, int depth) {
        Set<Function> frontier = new LinkedHashSet<>();
        for (long s : seeds) {
            Function f = fm.getFunctionAt(sp.getAddress(s));
            if (f != null) frontier.add(f);
        }
        Set<Function> all = new LinkedHashSet<>(frontier);
        for (int d = 0; d < depth; d++) {
            Set<Function> next = new LinkedHashSet<>();
            for (Function f : frontier) {
                for (Reference r : rm.getReferencesTo(f.getEntryPoint())) {
                    Function c = fm.getFunctionContaining(r.getFromAddress());
                    if (c != null && !all.contains(c)) next.add(c);
                }
            }
            all.addAll(next);
            frontier = next;
            if (frontier.isEmpty()) break;
        }
        return all;
    }

    private int scoreGate(String code) {
        int s = 0;
        // Structural hints that indicate a gate / hysteresis
        if (code.contains(" = true") || code.contains(" = false")) s += 2;
        if (code.matches("(?s).*\\b[A-Za-z_]+_\\w*[gG]ate.*")) s += 2;
        if (code.contains("overrid")) s += 4;
        if (code.contains("latch")) s += 2;
        if (code.contains("DAT_fef")) s += 1;  // RAM addresses — Transit uses 0xfefxxxxx RAM
        // abs() pattern
        if (code.matches("(?s).*if\\s*\\(\\s*\\(?int\\)?\\s*\\w+\\s*<\\s*0\\s*\\).*=\\s*-\\w+.*")) s += 3;
        // hysteresis: two successive compares of same variable against different thresholds
        int cmpCount = 0;
        int idx = 0;
        while ((idx = code.indexOf(" < ", idx)) >= 0) { cmpCount++; idx += 3; }
        idx = 0;
        while ((idx = code.indexOf(" > ", idx)) >= 0) { cmpCount++; idx += 3; }
        if (cmpCount >= 4) s += cmpCount / 2;
        // "quiet" or "inhibit" or "Override" or "Driver"
        if (code.toLowerCase().contains("quiet")) s += 5;
        if (code.toLowerCase().contains("override")) s += 5;
        if (code.toLowerCase().contains("driver")) s += 2;
        return s;
    }

    @Override
    public void run() throws Exception {
        Files.createDirectories(Paths.get(OUT_DIR));
        FunctionManager fm = currentProgram.getFunctionManager();
        ReferenceManager rm = currentProgram.getReferenceManager();
        AddressSpace sp = currentProgram.getAddressFactory().getDefaultAddressSpace();

        Set<Function> callers = collectCallers(fm, rm, sp, TORQUE_READERS, TRANSITIVE_DEPTH);
        println("Collected " + callers.size() + " functions (seed + " + TRANSITIVE_DEPTH + "-hop callers)");

        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);

        List<String[]> rows = new ArrayList<>();
        for (Function f : callers) {
            if (monitor.isCancelled()) break;
            try {
                DecompileResults res = di.decompileFunction(f, 60, monitor);
                if (res.getDecompiledFunction() == null) continue;
                String code = res.getDecompiledFunction().getC();
                int score = scoreGate(code);
                String fn = String.format("%08x_%s.c",
                    f.getEntryPoint().getOffset(),
                    f.getName().replaceAll("[^A-Za-z0-9_]", "_"));
                Files.writeString(Paths.get(OUT_DIR, fn), code);
                rows.add(new String[] {
                    String.format("0x%08x", f.getEntryPoint().getOffset()),
                    String.valueOf(f.getBody().getNumAddresses()),
                    String.valueOf(code.split("\n").length),
                    String.valueOf(score),
                    fn
                });
            } catch (Exception e) { /* skip */ }
        }
        di.dispose();

        rows.sort((a, b) -> Integer.compare(Integer.parseInt(b[3]), Integer.parseInt(a[3])));
        StringBuilder idx = new StringBuilder();
        idx.append("func_addr\tsize\tlines\tscore\tfile\n");
        for (String[] r : rows) {
            idx.append(String.join("\t", r)).append('\n');
        }
        Files.writeString(Paths.get(OUT_DIR, "_INDEX.tsv"), idx.toString());
        println("Top 10 by score:");
        rows.stream().limit(10).forEach(r ->
            println(String.format("  score=%s size=%s  %s", r[3], r[1], r[4])));
    }
}
