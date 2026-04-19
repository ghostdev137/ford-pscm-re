// Dump caller-layer context for key Transit state-writer jump sites.
// @category Pipeline
// @runtime Java
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileOptions;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressIterator;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.ReferenceManager;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

public class TransitCallerTrace extends GhidraScript {
    private static class Target {
        final long site;
        final String name;
        Target(long site, String name) {
            this.site = site;
            this.name = name;
        }
    }

    private static final Target[] TARGETS = {
        new Target(0x010AAAE4L, "caller_of_010b7b30_write_2444"),
        new Target(0x010B75A8L, "caller_of_010b532a_write_2444"),
        new Target(0x010B729EL, "caller_of_010b5020_write_2efe"),
        new Target(0x0107CAF6L, "caller_of_01072bba_write_2e20"),
        new Target(0x0103598CL, "caller_of_0103681e_mid_dispatch"),
        new Target(0x0107328CL, "caller_of_0107ccf0_mid_dispatch"),
        new Target(0x01036A4CL, "caller_of_01038ade_selector_ctx"),
        new Target(0x0107CD04L, "caller_of_0107ca92_write_2e20_branch"),
        new Target(0x01107BC4L, "helper_select_2444_branch"),
        new Target(0x011078BAL, "helper_select_2efe_branch"),
        new Target(0x010B4AD4L, "dispatch_b4ad4"),
        new Target(0x010B4B10L, "dispatch_b4b10"),
    };

    @Override
    public void run() throws Exception {
        Path outDir = Paths.get(System.getProperty(
            "transit.callertrace.out",
            "/tmp/pscm/transit_caller_trace"));
        Files.createDirectories(outDir);

        ReferenceManager rm = currentProgram.getReferenceManager();
        DecompInterface di = new DecompInterface();
        DecompileOptions opts = new DecompileOptions();
        di.setOptions(opts);
        di.toggleCCode(true);
        di.toggleSyntaxTree(true);
        di.setSimplificationStyle("decompile");
        di.openProgram(currentProgram);

        StringBuilder index = new StringBuilder();
        index.append("Transit caller trace index\n\n");

        for (Target t : TARGETS) {
            Address site = toAddr(t.site);
            Function f = getFunctionContaining(site);
            Path out = outDir.resolve(String.format("%08x_%s.txt", t.site, t.name));
            StringBuilder sb = new StringBuilder();
            sb.append(String.format("target_site=0x%08x\nlabel=%s\n\n", t.site, t.name));

            if (f == null) {
                sb.append("containing_function=(none)\n");
                appendWindow(sb, site, 0x20, 0x30);
                Files.writeString(out, sb.toString());
                index.append(String.format("0x%08x %s -> no containing function\n", t.site, t.name));
                continue;
            }

            sb.append(String.format("function=%s\nentry=0x%08x\nsize=%d\n\n",
                f.getName(), f.getEntryPoint().getOffset(), f.getBody().getNumAddresses()));

            sb.append("refs_to_function_entry:\n");
            ReferenceIterator refsTo = rm.getReferencesTo(f.getEntryPoint());
            int refsToCount = 0;
            while (refsTo.hasNext()) {
                Reference ref = refsTo.next();
                Function caller = getFunctionContaining(ref.getFromAddress());
                sb.append(String.format("  0x%08x -> 0x%08x  %-14s  %s\n",
                    ref.getFromAddress().getOffset(),
                    f.getEntryPoint().getOffset(),
                    ref.getReferenceType().toString(),
                    caller == null ? "(none)" :
                        String.format("%s @ 0x%08x", caller.getName(), caller.getEntryPoint().getOffset())));
                refsToCount++;
            }
            if (refsToCount == 0) {
                sb.append("  (none)\n");
            }
            sb.append("\n");

            sb.append("instruction_window_around_target:\n");
            appendWindow(sb, site, 0x30, 0x50);
            sb.append("\n");

            sb.append("references_from_function_body:\n");
            int bodyRefCount = 0;
            AddressIterator it = f.getBody().getAddresses(true);
            while (it.hasNext()) {
                Address from = it.next();
                Reference[] refs = rm.getReferencesFrom(from);
                for (Reference ref : refs) {
                    Address to = ref.getToAddress();
                    if (to == null) {
                        continue;
                    }
                    long off = to.getOffset();
                    if ((0x01002B50L <= off && off < 0x01002C40L) ||
                        (0x0100DB80L <= off && off < 0x0100DF00L) ||
                        (0x010B4900L <= off && off < 0x010B8000L) ||
                        (0x01072B00L <= off && off < 0x0107CB20L) ||
                        (0x010CE5A0L <= off && off < 0x010CE700L)) {
                        sb.append(String.format("  0x%08x -> 0x%08x  %s\n",
                            from.getOffset(), off, ref.getReferenceType().toString()));
                        bodyRefCount++;
                    }
                }
            }
            if (bodyRefCount == 0) {
                sb.append("  (none)\n");
            }
            sb.append("\n");

            sb.append("decompile:\n\n");
            try {
                DecompileResults dr = di.decompileFunction(f, 60, monitor);
                if (dr != null && dr.decompileCompleted() && dr.getDecompiledFunction() != null) {
                    sb.append(dr.getDecompiledFunction().getC());
                    sb.append("\n");
                } else if (dr != null) {
                    sb.append("decompile_failed: ");
                    sb.append(dr.getErrorMessage());
                    sb.append("\n");
                } else {
                    sb.append("decompile_returned_null\n");
                }
            } catch (Exception e) {
                sb.append("decompile_exception: ");
                sb.append(e.toString());
                sb.append("\n");
            }

            Files.writeString(out, sb.toString());
            index.append(String.format("0x%08x %s -> %s @ 0x%08x size=%d\n",
                t.site, t.name, f.getName(), f.getEntryPoint().getOffset(), f.getBody().getNumAddresses()));
        }

        Files.writeString(outDir.resolve("index.txt"), index.toString());
        println("wrote caller trace to " + outDir);
    }

    private void appendWindow(StringBuilder sb, Address center, long before, long after) {
        Address start = center.subtract(before);
        Address end = center.add(after);
        InstructionIterator it = currentProgram.getListing().getInstructions(start, true);
        while (it.hasNext()) {
            Instruction ins = it.next();
            if (ins.getAddress().compareTo(end) > 0) {
                break;
            }
            sb.append(String.format("  0x%08x  %s\n", ins.getAddress().getOffset(), ins.toString()));
        }
    }
}
