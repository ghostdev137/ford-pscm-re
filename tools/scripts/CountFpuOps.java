// Count all FPU operations in the currently-loaded program and report
// by mnemonic. Used to determine whether the firmware does meaningful
// float work.
// @category Transit
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.listing.Listing;
import java.util.TreeMap;
import java.util.Map;

public class CountFpuOps extends GhidraScript {
    @Override
    public void run() throws Exception {
        Listing listing = currentProgram.getListing();
        Map<String, Integer> fp = new TreeMap<>();
        Map<String, Integer> mac = new TreeMap<>();
        int total = 0;
        InstructionIterator it = listing.getInstructions(true);
        while (it.hasNext()) {
            if (monitor.isCancelled()) break;
            Instruction ins = it.next();
            total++;
            String m = ins.getMnemonicString().toLowerCase();
            if (m.startsWith("cmpf") || m.startsWith("subf") || m.startsWith("addf")
                || m.startsWith("mulf") || m.startsWith("divf") || m.startsWith("sqrtf")
                || m.startsWith("trnc") || m.startsWith("floorf") || m.startsWith("ceilf")
                || m.startsWith("cvtf") || m.startsWith("maxf") || m.startsWith("minf")
                || m.equals("fcmp") || m.startsWith("fadd") || m.startsWith("fsub")
                || m.startsWith("fmul") || m.startsWith("fdiv")) {
                fp.merge(m, 1, Integer::sum);
            }
            if (m.startsWith("mulh") || m.startsWith("mac") || m.equals("mul") || m.equals("mulu")
                || m.startsWith("div") || m.startsWith("satadd") || m.startsWith("satsub")) {
                mac.merge(m, 1, Integer::sum);
            }
        }
        println("Total instructions: " + total);
        println("\nFPU ops:");
        fp.forEach((k, v) -> println(String.format("  %-12s %d", k, v)));
        int fpSum = fp.values().stream().mapToInt(Integer::intValue).sum();
        println("  TOTAL FP = " + fpSum);
        println("\nInteger/fixed-point math ops (top):");
        mac.entrySet().stream()
            .sorted((a, b) -> Integer.compare(b.getValue(), a.getValue()))
            .limit(15)
            .forEach(e -> println(String.format("  %-12s %d", e.getKey(), e.getValue())));
    }
}
