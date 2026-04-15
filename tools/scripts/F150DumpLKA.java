// Dump decompile + callers for F150 LKA candidates.
// @category Pipeline
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import java.io.*;
import java.nio.file.*;

public class F150DumpLKA extends GhidraScript {
    @Override
    public void run() throws Exception {
        long[] targets = {0x10088d64L, 0x101a3b84L, 0x1005f5b0L, 0x10065b7cL, 0x10180044L};
        Path out = Paths.get("/tmp/pscm/f150_lka");
        Files.createDirectories(out);
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        FunctionManager fm = currentProgram.getFunctionManager();
        ReferenceManager rm = currentProgram.getReferenceManager();
        AddressFactory af = currentProgram.getAddressFactory();
        for (long t : targets) {
            Address a = af.getDefaultAddressSpace().getAddress(t);
            Function f = fm.getFunctionAt(a);
            if (f == null) { println("no func at 0x" + Long.toHexString(t)); continue; }
            StringBuilder sb = new StringBuilder();
            sb.append(String.format("// %s @ 0x%08x size=%d\n", f.getName(), t, f.getBody().getNumAddresses()));
            sb.append("// CALLERS:\n");
            ReferenceIterator refs = rm.getReferencesTo(a);
            int callerCount = 0;
            while (refs.hasNext()) {
                Reference r = refs.next();
                if (r.getReferenceType().isCall() || r.getReferenceType().isJump()) {
                    Function caller = fm.getFunctionContaining(r.getFromAddress());
                    sb.append(String.format("//   from 0x%08x  in %s\n",
                        r.getFromAddress().getOffset(),
                        caller != null ? caller.getName() : "?"));
                    callerCount++;
                    if (callerCount > 10) { sb.append("//   ... and more\n"); break; }
                }
            }
            DecompileResults r = di.decompileFunction(f, 30, monitor);
            if (r != null && r.getDecompiledFunction() != null) {
                sb.append(r.getDecompiledFunction().getC());
            } else {
                sb.append("// decompile failed\n");
            }
            Files.writeString(out.resolve(String.format("%08x.c", t)), sb.toString());
            println("wrote 0x" + Long.toHexString(t) + " (" + callerCount + " callers)");
        }
    }
}
