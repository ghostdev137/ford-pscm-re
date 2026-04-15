// Dump the 3 APA task sub-functions
// @category Pipeline
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import java.io.*;
import java.nio.file.*;

public class F150APA_Dump extends GhidraScript {
    @Override
    public void run() throws Exception {
        Path out = Paths.get("/tmp/pscm/f150_apa");
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        FunctionManager fm = currentProgram.getFunctionManager();
        AddressFactory af = currentProgram.getAddressFactory();
        for (long t : new long[]{0x1018466eL, 0x101848acL}) {
            Address a = af.getDefaultAddressSpace().getAddress(t);
            Function f = fm.getFunctionAt(a);
            if (f == null) continue;
            DecompileResults r = di.decompileFunction(f, 60, monitor);
            String c = (r != null && r.getDecompiledFunction() != null) ? r.getDecompiledFunction().getC() : "// failed";
            Files.writeString(out.resolve(String.format("%08x.c", t)),
                String.format("// %s size=%d\n%s", f.getName(), f.getBody().getNumAddresses(), c));
            println("wrote 0x"+Long.toHexString(t));
        }
    }
}
