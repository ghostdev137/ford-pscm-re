// Dump the 6 callers of the shared angle-read function to find per-mode clamps.
// @category Pipeline
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import java.io.*;
import java.nio.file.*;

public class F150DumpModes extends GhidraScript {
    @Override
    public void run() throws Exception {
        long[] targets = {
            0x10186afaL, 0x10180044L, 0x101a4d56L,
            0x101aa05eL, 0x101ab934L, 0x101ad86cL,
            0x101a4e4aL,  // third in LKA task
        };
        Path out = Paths.get("/tmp/pscm/f150_lka");
        Files.createDirectories(out);
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        FunctionManager fm = currentProgram.getFunctionManager();
        AddressFactory af = currentProgram.getAddressFactory();
        for (long t : targets) {
            Address a = af.getDefaultAddressSpace().getAddress(t);
            Function f = fm.getFunctionAt(a);
            if (f == null) { println("no func 0x"+Long.toHexString(t)); continue; }
            DecompileResults r = di.decompileFunction(f, 30, monitor);
            String code = r != null && r.getDecompiledFunction() != null ? r.getDecompiledFunction().getC() : "// decomp failed\n";
            Files.writeString(out.resolve(String.format("mode_%08x.c", t)),
                String.format("// %s size=%d\n%s", f.getName(), f.getBody().getNumAddresses(), code));
            println("wrote mode_0x" + Long.toHexString(t));
        }
    }
}
