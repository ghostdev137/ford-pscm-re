// Decompile every function containing an FPU compare/subtract instruction
// (cmpf.s, cmpf.d, subf.s, subf.d) and persist the C to disk.
// Purpose: find the driver-override quiet-gate reader by scanning
// decompiled output for 0.8 / -0.8 literals.
// @category F150
// @runtime Java
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.listing.Listing;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

public class DecompileCmpfFuncs extends GhidraScript {
    @Override
    public void run() throws Exception {
        String outDir = System.getenv().getOrDefault("CMPF_OUT_DIR", "/tmp/pscm/cmpf_decomps");
        Files.createDirectories(Paths.get(outDir));

        FunctionManager fm = currentProgram.getFunctionManager();
        Listing listing = currentProgram.getListing();

        List<Function> candidates = new ArrayList<>();
        int totalFuncs = 0;
        for (Function f : fm.getFunctions(true)) {
            totalFuncs++;
            if (monitor.isCancelled()) break;
            InstructionIterator it = listing.getInstructions(f.getBody(), true);
            boolean found = false;
            while (it.hasNext()) {
                String mn = it.next().getMnemonicString().toLowerCase();
                // Float compares, float subtracts, float conversions used in compare
                if (mn.startsWith("cmpf") || mn.equals("subf.s") || mn.equals("subf.d")
                    || mn.equals("fcmp") || mn.startsWith("trnc") || mn.startsWith("ceilf")
                    || mn.startsWith("floorf")) {
                    found = true;
                    break;
                }
            }
            if (found) candidates.add(f);
        }
        println(String.format("Scanned %d functions; %d contain FPU compare/sub ops",
            totalFuncs, candidates.size()));

        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        StringBuilder summary = new StringBuilder();
        summary.append("func_addr\tsize\tlines\tmatches_ov_band\tfile\n");

        int n = 0;
        for (Function f : candidates) {
            if (monitor.isCancelled()) break;
            try {
                DecompileResults res = di.decompileFunction(f, 60, monitor);
                if (res.getDecompiledFunction() == null) continue;
                String code = res.getDecompiledFunction().getC();
                // Count band-relevant float literals
                int bandHits = 0;
                for (String lit : new String[] {
                        " 0.800", " -0.800", "  0.800", " 0.500", " -0.500",
                        " 30.00", " 30.0", "0x3f4ccccd", "0x3f000000",
                        "0xbf4ccccd", "0xbf000000", "0x41f00000",
                        "0xcdcc4c3f", "0xcdcc4cbf"}) {
                    int idx = 0;
                    while ((idx = code.indexOf(lit, idx)) >= 0) {
                        bandHits++;
                        idx += lit.length();
                    }
                }
                String fname = String.format("%08x_%s.c",
                    f.getEntryPoint().getOffset(),
                    f.getName().replaceAll("[^A-Za-z0-9_]", "_"));
                Files.writeString(Paths.get(outDir, fname), code);
                int lines = code.split("\n").length;
                summary.append(String.format("0x%08x\t%d\t%d\t%d\t%s\n",
                    f.getEntryPoint().getOffset(),
                    f.getBody().getNumAddresses(),
                    lines, bandHits, fname));
                n++;
                if ((n % 50) == 0) println("decompiled " + n + "/" + candidates.size());
            } catch (Exception e) {
                summary.append(String.format("0x%08x\tERROR\t0\t0\t%s\n",
                    f.getEntryPoint().getOffset(), e.getMessage()));
            }
        }
        di.dispose();
        Files.writeString(Paths.get(outDir, "_INDEX.tsv"), summary.toString());
        println("Wrote " + n + " decompiles to " + outDir);
    }
}
