// Find functions that read/write the F-150 AS-BUILT backing-store RAM window.
// @category Probe
// @runtime Java

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressFactory;
import ghidra.program.model.address.AddressSpace;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.ReferenceManager;
import java.util.LinkedHashMap;
import java.util.Map;

public class F150AsBuiltRamRefs extends GhidraScript {
    @Override
    public void run() throws Exception {
        long start = 0xfebedda8L;
        long end = 0xfebee038L;

        AddressFactory af = currentProgram.getAddressFactory();
        AddressSpace asp = af.getDefaultAddressSpace();
        ReferenceManager rm = currentProgram.getReferenceManager();
        FunctionManager fm = currentProgram.getFunctionManager();

        Map<Function, Integer> writers = new LinkedHashMap<>();
        Map<Function, Integer> readers = new LinkedHashMap<>();

        for (long a = start; a <= end; a += 1) {
            Address addr = asp.getAddress(a);
            ReferenceIterator refs = rm.getReferencesTo(addr);
            while (refs.hasNext()) {
                Reference r = refs.next();
                Function f = fm.getFunctionContaining(r.getFromAddress());
                if (f == null) {
                    continue;
                }
                if (r.getReferenceType().isWrite()) {
                    writers.merge(f, 1, Integer::sum);
                }
                else if (r.getReferenceType().isRead()) {
                    readers.merge(f, 1, Integer::sum);
                }
            }
        }

        println(String.format("AS-BUILT RAM window: 0x%08x..0x%08x", start, end));

        println("\nTop writers:");
        writers.entrySet().stream()
            .sorted((a, b) -> Integer.compare(b.getValue(), a.getValue()))
            .limit(40)
            .forEach(e -> println(String.format("  %4d  %s @ 0x%08x size=%d",
                e.getValue(), e.getKey().getName(), e.getKey().getEntryPoint().getOffset(), e.getKey().getBody().getNumAddresses())));

        println("\nTop readers:");
        readers.entrySet().stream()
            .sorted((a, b) -> Integer.compare(b.getValue(), a.getValue()))
            .limit(40)
            .forEach(e -> println(String.format("  %4d  %s @ 0x%08x size=%d",
                e.getValue(), e.getKey().getName(), e.getKey().getEntryPoint().getOffset(), e.getKey().getBody().getNumAddresses())));
    }
}
