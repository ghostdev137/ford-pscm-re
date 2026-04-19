// Resolve containing functions for a set of interesting raw-hit addresses and optionally decompile them.
// @category Probe
// @runtime Java

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressFactory;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;

public class F150AddrToFunc extends GhidraScript {
    @Override
    public void run() throws Exception {
        long[] addrs = {
            0x10045854L,
            0x1008e360L,
            0x100a0483L,
            0x100a1331L,
            0x100d29cbL,
            0x1009ab9aL,
            0x1009ac2eL,
            0x1009ac68L,
            0x1009acb6L,
            0x1009acd4L,
            0x1009ad00L,
            0x1009afaaL,
            0x1009b012L,
            0x1009b348L,
            0x1009b47cL,
            0x1009b732L,
            0x1009b8faL,
        };

        AddressFactory af = currentProgram.getAddressFactory();
        FunctionManager fm = currentProgram.getFunctionManager();
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);

        for (long raw : addrs) {
            Address a = af.getDefaultAddressSpace().getAddress(raw);
            Function f = fm.getFunctionContaining(a);
            println("\n============================================================");
            println(String.format("ADDR 0x%08x", raw));
            if (f == null) {
                try {
                    disassemble(a);
                    f = createFunction(a, null);
                }
                catch (Exception e) {
                    // Keep going; some targets may still be data.
                }
            }
            if (f == null) {
                println("  no containing function");
                continue;
            }
            println(String.format("  in %s @ 0x%08x size=%d",
                f.getName(), f.getEntryPoint().getOffset(), f.getBody().getNumAddresses()));
            DecompileResults res = di.decompileFunction(f, 30, monitor);
            if (res != null && res.getDecompiledFunction() != null) {
                println("\n" + res.getDecompiledFunction().getC());
            }
        }
    }
}
