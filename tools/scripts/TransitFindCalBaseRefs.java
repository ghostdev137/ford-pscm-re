// Find ld.w instructions with displacement in the cal+0x29D4..29E4 band.
// Goal: identify which register serves as the cal-base pointer, then
// trace who writes to it (that's where cal is actually rooted).
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
import java.util.TreeMap;

public class TransitFindCalBaseRefs extends GhidraScript {
    @Override
    public void run() throws Exception {
        Files.createDirectories(Paths.get("/tmp/pscm/transit_override"));
        FunctionManager fm = currentProgram.getFunctionManager();
        Listing listing = currentProgram.getListing();

        // Displacements we care about (±0.8 Nm hysteresis family).
        long[] wantDisp = { 0x29D4, 0x29D8, 0x29DC, 0x29E0, 0x29E4,
                            0x29E8, 0x29CC, 0x29D0, 0x29F0 };
        StringBuilder out = new StringBuilder();
        out.append("=== ld.w/ld.hu instructions with displacement in cal override band ===\n");
        Map<Integer, Integer> baseRegCounts = new HashMap<>();
        int total = 0;
        InstructionIterator it = listing.getInstructions(true);
        while (it.hasNext()) {
            if (monitor.isCancelled()) break;
            Instruction ins = it.next();
            String mn = ins.getMnemonicString().toLowerCase();
            if (!mn.startsWith("ld") && !mn.startsWith("st")) continue;
            if (ins.getNumOperands() < 2) continue;
            // Look for scalar operand that matches
            long foundDisp = -1;
            for (int op = 0; op < ins.getNumOperands(); op++) {
                for (Object o : ins.getOpObjects(op)) {
                    if (o instanceof Scalar) {
                        long v = ((Scalar) o).getSignedValue();
                        for (long w : wantDisp) {
                            if (v == w) { foundDisp = v; break; }
                        }
                        if (foundDisp >= 0) break;
                    }
                }
                if (foundDisp >= 0) break;
            }
            if (foundDisp < 0) continue;

            total++;
            Function f = fm.getFunctionContaining(ins.getAddress());
            String fn = f != null ? f.getName() : "<none>";
            long fe = f != null ? f.getEntryPoint().getOffset() : 0L;
            out.append(String.format("  @0x%08x  %s  %s  fn=%s @0x%08x\n",
                ins.getAddress().getOffset(), mn, ins.toString(), fn, fe));
        }
        out.append(String.format("\nTotal: %d load/store instructions with displacement in override band\n", total));

        // Also: enumerate ALL ld.w instructions in the program, histogram of disp values
        out.append("\n=== Displacement histogram for all ld.w instructions (top 50) ===\n");
        Map<Long, Integer> dispCounts = new HashMap<>();
        it = listing.getInstructions(true);
        while (it.hasNext()) {
            if (monitor.isCancelled()) break;
            Instruction ins = it.next();
            if (!"ld.w".equalsIgnoreCase(ins.getMnemonicString())) continue;
            for (int op = 0; op < ins.getNumOperands(); op++) {
                for (Object o : ins.getOpObjects(op)) {
                    if (o instanceof Scalar) {
                        long v = ((Scalar) o).getSignedValue();
                        if (v > 0x1000 && v < 0x8000) {
                            dispCounts.merge(v, 1, Integer::sum);
                        }
                    }
                }
            }
        }
        dispCounts.entrySet().stream()
            .sorted((a, b) -> Integer.compare(b.getValue(), a.getValue()))
            .limit(50)
            .forEach(e -> out.append(String.format("  disp=0x%04x (%d): %d\n", e.getKey(), e.getKey(), e.getValue())));

        Files.writeString(Paths.get("/tmp/pscm/transit_override/cal_base_refs.txt"), out.toString());
        println("Wrote /tmp/pscm/transit_override/cal_base_refs.txt; found " + total + " band hits");
    }
}
