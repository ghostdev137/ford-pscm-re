// F-150 analog of TransitOverrideThresholdTrace. Hunts xrefs + decompiles
// functions that read the -0.8 LE float singleton at 0x101D7A5C and its
// adjacent hysteresis-family floats. F-150 RH850 project decompiles
// cleaner than Transit, so this is the fastest path to understanding
// the driver-override quiet-gate algorithm.
// @category F150
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

public class F150OverrideThresholdTrace extends GhidraScript {
    // F-150 cal hysteresis family addresses (LE floats)
    // 0x101d7a5c = -0.8 (singleton)
    // 0x101d7a60 = -0.5
    // 0x101d7a70 = +0.5
    // +0.8 does not appear adjacent — F-150 may use a different symmetric
    // pattern (e.g., -0.8/-0.5 for one direction and compute the mirror).
    private static final long[] TARGETS = {
        0x101D7A4CL, 0x101D7A50L, 0x101D7A54L, 0x101D7A58L,
        0x101D7A5CL,   // -0.8
        0x101D7A60L,   // -0.5
        0x101D7A64L, 0x101D7A68L, 0x101D7A6CL, 0x101D7A70L,  // +0.5
        0x101D7A74L
    };
    private static final long BAND_RADIUS = 0x40;
    private static final String OUT_DIR = "/tmp/pscm/f150_override";

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
        xrefOut.append("=== F-150 xrefs to -0.8 neighborhood (0x101D7A4C..7A74) ===\n");
        Set<Function> hit = new LinkedHashSet<>();

        for (long t : TARGETS) {
            Address a = sp.getAddress(t);
            int n = 0;
            for (Reference r : rm.getReferencesTo(a)) {
                Address src = r.getFromAddress();
                Function f = fm.getFunctionContaining(src);
                String fn = f != null ? f.getName() : "<none>";
                long fe = f != null ? f.getEntryPoint().getOffset() : 0L;
                xrefOut.append(String.format("  to=0x%08x  from=0x%08x  %s @ 0x%08x  %s\n",
                    t, src.getOffset(), fn, fe, r.getReferenceType()));
                n++;
                if (f != null) hit.add(f);
            }
            if (n == 0) xrefOut.append(String.format("  to=0x%08x  <no xrefs>\n", t));
        }

        // Also scan movhi+movea/addi for any pointer construction into band.
        xrefOut.append("\n=== Global movhi+movea into band ===\n");
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
                    if (inBand(v)) {
                        Function f = fm.getFunctionContaining(ins.getAddress());
                        String fn = f != null ? f.getName() : "<none>";
                        long fe = f != null ? f.getEntryPoint().getOffset() : 0L;
                        xrefOut.append(String.format("  @0x%08x  ptr=0x%08x  fn=%s @0x%08x\n",
                            prev.getAddress().getOffset(), v, fn, fe));
                        if (f != null) hit.add(f);
                    }
                }
            }
            prev = ins;
        }

        // And immediate scalar scan (same-function)
        xrefOut.append("\n=== Scalar immediate match in band ===\n");
        for (Function f : fm.getFunctions(true)) {
            if (monitor.isCancelled()) break;
            InstructionIterator fi = listing.getInstructions(f.getBody(), true);
            int n = 0;
            while (fi.hasNext()) {
                Instruction ins = fi.next();
                for (int op = 0; op < ins.getNumOperands(); op++) {
                    for (Object o : ins.getOpObjects(op)) {
                        if (o instanceof Scalar) {
                            long v = ((Scalar) o).getUnsignedValue() & 0xFFFFFFFFL;
                            if (inBand(v)) { n++; hit.add(f); }
                        }
                    }
                }
            }
            if (n > 0) {
                xrefOut.append(String.format("  %s @ 0x%08x  scalar_hits=%d\n",
                    f.getName(), f.getEntryPoint().getOffset(), n));
            }
        }

        Files.writeString(Paths.get(OUT_DIR, "xrefs.txt"), xrefOut.toString());
        println("xrefs.txt: " + hit.size() + " distinct functions");

        // Decompile each hit function
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        StringBuilder summary = new StringBuilder();
        summary.append("=== Decompiled candidates ===\n");
        for (Function f : hit) {
            if (monitor.isCancelled()) break;
            try {
                DecompileResults res = di.decompileFunction(f, 90, monitor);
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
                summary.append(String.format("  %s @ 0x%08x  ERROR: %s\n",
                    f.getName(), f.getEntryPoint().getOffset(), e.getMessage()));
            }
        }
        di.dispose();
        Files.writeString(Paths.get(OUT_DIR, "_SUMMARY.txt"), summary.toString());
        println(summary.toString());
    }
}
