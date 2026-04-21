// Find code that WRITES to the F-150 quiet-gate thresholds
// _DAT_fef26382 and _DAT_fef263de. The writer is the cal->RAM copy
// routine; tracing it back tells us which cal address holds the
// threshold values.
// @category F150
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
import java.util.LinkedHashSet;
import java.util.Set;

public class F150FindQuietGateRamInit extends GhidraScript {
    @Override
    public void run() throws Exception {
        String outDir = "/tmp/pscm/f150_quietgate";
        Files.createDirectories(Paths.get(outDir));

        FunctionManager fm = currentProgram.getFunctionManager();
        ReferenceManager rm = currentProgram.getReferenceManager();
        AddressSpace sp = currentProgram.getAddressFactory().getDefaultAddressSpace();

        long[] targets = {
            0xFEF26382L,   // abs torque threshold (found via decompile)
            0xFEF263DEL,   // state threshold (was validated via emulation)
            0xFEF263FAL,   // motor-current clamp value (in same fn)
            0xFEF263FCL,   // filter alpha
            0xFEF263F2L,   // another filter alpha
            0xFEF263F4L,
            0xFEF263F6L,
            0xFEF263F8L,
            0xFEF263FEL
        };

        Set<Function> writers = new LinkedHashSet<>();
        Set<Function> readers = new LinkedHashSet<>();
        StringBuilder log = new StringBuilder();

        for (long t : targets) {
            Address a = sp.getAddress(t);
            log.append(String.format("\n--- 0x%08x ---\n", t));
            for (Reference r : rm.getReferencesTo(a)) {
                Address src = r.getFromAddress();
                Function f = fm.getFunctionContaining(src);
                String fn = f != null ? f.getName() : "<none>";
                long fe = f != null ? f.getEntryPoint().getOffset() : 0;
                String rt = r.getReferenceType().toString();
                log.append(String.format("  from=0x%08x  %s @0x%08x  type=%s\n",
                    src.getOffset(), fn, fe, rt));
                if (f != null) {
                    if (rt.contains("WRITE")) writers.add(f);
                    else readers.add(f);
                }
            }
        }
        Files.writeString(Paths.get(outDir, "xrefs.txt"), log.toString());
        println("writers: " + writers.size() + " readers: " + readers.size());

        // Decompile writers first (highest interest)
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        StringBuilder idx = new StringBuilder();
        idx.append("role\tfunc_addr\tlines\tfile\n");

        for (Function f : writers) {
            try {
                DecompileResults r = di.decompileFunction(f, 90, monitor);
                if (r.getDecompiledFunction() == null) continue;
                String code = r.getDecompiledFunction().getC();
                String fn = String.format("writer_%08x_%s.c",
                    f.getEntryPoint().getOffset(),
                    f.getName().replaceAll("[^A-Za-z0-9_]", "_"));
                Files.writeString(Paths.get(outDir, fn), code);
                idx.append(String.format("writer\t0x%08x\t%d\t%s\n",
                    f.getEntryPoint().getOffset(), code.split("\n").length, fn));
            } catch (Exception e) { /* skip */ }
        }
        for (Function f : readers) {
            if (writers.contains(f)) continue;
            try {
                DecompileResults r = di.decompileFunction(f, 90, monitor);
                if (r.getDecompiledFunction() == null) continue;
                String code = r.getDecompiledFunction().getC();
                String fn = String.format("reader_%08x_%s.c",
                    f.getEntryPoint().getOffset(),
                    f.getName().replaceAll("[^A-Za-z0-9_]", "_"));
                Files.writeString(Paths.get(outDir, fn), code);
                idx.append(String.format("reader\t0x%08x\t%d\t%s\n",
                    f.getEntryPoint().getOffset(), code.split("\n").length, fn));
            } catch (Exception e) { /* skip */ }
        }
        di.dispose();
        Files.writeString(Paths.get(outDir, "_INDEX.tsv"), idx.toString());
        println("Wrote " + outDir);
    }
}
