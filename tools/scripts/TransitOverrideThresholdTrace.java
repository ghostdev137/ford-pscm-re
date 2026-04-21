// Trace code that reads the Transit LKA driver-override threshold words
// at cal+0x29D4 (+0.8 Nm hypothesis) and cal+0x29E0 (-0.8 Nm hypothesis).
// Runtime cal base is 0x00FD0000, so the targets are 0x00FD29D4 / 0x00FD29E0.
//
// Strategy:
//  1. Ghidra ReferenceManager xrefs to each target address.
//  2. Global movhi+movea/addi pair scan — find pointer reconstructions
//     landing within the ±64-byte band around each threshold.
//  3. Dump each containing function's body as decomp-ready disassembly
//     so we can eyeball the comparison site.
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
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;

public class TransitOverrideThresholdTrace extends GhidraScript {

    private static final long[] TARGETS = {
        0x00FD29D4L,   // +0.8 Nm candidate (quiet-gate upper)
        0x00FD29E0L    // -0.8 Nm candidate (quiet-gate lower)
    };
    private static final long BAND_RADIUS = 0x40;

    private static final String OUT_DIR = "/tmp/pscm/transit_override";

    private long firstScalar(Instruction ins) {
        for (int op = 0; op < ins.getNumOperands(); op++) {
            for (Object o : ins.getOpObjects(op)) {
                if (o instanceof Scalar) return ((Scalar) o).getUnsignedValue();
            }
        }
        return Long.MIN_VALUE;
    }

    private boolean inBand(long v) {
        for (long t : TARGETS) {
            if (v >= t - BAND_RADIUS && v < t + BAND_RADIUS + 4) return true;
        }
        return false;
    }

    @Override
    public void run() throws Exception {
        Files.createDirectories(Paths.get(OUT_DIR));

        FunctionManager fm = currentProgram.getFunctionManager();
        Listing listing = currentProgram.getListing();
        ReferenceManager rm = currentProgram.getReferenceManager();
        AddressSpace sp = currentProgram.getAddressFactory().getDefaultAddressSpace();

        StringBuilder xrefOut = new StringBuilder();
        xrefOut.append("=== Ghidra xrefs to cal+0x29D4 / 0x29E0 ===\n");
        Set<Function> xrefFuncs = new LinkedHashSet<>();
        for (long t : TARGETS) {
            xrefOut.append(String.format("\n--- 0x%08x ---\n", t));
            Address a = sp.getAddress(t);
            for (Reference r : rm.getReferencesTo(a)) {
                Address src = r.getFromAddress();
                Function f = fm.getFunctionContaining(src);
                String fn = f != null ? f.getName() : "<none>";
                long fe = f != null ? f.getEntryPoint().getOffset() : 0L;
                xrefOut.append(String.format("  from=0x%08x  %s @ 0x%08x  type=%s\n",
                    src.getOffset(), fn, fe, r.getReferenceType()));
                if (f != null) xrefFuncs.add(f);
            }
        }

        // Global movhi+movea pair scan within BAND
        xrefOut.append("\n=== Global movhi+movea/addi into cal+0x29D4..29E0 band ===\n");
        InstructionIterator it = listing.getInstructions(true);
        Instruction prev = null;
        Map<Function, Integer> bandFuncs = new LinkedHashMap<>();
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
                    if (inBand(v)) {
                        Function f = fm.getFunctionContaining(ins.getAddress());
                        String fn = f != null ? f.getName() : "<none>";
                        long fe = f != null ? f.getEntryPoint().getOffset() : 0L;
                        xrefOut.append(String.format("  @0x%08x  %s+%s  ptr=0x%08x  fn=%s @0x%08x\n",
                            prev.getAddress().getOffset(), prev.getMnemonicString(),
                            ins.getMnemonicString(), v, fn, fe));
                        if (f != null) {
                            bandFuncs.merge(f, 1, Integer::sum);
                            xrefFuncs.add(f);
                        }
                    }
                }
            }
            prev = ins;
        }

        // Also check GP-relative / immediate scalar loads of the literal values 0x00FD29D4 etc.
        xrefOut.append("\n=== Scalar immediates matching target addresses ===\n");
        for (Function f : fm.getFunctions(true)) {
            if (monitor.isCancelled()) break;
            InstructionIterator fit = listing.getInstructions(f.getBody(), true);
            int hits = 0;
            while (fit.hasNext()) {
                Instruction ins = fit.next();
                for (int op = 0; op < ins.getNumOperands(); op++) {
                    for (Object o : ins.getOpObjects(op)) {
                        if (o instanceof Scalar) {
                            long v = ((Scalar) o).getUnsignedValue() & 0xffffffffL;
                            if (inBand(v)) {
                                xrefOut.append(String.format("  @0x%08x  %s %s  v=0x%08x  fn=%s @0x%08x\n",
                                    ins.getAddress().getOffset(), ins.getMnemonicString(),
                                    ins.toString(), v, f.getName(), f.getEntryPoint().getOffset()));
                                hits++;
                                xrefFuncs.add(f);
                            }
                        }
                    }
                }
            }
        }

        Files.writeString(Paths.get(OUT_DIR, "xrefs.txt"), xrefOut.toString());
        println("xrefs.txt: " + xrefFuncs.size() + " distinct functions touch the band");

        // Decompile each function that hit, into per-function .c files
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        StringBuilder summary = new StringBuilder();
        summary.append("=== Decompiled candidates ===\n");
        for (Function f : xrefFuncs) {
            if (monitor.isCancelled()) break;
            try {
                DecompileResults res = di.decompileFunction(f, 60, monitor);
                String code = res.getDecompiledFunction() != null
                    ? res.getDecompiledFunction().getC()
                    : "/* decompile failed: " + res.getErrorMessage() + " */\n";
                String fname = String.format("%08x_%s.c",
                    f.getEntryPoint().getOffset(),
                    f.getName().replaceAll("[^A-Za-z0-9_]", "_"));
                Files.writeString(Paths.get(OUT_DIR, fname), code);
                int lines = code.split("\n").length;
                summary.append(String.format("  %s @ 0x%08x  lines=%d  -> %s\n",
                    f.getName(), f.getEntryPoint().getOffset(), lines, fname));
            } catch (Exception e) {
                summary.append(String.format("  %s @ 0x%08x  DECOMPILE-ERROR: %s\n",
                    f.getName(), f.getEntryPoint().getOffset(), e.getMessage()));
            }
        }
        di.dispose();
        Files.writeString(Paths.get(OUT_DIR, "_SUMMARY.txt"), summary.toString());
        println(summary.toString());
    }
}
