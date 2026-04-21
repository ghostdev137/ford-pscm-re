// Report all xrefs to given addresses with their reference types + source fn.
// @category Transit
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSpace;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.Listing;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceManager;

public class XrefsByType extends GhidraScript {
    @Override
    public void run() throws Exception {
        String env = System.getenv("XREF_TARGETS");
        if (env == null) env = "0xfef26382,0xfef263de,0xfef26384,0xfef26388,0xfef2638c";
        ReferenceManager rm = currentProgram.getReferenceManager();
        FunctionManager fm = currentProgram.getFunctionManager();
        Listing listing = currentProgram.getListing();
        AddressSpace sp = currentProgram.getAddressFactory().getDefaultAddressSpace();
        for (String t : env.split(",")) {
            long a = Long.decode(t.trim()) & 0xFFFFFFFFL;
            Address addr = sp.getAddress(a);
            println(String.format("\n=== 0x%08x ===", a));
            int n = 0;
            for (Reference r : rm.getReferencesTo(addr)) {
                Address src = r.getFromAddress();
                Function f = fm.getFunctionContaining(src);
                Instruction ins = listing.getInstructionAt(src);
                println(String.format("  from 0x%08x  %s  fn=%s @0x%08x  %s",
                    src.getOffset(), r.getReferenceType(),
                    f != null ? f.getName() : "<none>",
                    f != null ? f.getEntryPoint().getOffset() : 0L,
                    ins != null ? ins.toString() : ""));
                n++;
            }
            if (n == 0) println("  (no xrefs)");
        }
    }
}
