// Dump multiple specific functions by address (passed via env var)
// @category Pipeline
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import java.io.*;
import java.nio.file.*;

public class F150DumpCallers extends GhidraScript {
    @Override
    public void run() throws Exception {
        long[] targets = {
            0x100586d0L,  // caller of 0x1005f5b0
            0x100561e8L, 0x100561feL, 0x10056214L,  // the signal setter series
            0x1005622aL, 0x10056242L,
            0x101a3b84L,  // 2048 hotspot
        };
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
            int n=0;
            ReferenceIterator refs = rm.getReferencesTo(a);
            while (refs.hasNext() && n<15) {
                Reference r = refs.next();
                if (r.getReferenceType().isCall() || r.getReferenceType().isJump()) {
                    Function caller = fm.getFunctionContaining(r.getFromAddress());
                    sb.append(String.format("//   from 0x%08x  in %s\n", r.getFromAddress().getOffset(),
                        caller != null ? caller.getName() + String.format(" @ 0x%x", caller.getEntryPoint().getOffset()) : "?"));
                    n++;
                }
            }
            DecompileResults r = di.decompileFunction(f, 30, monitor);
            if (r != null && r.getDecompiledFunction() != null) sb.append(r.getDecompiledFunction().getC());
            Files.writeString(out.resolve(String.format("%08x.c", t)), sb.toString());
            println("wrote 0x" + Long.toHexString(t));
        }
    }
}
