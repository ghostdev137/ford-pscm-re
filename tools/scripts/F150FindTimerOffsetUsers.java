// Scan instructions for GP-relative references to timer calibration offsets.
// @category Pipeline
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.listing.Listing;
import ghidra.program.model.scalar.Scalar;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

public class F150FindTimerOffsetUsers extends GhidraScript {
    private static final class Target {
        final long value;
        final String label;
        Target(long value, String label) {
            this.value = value;
            this.label = label;
        }
    }

    private static final List<Target> TARGETS = Arrays.asList(
        new Target(0x7adcL, "LKA arm timer"),
        new Target(0x7adeL, "LKA re-arm timer"),
        new Target(0x7ae0L, "LKA settle/hysteresis A"),
        new Target(0x7ae2L, "LKA settle/hysteresis B"),
        new Target(0x7e64L, "ESA/TJA timer"),
        new Target(0x7e66L, "ESA/TJA settle/hysteresis B"),
        new Target(0x7e68L, "ESA/TJA settle/hysteresis A"),
        new Target(10000L, "literal 10000"),
        new Target(1500L, "literal 1500"),
        new Target(300L, "literal 300")
    );

    @Override
    public void run() throws Exception {
        Path out = Path.of(System.getenv().getOrDefault("F150_TIMER_OFFSET_OUT", "/tmp/pscm/f150_timer_offsets.txt"));
        Files.createDirectories(out.getParent());

        Listing listing = currentProgram.getListing();
        FunctionManager fm = currentProgram.getFunctionManager();
        Map<Function, Set<String>> hitsByFunction = new LinkedHashMap<>();
        StringBuilder sb = new StringBuilder();

        InstructionIterator it = listing.getInstructions(true);
        while (it.hasNext() && !monitor.isCancelled()) {
            Instruction ins = it.next();
            Set<String> hits = new LinkedHashSet<>();
            for (int op = 0; op < ins.getNumOperands(); op++) {
                String repr = ins.getDefaultOperandRepresentation(op).toLowerCase();
                Object[] objs = ins.getOpObjects(op);
                for (Target target : TARGETS) {
                    if (repr.contains(String.format("0x%x", target.value))) {
                        hits.add(target.label + " via " + repr);
                    }
                }
                for (Object obj : objs) {
                    if (obj instanceof Scalar) {
                        long sval = ((Scalar) obj).getUnsignedValue();
                        for (Target target : TARGETS) {
                            if (sval == target.value) {
                                hits.add(target.label + " scalar");
                            }
                        }
                    }
                }
            }
            if (hits.isEmpty()) {
                continue;
            }
            Function f = fm.getFunctionContaining(ins.getAddress());
            sb.append(String.format("%s  %s  fn=%s @0x%08x  hits=%s\n",
                ins.getAddress(),
                ins,
                f == null ? "<none>" : f.getName(),
                f == null ? 0L : f.getEntryPoint().getOffset(),
                hits));
            if (f != null) {
                hitsByFunction.computeIfAbsent(f, __ -> new LinkedHashSet<>()).addAll(hits);
            }
        }

        sb.append("\n=== Functions grouped ===\n");
        for (Map.Entry<Function, Set<String>> entry : hitsByFunction.entrySet()) {
            Function f = entry.getKey();
            sb.append(String.format("%s @0x%08x size=%d tags=%s\n",
                f.getName(), f.getEntryPoint().getOffset(), f.getBody().getNumAddresses(), entry.getValue()));
        }

        Files.writeString(out, sb.toString());
        println("wrote " + out);
    }
}
