// Dump one specific function and its call edges for quick inspection.
// @category Probe
// @runtime Java

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressFactory;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.listing.Listing;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.ReferenceManager;

public class F150DumpTarget extends GhidraScript {
    @Override
    public void run() throws Exception {
        AddressFactory af = currentProgram.getAddressFactory();
        FunctionManager fm = currentProgram.getFunctionManager();
        ReferenceManager rm = currentProgram.getReferenceManager();
        Listing listing = currentProgram.getListing();
        long[] targets = {
            0x1005cb56L,
            0x10086da6L,
            0x100871baL,
            0x1008791eL,
            0x10087ec8L,
        };

        for (long target : targets) {
            Address a = af.getDefaultAddressSpace().getAddress(target);
            Function f = fm.getFunctionAt(a);
            if (f == null) {
                println("no function at 0x" + Long.toHexString(target));
                continue;
            }

            println("\n============================================================");
            println(String.format("FUNCTION %s @ 0x%08x size=%d",
                f.getName(), f.getEntryPoint().getOffset(), f.getBody().getNumAddresses()));

            println("\nCALLERS:");
            ReferenceIterator refs = rm.getReferencesTo(a);
            while (refs.hasNext()) {
                Reference r = refs.next();
                if (r.getReferenceType().isCall() || r.getReferenceType().isJump()) {
                    Function caller = fm.getFunctionContaining(r.getFromAddress());
                    println(String.format("  from 0x%08x in %s",
                        r.getFromAddress().getOffset(),
                        caller != null ? caller.getName() + String.format(" @ 0x%08x", caller.getEntryPoint().getOffset()) : "<no function>"));
                }
            }

            println("\nCALLEES:");
            InstructionIterator it = listing.getInstructions(f.getBody(), true);
            while (it.hasNext()) {
                Instruction ins = it.next();
                for (Reference r : ins.getReferencesFrom()) {
                    if (r.getReferenceType().isCall()) {
                        Function callee = fm.getFunctionAt(r.getToAddress());
                        println(String.format("  0x%08x -> %s",
                            ins.getAddress().getOffset(),
                            callee != null ? callee.getName() + String.format(" @ 0x%08x", callee.getEntryPoint().getOffset()) : r.getToAddress().toString()));
                    }
                }
            }

            DecompInterface di = new DecompInterface();
            di.openProgram(currentProgram);
            DecompileResults res = di.decompileFunction(f, 30, monitor);
            println("\nDECOMPILE:\n");
            if (res != null && res.getDecompiledFunction() != null) {
                println(res.getDecompiledFunction().getC());
            }
            else {
                println("<decompile failed>");
            }
        }
    }
}
