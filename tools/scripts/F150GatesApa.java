// Find LKA enable gates + APA RAM namespace.
// @category Pipeline
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;

public class F150GatesApa extends GhidraScript {
    @Override
    public void run() throws Exception {
        Path out = Paths.get("/tmp/pscm/f150_lka");
        Files.createDirectories(out);
        AddressFactory af = currentProgram.getAddressFactory();
        AddressSpace asp = af.getDefaultAddressSpace();
        ReferenceManager rm = currentProgram.getReferenceManager();
        FunctionManager fm = currentProgram.getFunctionManager();
        StringBuilder r = new StringBuilder();

        // 1. Writers of _DAT_fef21057 (LKA enable bool from rate-limiter)
        //    and fef210af, fef21a98 (enable/gate bools seen in 101a4f2a)
        r.append("=== Enable-flag writers ===\n");
        long[] flags = {0xfef21057L, 0xfef210afL, 0xfef21a98L, 0xfef2105cL, 0xfef21a65L};
        for (long t : flags) {
            Address a = asp.getAddress(t);
            r.append(String.format("\nfef%05x (gate): readers + writers\n", t & 0xFFFFFL));
            ReferenceIterator refs = rm.getReferencesTo(a);
            Set<Function> writers=new LinkedHashSet<>(), readers=new LinkedHashSet<>();
            while (refs.hasNext()) {
                Reference ref = refs.next();
                Function f = fm.getFunctionContaining(ref.getFromAddress());
                if (f==null) continue;
                if (ref.getReferenceType().isWrite()) writers.add(f);
                else if (ref.getReferenceType().isRead()) readers.add(f);
            }
            for (Function f : writers) r.append(String.format("  W %s @0x%x (%dB)\n",
                f.getName(), f.getEntryPoint().getOffset(), f.getBody().getNumAddresses()));
            for (Function f : readers) r.append(String.format("  R %s @0x%x (%dB)\n",
                f.getName(), f.getEntryPoint().getOffset(), f.getBody().getNumAddresses()));
        }

        // 2. Enumerate unique fef2xxxx RAM namespaces by 256-byte-page writes per function
        r.append("\n=== RAM namespaces by 4KB page (fef2xxxx writes) ===\n");
        Map<Long, Set<Function>> pageToWriters = new TreeMap<>();
        AddressIterator ait = rm.getReferenceSourceIterator(
            asp.getAddress(0x10040000L), true);
        while (ait.hasNext() && !monitor.isCancelled()) {
            Address src = ait.next();
            Reference[] refs = rm.getReferencesFrom(src);
            for (Reference ref : refs) {
                if (!ref.getReferenceType().isWrite()) continue;
                long to = ref.getToAddress().getOffset();
                if (to < 0xfef20000L || to >= 0xfef30000L) continue;
                long page = to & 0xFFFFF000L;
                Function f = fm.getFunctionContaining(src);
                if (f == null) continue;
                pageToWriters.computeIfAbsent(page, k->new LinkedHashSet<>()).add(f);
            }
        }
        for (Map.Entry<Long,Set<Function>> e : pageToWriters.entrySet()) {
            r.append(String.format("\npage 0x%x: %d writer funcs\n", e.getKey(), e.getValue().size()));
            int n=0; for (Function f : e.getValue()) {
                r.append(String.format("  %s @0x%x (%dB)\n", f.getName(),
                    f.getEntryPoint().getOffset(), f.getBody().getNumAddresses()));
                if (++n >= 8) { r.append("  ...\n"); break; }
            }
        }

        Files.writeString(out.resolve("_gates_apa.txt"), r.toString());
        println("wrote _gates_apa.txt (" + r.length() + " bytes)");
    }
}
