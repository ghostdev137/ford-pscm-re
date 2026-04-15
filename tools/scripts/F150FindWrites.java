// Find functions that WRITE to specific RAM globals (likely CAN RX side).
// @category Pipeline
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import java.util.*;

public class F150FindWrites extends GhidraScript {
    @Override
    public void run() throws Exception {
        // RAM globals used by the LKA rate-limiter (0x101a3b84):
        // _DAT_fef21a6e (angle?), _DAT_fef21a70, _DAT_fef21a72, _DAT_fef20ff0, _DAT_fef21026
        long[] targets = {
            0xfef21a6eL, 0xfef21a70L, 0xfef21a72L, 0xfef20ff0L, 0xfef21026L,
            0xfef21a20L, 0xfef21a3aL, 0xfef2105cL,
        };
        AddressFactory af = currentProgram.getAddressFactory();
        AddressSpace asp = af.getDefaultAddressSpace();
        ReferenceManager rm = currentProgram.getReferenceManager();
        FunctionManager fm = currentProgram.getFunctionManager();
        for (long t : targets) {
            Address a = asp.getAddress(t);
            println(String.format("\n=== refs TO 0x%08x", t));
            ReferenceIterator refs = rm.getReferencesTo(a);
            Set<Function> writerFuncs = new LinkedHashSet<>();
            while (refs.hasNext()) {
                Reference r = refs.next();
                if (r.getReferenceType().isWrite()) {
                    Function f = fm.getFunctionContaining(r.getFromAddress());
                    if (f != null) writerFuncs.add(f);
                }
            }
            for (Function f : writerFuncs) {
                println(String.format("  WRITES from %s @ 0x%08x (size=%d)",
                    f.getName(), f.getEntryPoint().getOffset(), f.getBody().getNumAddresses()));
            }
        }
    }
}
