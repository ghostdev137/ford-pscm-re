// Dump one function decompile to /tmp/pscm/f150_lka/
// @category Pipeline
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import java.io.*;
import java.nio.file.*;

public class F150DumpOne extends GhidraScript {
    @Override
    public void run() throws Exception {
        long t = 0x101a4d56L;
        Path out = Paths.get("/tmp/pscm/f150_lka");
        Files.createDirectories(out);
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        FunctionManager fm = currentProgram.getFunctionManager();
        ReferenceManager rm = currentProgram.getReferenceManager();
        AddressFactory af = currentProgram.getAddressFactory();
        Address a = af.getDefaultAddressSpace().getAddress(t);
        Function f = fm.getFunctionAt(a);
        if (f == null) { println("no func"); return; }
        StringBuilder sb = new StringBuilder();
        sb.append(String.format("// %s @ 0x%08x size=%d\n", f.getName(), t, f.getBody().getNumAddresses()));
        sb.append("// CALLERS:\n");
        ReferenceIterator refs = rm.getReferencesTo(a);
        int n=0;
        while (refs.hasNext() && n<15) {
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
