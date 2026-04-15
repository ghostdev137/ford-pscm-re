// Dump FUN_10097a04 to identify which CAN buffer it indexes
// @category Pipeline
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import java.io.*;
import java.nio.file.*;

public class F150APA_Trace extends GhidraScript {
    @Override
    public void run() throws Exception {
        Path out = Paths.get("/tmp/pscm/f150_apa");
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        FunctionManager fm = currentProgram.getFunctionManager();
        ReferenceManager rm = currentProgram.getReferenceManager();
        AddressFactory af = currentProgram.getAddressFactory();

        // FUN_10097a04 is the per-byte reader; similar FUN_10097a52 is the writer
        for (long t : new long[]{0x10097a04L, 0x10097a52L, 0x100978d4L, 0x100978dcL}) {
            Address a = af.getDefaultAddressSpace().getAddress(t);
            Function f = fm.getFunctionAt(a);
            if (f == null) continue;
            DecompileResults r = di.decompileFunction(f, 30, monitor);
            String c = (r != null && r.getDecompiledFunction() != null) ? r.getDecompiledFunction().getC() : "// failed";
            Files.writeString(out.resolve(String.format("shim_%08x.c", t)),
                String.format("// %s size=%d\n%s", f.getName(), f.getBody().getNumAddresses(), c));
            println("wrote shim 0x" + Long.toHexString(t));
        }
    }
}
