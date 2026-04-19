// Dump a comma-separated list of functions to /tmp/pscm/f150_lka/.
// Usage: set F150_DUMP_ADDRS=0x10123456,0x1012789a
// @category Pipeline
// @runtime Java
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressFactory;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.ReferenceManager;

import java.nio.file.Files;
import java.nio.file.Path;

public class F150DumpFunctionList extends GhidraScript {
    @Override
    public void run() throws Exception {
        String raw = System.getenv("F150_DUMP_ADDRS");
        if (raw == null || raw.trim().isEmpty()) {
            println("Set F150_DUMP_ADDRS to a comma-separated list of function entry addresses.");
            return;
        }

        Path out = Path.of(System.getenv().getOrDefault(
            "F150_DUMP_OUT_DIR", "/tmp/pscm/f150_lka/dumps"));
        Files.createDirectories(out);

        AddressFactory af = currentProgram.getAddressFactory();
        FunctionManager fm = currentProgram.getFunctionManager();
        ReferenceManager rm = currentProgram.getReferenceManager();
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);

        for (String piece : raw.split(",")) {
            String s = piece.trim().toLowerCase();
            if (s.isEmpty()) {
                continue;
            }
            long addr = s.startsWith("0x") ? Long.parseUnsignedLong(s.substring(2), 16)
                                           : Long.parseUnsignedLong(s, 16);
            Address a = af.getDefaultAddressSpace().getAddress(addr);
            Function f = fm.getFunctionAt(a);
            if (f == null) {
                println("no function at 0x" + Long.toHexString(addr));
                continue;
            }

            StringBuilder sb = new StringBuilder();
            sb.append(String.format("// %s @ 0x%08x size=%d\n",
                f.getName(), f.getEntryPoint().getOffset(), f.getBody().getNumAddresses()));
            sb.append("// CALLERS:\n");
            ReferenceIterator refs = rm.getReferencesTo(a);
            int n = 0;
            while (refs.hasNext() && n < 16) {
                Reference r = refs.next();
                if (r.getReferenceType().isCall() || r.getReferenceType().isJump()) {
                    Function caller = fm.getFunctionContaining(r.getFromAddress());
                    sb.append(String.format("//   from 0x%08x in %s\n",
                        r.getFromAddress().getOffset(),
                        caller != null ? caller.getName() + String.format(" @ 0x%08x", caller.getEntryPoint().getOffset()) : "<no function>"));
                    n++;
                }
            }
            sb.append('\n');

            DecompileResults res = di.decompileFunction(f, 60, monitor);
            if (res != null && res.getDecompiledFunction() != null) {
                sb.append(res.getDecompiledFunction().getC());
            } else {
                sb.append("// decompile failed\n");
            }

            Path dst = out.resolve(String.format("%08x_%s.c", addr, f.getName()));
            Files.writeString(dst, sb.toString());
            println("wrote " + dst);
        }
    }
}
