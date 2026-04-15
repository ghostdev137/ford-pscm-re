// Dump many specific funcs at once
// @category Pipeline
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import java.io.*;
import java.nio.file.*;

public class F150DumpMany extends GhidraScript {
    @Override
    public void run() throws Exception {
        long[] targets = {
            0x1017fbe0L,  // LKA main task (caller of RX unpacker + rate limiter)
            0x100968eaL,  // Com_Recv angle shim
            0x10096e72L,  // Com_Recv A
            0x10096b1eL,  // Com_Recv B
            0x100978bcL,  // Com_Recv C
            0x1009691eL,  // Com_Recv D
            0x10096f40L,  // Com_Recv curvature 1
            0x10096f38L,  // Com_Recv curvature 2
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
            ReferenceIterator refs = rm.getReferencesTo(a);
            int n=0;
            while (refs.hasNext() && n<8) {
                Reference r = refs.next();
                if (r.getReferenceType().isCall() || r.getReferenceType().isJump()) {
                    Function caller = fm.getFunctionContaining(r.getFromAddress());
                    sb.append(String.format("//   from 0x%08x  in %s\n", r.getFromAddress().getOffset(),
                        caller != null ? caller.getName() : "?"));
                    n++;
                }
            }
            DecompileResults r = di.decompileFunction(f, 30, monitor);
            if (r != null) sb.append(r.getDecompiledFunction().getC());
            Files.writeString(out.resolve(String.format("%08x.c", t)), sb.toString());
            println("wrote 0x" + Long.toHexString(t));
        }
    }
}
