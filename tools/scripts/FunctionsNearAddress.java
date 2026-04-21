// List functions near a specific address; find the containing function,
// its preceding function, and its following function.
// @category Transit
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSpace;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import ghidra.program.model.listing.FunctionManager;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.ReferenceManager;
import java.util.ArrayList;
import java.util.List;

public class FunctionsNearAddress extends GhidraScript {
    @Override
    public void run() throws Exception {
        String env = System.getenv("TRANSIT_TARGETS");
        if (env == null) { println("set TRANSIT_TARGETS"); return; }
        FunctionManager fm = currentProgram.getFunctionManager();
        ReferenceManager rm = currentProgram.getReferenceManager();
        AddressSpace sp = currentProgram.getAddressFactory().getDefaultAddressSpace();

        for (String tok : env.split(",")) {
            long va = Long.parseLong(tok.trim().replace("0x",""), 16);
            Address a = sp.getAddress(va);
            println(String.format("\n=== 0x%08x ===", va));
            Function at = fm.getFunctionAt(a);
            Function containing = fm.getFunctionContaining(a);
            println("  getFunctionAt: " + (at != null ? at.getName() + " @ 0x" + Long.toHexString(at.getEntryPoint().getOffset()) : "(none)"));
            println("  getFunctionContaining: " + (containing != null ? containing.getName() + " @ 0x" + Long.toHexString(containing.getEntryPoint().getOffset()) + " size=" + containing.getBody().getNumAddresses() : "(none)"));

            // Preceding + following functions
            List<Function> all = new ArrayList<>();
            FunctionIterator fi = fm.getFunctions(true);
            while (fi.hasNext()) all.add(fi.next());
            for (int i = 0; i < all.size(); i++) {
                if (all.get(i).getEntryPoint().getOffset() >= va) {
                    if (i > 0) {
                        Function before = all.get(i-1);
                        println(String.format("  previous fn: %s @ 0x%08x  size=%d",
                            before.getName(), before.getEntryPoint().getOffset(), before.getBody().getNumAddresses()));
                    }
                    for (int j = i; j < Math.min(i+3, all.size()); j++) {
                        Function n = all.get(j);
                        println(String.format("  following fn: %s @ 0x%08x  size=%d",
                            n.getName(), n.getEntryPoint().getOffset(), n.getBody().getNumAddresses()));
                    }
                    break;
                }
            }

            // All xrefs TO this address
            println("  xrefs to 0x" + Long.toHexString(va) + ":");
            ReferenceIterator rit = rm.getReferencesTo(a);
            int n = 0;
            while (rit.hasNext()) {
                Reference r = rit.next();
                Function src = fm.getFunctionContaining(r.getFromAddress());
                println(String.format("    from 0x%08x  %s  fn=%s",
                    r.getFromAddress().getOffset(), r.getReferenceType(),
                    src != null ? src.getName() : "(none)"));
                n++;
                if (n >= 30) { println("    ... (more)"); break; }
            }
        }
    }
}
