// Probe seeded Transit project for config/DID refs and candidate function context.
// @category Pipeline
// @runtime Java
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.ReferenceManager;
import java.util.LinkedHashSet;
import java.util.Set;

public class TransitConfigProbe extends GhidraScript {
    private static final long[][] RANGES = {
        {0x01003040L, 0x01003170L}, // suspected as-built validation/template area
        {0x01008600L, 0x010086C0L}, // prior config-table hunt window
        {0x0100DBACL, 0x0100DD00L}, // DID + descriptor cluster
    };

    private static final String[] RANGE_LABELS = {
        "asbuilt_template_validation",
        "config_table",
        "did_table_and_desc",
    };

    private static final long[] CANDIDATES = {
        0x0108BF42L,
        0x01090CE4L,
        0x0107B6DCL,
        0x010B4C60L,
        0x010CE5DEL,
        0x010CE608L,
    };

    @Override
    public void run() throws Exception {
        ReferenceManager rm = currentProgram.getReferenceManager();
        DecompInterface ifc = new DecompInterface();
        ifc.openProgram(currentProgram);

        for (int i = 0; i < RANGES.length; i++) {
            long start = RANGES[i][0];
            long end = RANGES[i][1];
            println(String.format("== %s 0x%08x..0x%08x ==",
                RANGE_LABELS[i], start, end));
            Set<Function> funcs = new LinkedHashSet<>();
            int totalRefs = 0;
            for (long off = start; off < end; off++) {
                Address a = toAddr(off);
                ReferenceIterator refs = rm.getReferencesTo(a);
                while (refs.hasNext()) {
                    Reference ref = refs.next();
                    totalRefs++;
                    Function f = getFunctionContaining(ref.getFromAddress());
                    if (f != null) {
                        funcs.add(f);
                    }
                    println(String.format("ref %s -> %s type=%s func=%s",
                        ref.getFromAddress(),
                        a,
                        ref.getReferenceType(),
                        f == null ? "(none)" :
                            f.getEntryPoint().toString() + " " + f.getName()));
                }
            }
            println(String.format("totalRefs=%d uniqueFuncs=%d", totalRefs, funcs.size()));
            for (Function f : funcs) {
                println(String.format("FUNC %s %s size=%d",
                    f.getEntryPoint(), f.getName(), f.getBody().getNumAddresses()));
            }
            println("");
        }

        for (long off : CANDIDATES) {
            Address a = toAddr(off);
            Function f = getFunctionContaining(a);
            println(String.format("== candidate 0x%08x ==", off));
            if (f == null) {
                println("no containing function");
                println("");
                continue;
            }

            println(String.format("function=%s entry=%s size=%d",
                f.getName(), f.getEntryPoint(), f.getBody().getNumAddresses()));

            println("callers:");
            for (Function caller : f.getCallingFunctions(monitor)) {
                println(String.format("  %s %s size=%d",
                    caller.getEntryPoint(), caller.getName(), caller.getBody().getNumAddresses()));
            }

            println("callees:");
            for (Function callee : f.getCalledFunctions(monitor)) {
                println(String.format("  %s %s size=%d",
                    callee.getEntryPoint(), callee.getName(), callee.getBody().getNumAddresses()));
            }

            DecompileResults res = ifc.decompileFunction(f, 60, monitor);
            if (res != null && res.decompileCompleted() && res.getDecompiledFunction() != null) {
                String[] lines = res.getDecompiledFunction().getC().split("\n");
                println("decompile:");
                for (int i = 0; i < Math.min(lines.length, 24); i++) {
                    println(lines[i]);
                }
            } else if (res != null) {
                println("decompile failed: " + res.getErrorMessage());
            } else {
                println("decompile returned null");
            }
            println("");
        }
    }
}
