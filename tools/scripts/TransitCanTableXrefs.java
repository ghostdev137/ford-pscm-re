// Find xrefs into the Transit CAN RX dispatch tables near 0x01002c88 /
// 0x01002d54. Report callers, and for the call-site function, dump
// decompile + disasm.
// @category Transit
// @runtime Java
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSpace;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.listing.Listing;
import ghidra.program.model.scalar.Scalar;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceManager;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.HashSet;
import java.util.LinkedHashSet;
import java.util.Set;

public class TransitCanTableXrefs extends GhidraScript {

    private static final long[] BANDS = {
        0x01002c00L, 0x01002e00L,      // CAN RX band (both tables)
        0x01002000L, 0x01002200L,      // upstream band
    };

    @Override
    public void run() throws Exception {
        String outDir = "/tmp/pscm/transit_can_rx";
        Files.createDirectories(Paths.get(outDir));
        FunctionManager fm = currentProgram.getFunctionManager();
        Listing listing = currentProgram.getListing();
        ReferenceManager rm = currentProgram.getReferenceManager();
        AddressSpace sp = currentProgram.getAddressFactory().getDefaultAddressSpace();

        Set<Function> referencingFns = new LinkedHashSet<>();
        StringBuilder xref = new StringBuilder();
        xref.append("=== Xrefs into CAN RX table bands ===\n");

        // Ghidra tracked xrefs
        for (int i = 0; i < BANDS.length; i += 2) {
            long lo = BANDS[i], hi = BANDS[i+1];
            xref.append(String.format("\n-- band 0x%08x..0x%08x --\n", lo, hi));
            for (long a = lo; a < hi; a += 2) {
                Address addr = sp.getAddress(a);
                for (Reference r : rm.getReferencesTo(addr)) {
                    Function f = fm.getFunctionContaining(r.getFromAddress());
                    xref.append(String.format("  to=0x%08x  from=0x%08x  %s  fn=%s @0x%08x\n",
                        a, r.getFromAddress().getOffset(), r.getReferenceType(),
                        f != null ? f.getName() : "<none>",
                        f != null ? f.getEntryPoint().getOffset() : 0L));
                    if (f != null) referencingFns.add(f);
                }
            }
        }

        // Instruction-level scan: movhi+movea/addi pairs into band
        xref.append("\n=== movhi+movea/addi pairs landing in CAN RX band ===\n");
        InstructionIterator it = listing.getInstructions(true);
        Instruction prev = null;
        while (it.hasNext()) {
            if (monitor.isCancelled()) break;
            Instruction ins = it.next();
            if (prev != null
                && "movhi".equalsIgnoreCase(prev.getMnemonicString())
                && ("movea".equalsIgnoreCase(ins.getMnemonicString())
                    || "addi".equalsIgnoreCase(ins.getMnemonicString()))) {
                long hi = firstScalar(prev);
                long lo = firstScalar(ins);
                if (hi != Long.MIN_VALUE && lo != Long.MIN_VALUE) {
                    long v = ((hi & 0xffffL) << 16) + (short) (lo & 0xffffL);
                    v &= 0xffffffffL;
                    for (int i = 0; i < BANDS.length; i += 2) {
                        if (v >= BANDS[i] && v < BANDS[i+1]) {
                            Function f = fm.getFunctionContaining(ins.getAddress());
                            xref.append(String.format(
                                "  @0x%08x  ptr=0x%08x  fn=%s @0x%08x\n",
                                prev.getAddress().getOffset(), v,
                                f != null ? f.getName() : "<none>",
                                f != null ? f.getEntryPoint().getOffset() : 0L));
                            if (f != null) referencingFns.add(f);
                            break;
                        }
                    }
                }
            }
            prev = ins;
        }

        Files.writeString(Paths.get(outDir, "xrefs.txt"), xref.toString());
        println("referencing fns: " + referencingFns.size());

        // Decompile each referencing function
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        StringBuilder idx = new StringBuilder();
        idx.append("func_addr\tbody\tlines\tfile\n");
        for (Function f : referencingFns) {
            try {
                DecompileResults r = di.decompileFunction(f, 60, monitor);
                if (r.getDecompiledFunction() == null) continue;
                String code = r.getDecompiledFunction().getC();
                String fn = String.format("%08x_%s.c",
                    f.getEntryPoint().getOffset(),
                    f.getName().replaceAll("[^A-Za-z0-9_]", "_"));
                Files.writeString(Paths.get(outDir, fn), code);
                int lines = code.split("\n").length;
                idx.append(String.format("0x%08x\t%d\t%d\t%s\n",
                    f.getEntryPoint().getOffset(),
                    f.getBody().getNumAddresses(), lines, fn));
            } catch (Exception e) {}
        }
        di.dispose();
        Files.writeString(Paths.get(outDir, "_INDEX.tsv"), idx.toString());
        println("Wrote " + outDir);
    }

    private long firstScalar(Instruction ins) {
        for (int op = 0; op < ins.getNumOperands(); op++) {
            for (Object o : ins.getOpObjects(op)) {
                if (o instanceof Scalar) return ((Scalar) o).getUnsignedValue();
            }
        }
        return Long.MIN_VALUE;
    }
}
