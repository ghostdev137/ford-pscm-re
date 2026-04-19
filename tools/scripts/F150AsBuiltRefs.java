// Find F-150 AS-BUILT DID table references and nearby descriptor xrefs.
// @category Probe
// @runtime Java

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.ReferenceManager;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.RefType;
import ghidra.program.model.symbol.Symbol;
import ghidra.program.model.symbol.SymbolTable;

public class F150AsBuiltRefs extends GhidraScript {
    private void dumpRefs(String label, long addrValue) {
        Address addr = toAddr(addrValue);
        println("\n== " + label + " @ " + addr + " ==");
        ReferenceManager rm = currentProgram.getReferenceManager();

        SymbolTable st = currentProgram.getSymbolTable();
        Symbol sym = st.getPrimarySymbol(addr);
        if (sym != null) {
            println("symbol: " + sym.getName());
        }

        ReferenceIterator it = rm.getReferencesTo(addr);
        int count = 0;
        while (it.hasNext()) {
            Reference ref = it.next();
            count++;
            Address from = ref.getFromAddress();
            Function f = getFunctionContaining(from);
            String fname = f != null ? f.getName() : "<no function>";
            RefType type = ref.getReferenceType();
            println(String.format("  from %s  %-18s  %s", from, fname, type));
        }
        println("refs: " + count);
    }

    @Override
    public void run() throws Exception {
        long[] targets = new long[] {
            0x10044BCA, // 0x3003
            0x10044BCC, // 0x301A
            0x10044BCE, // 0x301F
            0x10044BD0, // 0x3020
            0x10044BF2, // 0xDE00
            0x10044BF4, // 0xDE01
            0x10044BF6, // 0xDE02
            0x10044BF8, // 0xDE03
            0x10044BFA, // 0xDE04
            0x10044BFC, // 0xDE05
            0x1004BBF8, // start of descriptor-ish blob near DExx
            0x1004BC08,
            0x1004BC5C,
            0x1004BBA8,
            0x1004BBAC,
            0x1004BC70,
        };

        String[] labels = new String[] {
            "DID_3003",
            "DID_301A",
            "DID_301F",
            "DID_3020",
            "DID_DE00",
            "DID_DE01",
            "DID_DE02",
            "DID_DE03",
            "DID_DE04",
            "DID_DE05",
            "DESC_BASE",
            "DESC_PTR_1",
            "DESC_PTR_2",
            "DESC_PTR_3",
            "DESC_PTR_4",
            "MASK_TABLE",
        };

        for (int i = 0; i < targets.length; i++) {
            dumpRefs(labels[i], targets[i]);
        }
    }
}
