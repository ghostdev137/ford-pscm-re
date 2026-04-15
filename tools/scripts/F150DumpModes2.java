// Long-timeout dump of remaining mode wrappers + find writers to final torque output.
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

public class F150DumpModes2 extends GhidraScript {
    @Override
    public void run() throws Exception {
        Path out = Paths.get("/tmp/pscm/f150_lka");
        Files.createDirectories(out);
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        FunctionManager fm = currentProgram.getFunctionManager();
        ReferenceManager rm = currentProgram.getReferenceManager();
        AddressFactory af = currentProgram.getAddressFactory();

        // Long timeout for the BlueCruise monster
        long[] bigTargets = {0x10186afaL, 0x101ab934L};
        for (long t : bigTargets) {
            Address a = af.getDefaultAddressSpace().getAddress(t);
            Function f = fm.getFunctionAt(a);
            if (f == null) { println("no func 0x"+Long.toHexString(t)); continue; }
            println("decompiling " + f.getName() + " size=" + f.getBody().getNumAddresses() + " (may take minutes)");
            DecompileResults r = di.decompileFunction(f, 300, monitor);
            String code = r != null && r.getDecompiledFunction() != null ? r.getDecompiledFunction().getC() : "// decomp failed\n";
            Files.writeString(out.resolve(String.format("bigmode_%08x.c", t)), code);
            println("  wrote " + code.length() + " bytes");
        }

        // Find writers to final torque output _DAT_fef21a78 and authority gain _DAT_fef2642e
        long[] writeTargets = {0xfef21a78L, 0xfef2642eL, 0xfef21a62L, 0xfef21a65L};
        for (long t : writeTargets) {
            Address a = af.getDefaultAddressSpace().getAddress(t);
            println("\n=== refs TO 0x"+Long.toHexString(t));
            ReferenceIterator refs = rm.getReferencesTo(a);
            Set<Function> writers = new LinkedHashSet<>();
            Set<Function> readers = new LinkedHashSet<>();
            while (refs.hasNext()) {
                Reference r = refs.next();
                Function f = fm.getFunctionContaining(r.getFromAddress());
                if (f == null) continue;
                if (r.getReferenceType().isWrite()) writers.add(f);
                else if (r.getReferenceType().isRead()) readers.add(f);
            }
            for (Function f : writers)
                println(String.format("  WRITE by %s @0x%08x (size=%d)", f.getName(), f.getEntryPoint().getOffset(), f.getBody().getNumAddresses()));
            int nr=0; for (Function f : readers) {
                println(String.format("  READ by %s @0x%08x", f.getName(), f.getEntryPoint().getOffset()));
                if (++nr >= 6) { println("  ... more readers"); break; }
            }
        }
    }
}
