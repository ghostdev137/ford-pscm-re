// Dump LKA control, find motor-driver reader of fef21a78, find LCA output writer.
// @category Pipeline
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;

public class F150FullMap2 extends GhidraScript {
    @Override
    public void run() throws Exception {
        Path out = Paths.get("/tmp/pscm/f150_lka");
        Files.createDirectories(out);
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        FunctionManager fm = currentProgram.getFunctionManager();
        ReferenceManager rm = currentProgram.getReferenceManager();
        AddressFactory af = currentProgram.getAddressFactory();
        AddressSpace asp = af.getDefaultAddressSpace();
        StringBuilder report = new StringBuilder();

        // 1. Dump FUN_101a4f2a (missed LKA function)
        for (long t : new long[]{0x101a4f2aL, 0x101ae572L, 0x101ac6a8L, 0x101af182L, 0x101b000cL}) {
            Address a = asp.getAddress(t);
            Function f = fm.getFunctionAt(a);
            if (f == null) continue;
            DecompileResults r = di.decompileFunction(f, 60, monitor);
            String c = (r != null && r.getDecompiledFunction() != null) ? r.getDecompiledFunction().getC() : "// failed\n";
            Files.writeString(out.resolve(String.format("lca_%08x.c", t)),
                String.format("// %s size=%d\n%s", f.getName(), f.getBody().getNumAddresses(), c));
            println("wrote " + f.getName() + " (" + c.length() + " bytes)");
        }

        // 2. Find who READS fef21a78 (final LKA output) — those are the motor-driver consumers
        report.append("\n=== READERS of fef21a78 (final LKA torque) ===\n");
        ReferenceIterator refs = rm.getReferencesTo(asp.getAddress(0xfef21a78L));
        Set<Function> readers = new LinkedHashSet<>();
        while (refs.hasNext()) {
            Reference r = refs.next();
            Function f = fm.getFunctionContaining(r.getFromAddress());
            if (f == null) continue;
            if (r.getReferenceType().isRead()) readers.add(f);
        }
        for (Function f : readers)
            report.append(String.format("  %s @0x%x size=%d\n",
                f.getName(), f.getEntryPoint().getOffset(), f.getBody().getNumAddresses()));

        // 3. In the LCA writer candidates, look for a function that matches the LKA-output signature:
        //    (a) small size (~88), (b) writes exactly 1 global, (c) contains ±0x5000 / ±0x2800 type clamp
        report.append("\n=== LCA output candidates (small funcs writing few LCA globals) ===\n");
        long[] lcaWriters = {0x101ab934L, 0x101ae572L, 0x101ac6a8L, 0x101af182L, 0x101b000cL,
                             0x101ad5a4L, 0x101aef34L, 0x101adb5aL, 0x101aaf16L, 0x101aa05eL,
                             0x101ad86cL};
        for (long t : lcaWriters) {
            Address a = asp.getAddress(t);
            Function f = fm.getFunctionAt(a);
            if (f == null) continue;
            // Count immediates matching known clamp shapes
            Listing L = currentProgram.getListing();
            InstructionIterator it = L.getInstructions(f.getBody(), true);
            Map<Long,Integer> clamps = new TreeMap<>();
            while (it.hasNext()) {
                Instruction ins = it.next();
                for (int op = 0; op < ins.getNumOperands(); op++) {
                    for (Object o : ins.getOpObjects(op)) {
                        if (o instanceof ghidra.program.model.scalar.Scalar) {
                            long v = ((ghidra.program.model.scalar.Scalar)o).getSignedValue();
                            long av = Math.abs(v);
                            if (av == 0x2800L || av == 0x5000L || av == 0x6400L || av == 0x7FFF
                                || av == 0x4000L || av == 0x8000L || av == 0x1000L || av == 0x2000L) {
                                clamps.merge(v, 1, Integer::sum);
                            }
                        }
                    }
                }
            }
            if (!clamps.isEmpty()) {
                report.append(String.format("  %s @0x%x size=%d clamps=%s\n",
                    f.getName(), t, f.getBody().getNumAddresses(), clamps));
            }
        }

        Files.writeString(out.resolve("_fullmap2.txt"), report.toString());
        println("wrote _fullmap2.txt");
    }
}
