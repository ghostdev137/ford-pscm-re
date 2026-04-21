// F-150: scan all load/store instructions for displacement ~0x7A5C
// (offset from cal base 0x101D0000 to the -0.8 singleton).
// Report base register so we can identify the cal-pointer register.
// @category F150
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

public class F150FindLdDisp extends GhidraScript {
    @Override
    public void run() throws Exception {
        Files.createDirectories(Paths.get("/tmp/pscm/f150_quietgate"));
        FunctionManager fm = currentProgram.getFunctionManager();
        Listing listing = currentProgram.getListing();

        // Target displacements around -0.8 at cal+0x7A5C on F-150
        long[] want = { 0x7A4C, 0x7A50, 0x7A54, 0x7A58, 0x7A5C, 0x7A60,
                        0x7A64, 0x7A68, 0x7A6C, 0x7A70, 0x7A74, 0x7A78 };
        StringBuilder out = new StringBuilder();
        out.append("=== ld.w/st.w with disp in 0x7A4C..0x7A78 band ===\n");

        Map<Long, Integer> allDisps = new HashMap<>();
        InstructionIterator it = listing.getInstructions(true);
        int band = 0;
        while (it.hasNext()) {
            if (monitor.isCancelled()) break;
            Instruction ins = it.next();
            String mn = ins.getMnemonicString().toLowerCase();
            if (!(mn.startsWith("ld") || mn.startsWith("st") || mn.startsWith("sld"))) continue;
            for (int op = 0; op < ins.getNumOperands(); op++) {
                for (Object o : ins.getOpObjects(op)) {
                    if (o instanceof Scalar) {
                        long v = ((Scalar) o).getSignedValue();
                        if (v < 0) v = ((Scalar) o).getUnsignedValue();
                        if (v > 0x1000 && v < 0x10000) {
                            allDisps.merge(v, 1, Integer::sum);
                        }
                        for (long w : want) {
                            if (v == w) {
                                Function f = fm.getFunctionContaining(ins.getAddress());
                                String fn = f != null ? f.getName() : "<none>";
                                long fe = f != null ? f.getEntryPoint().getOffset() : 0;
                                out.append(String.format("  @0x%08x  %s  %s  fn=%s @0x%08x\n",
                                    ins.getAddress().getOffset(), mn, ins.toString(), fn, fe));
                                band++;
                                break;
                            }
                        }
                    }
                }
            }
        }
        out.append(String.format("\nBand hits: %d\n", band));

        out.append("\n=== Top 40 ld/st displacements in 0x1000..0xFFFF range ===\n");
        allDisps.entrySet().stream()
            .sorted((a, b) -> Integer.compare(b.getValue(), a.getValue()))
            .limit(40)
            .forEach(e -> out.append(String.format("  disp=0x%04x  count=%d\n", e.getKey(), e.getValue())));

        Files.writeString(Paths.get("/tmp/pscm/f150_quietgate/ld_disp_scan.txt"), out.toString());
        println("Band hits: " + band);
    }
}
