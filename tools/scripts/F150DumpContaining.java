// Dump the functions containing a list of absolute addresses.
// @category Pipeline
// @runtime Java
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressFactory;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;

import java.nio.file.Files;
import java.nio.file.Path;

public class F150DumpContaining extends GhidraScript {
    @Override
    public void run() throws Exception {
        long[] targets = {
            0x101a20f8L,
            0x1018a062L,
            0x10096f38L,
            0x10096f40L,
            0x100968eaL
        };

        Path out = Path.of(System.getenv().getOrDefault(
            "F150_DUMP_CONTAINING_OUT", "/tmp/pscm/f150_torque_source"));
        Files.createDirectories(out);

        AddressFactory af = currentProgram.getAddressFactory();
        FunctionManager fm = currentProgram.getFunctionManager();
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);

        for (long t : targets) {
            Address a = af.getDefaultAddressSpace().getAddress(t);
            Function f = fm.getFunctionContaining(a);
            if (f == null) {
                println(String.format("no containing function for 0x%x", t));
                continue;
            }

            DecompileResults r = di.decompileFunction(f, 60, monitor);
            String code = (r != null && r.getDecompiledFunction() != null)
                ? r.getDecompiledFunction().getC()
                : "// decomp failed\n";

            String header = String.format(
                "// contains 0x%08x\n// %s @ 0x%08x size=%d\n",
                t, f.getName(), f.getEntryPoint().getOffset(), f.getBody().getNumAddresses());
            Files.writeString(out.resolve(String.format("%08x_%s.c",
                f.getEntryPoint().getOffset(), f.getName())), header + code);
            println(String.format("wrote containing function for 0x%x -> %s", t, f.getName()));
        }
    }
}
