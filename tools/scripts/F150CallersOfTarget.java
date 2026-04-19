// Force a function at a target and dump its callers.
// @category Probe
// @runtime Java

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressFactory;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.ReferenceManager;

public class F150CallersOfTarget extends GhidraScript {
    @Override
    public void run() throws Exception {
        long target = 0x10045854L;
        AddressFactory af = currentProgram.getAddressFactory();
        Address a = af.getDefaultAddressSpace().getAddress(target);
        FunctionManager fm = currentProgram.getFunctionManager();
        ReferenceManager rm = currentProgram.getReferenceManager();

        Function f = fm.getFunctionContaining(a);
        if (f == null) {
            disassemble(a);
            f = createFunction(a, null);
        }

        println(String.format("TARGET 0x%08x -> %s",
            target, f != null ? f.getName() + String.format(" @ 0x%08x", f.getEntryPoint().getOffset()) : "<no function>"));

        ReferenceIterator refs = rm.getReferencesTo(a);
        while (refs.hasNext()) {
            Reference r = refs.next();
            if (r.getReferenceType().isCall() || r.getReferenceType().isJump()) {
                Function caller = fm.getFunctionContaining(r.getFromAddress());
                println(String.format("  caller from 0x%08x in %s",
                    r.getFromAddress().getOffset(),
                    caller != null ? caller.getName() + String.format(" @ 0x%08x", caller.getEntryPoint().getOffset()) : "<no function>"));
            }
        }
    }
}
