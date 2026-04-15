// Find F150 APA cal-gain tables. Strategy: the helper functions FUN_10183768/846/984/92e/100977a6
// each take `(key, cal_a, cal_b, cal_c, cal_d)` args — the cals are breakpoint table pointers.
// Dump them + their callers to see where the speed-gain tables live.
// @category Pipeline
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import java.io.*;
import java.nio.file.*;

public class F150APAGainTables extends GhidraScript {
    @Override
    public void run() throws Exception {
        Path out = Paths.get("/tmp/pscm/f150_apa");
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        FunctionManager fm = currentProgram.getFunctionManager();
        AddressFactory af = currentProgram.getAddressFactory();
        for (long t : new long[]{0x10183768L, 0x10183846L, 0x10183984L, 0x1018392eL, 0x100977a6L}) {
            Address a = af.getDefaultAddressSpace().getAddress(t);
            Function f = fm.getFunctionAt(a);
            if (f == null) { println("no func 0x"+Long.toHexString(t)); continue; }
            DecompileResults r = di.decompileFunction(f, 60, monitor);
            String c = (r != null && r.getDecompiledFunction() != null) ? r.getDecompiledFunction().getC() : "// failed";
            Files.writeString(out.resolve(String.format("helper_%08x.c", t)),
                String.format("// %s size=%d\n%s", f.getName(), f.getBody().getNumAddresses(), c));
            println("wrote helper 0x"+Long.toHexString(t));
        }
    }
}
