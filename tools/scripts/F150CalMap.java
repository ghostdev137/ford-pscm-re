// Find cal-offsets for known gain constants by identifying the ROM->RAM copy table.
// Strategy: fef264xx RAM values are mirrored from cal (0x101D0xxx). The offset is
// probably direct (fef2xxxx - base = cal offset relative to cal base).
// Also scan for APA RAM namespace across full fef20000..fef40000.
// @category Pipeline
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;

public class F150CalMap extends GhidraScript {
    @Override
    public void run() throws Exception {
        Path out = Paths.get("/tmp/pscm/f150_lka");
        AddressFactory af = currentProgram.getAddressFactory();
        AddressSpace asp = af.getDefaultAddressSpace();
        ReferenceManager rm = currentProgram.getReferenceManager();
        FunctionManager fm = currentProgram.getFunctionManager();
        StringBuilder r = new StringBuilder();

        // 1. For each known gain constant, list all reads.
        long[] calGains = {
            0xfef2642eL,  // LKA output gain (×ratelimited angle)
            0xfef2647cL,  // master curvature→torque (Q11)
            0xfef26405L, 0xfef26406L,  // rate limits
            0xfef26446L, 0xfef26448L,  // speed gates
            0xfef26452L, 0xfef26454L,  // ramp speed thresholds
            0xfef2645cL, 0xfef2645eL,  // ramp rate constants
            0xfef26484L, 0xfef26489L, 0xfef2648aL,  // enable+saturation
        };
        r.append("=== Cal constants (RAM mirrors at fef264xx) ===\n");
        for (long t : calGains) {
            Address a = asp.getAddress(t);
            ReferenceIterator refs = rm.getReferencesTo(a);
            int reads=0, writes=0;
            Set<String> readers = new LinkedHashSet<>();
            while (refs.hasNext()) {
                Reference ref = refs.next();
                Function f = fm.getFunctionContaining(ref.getFromAddress());
                if (f==null) continue;
                if (ref.getReferenceType().isRead()) { reads++; readers.add(f.getName()); }
                else if (ref.getReferenceType().isWrite()) writes++;
            }
            r.append(String.format("  fef%05x  reads=%d writes=%d  readers=%s\n",
                t & 0xFFFFFL, reads, writes, readers));
        }

        // 2. Find all pages in fef20000..fef40000 that have writers (APA hunt)
        r.append("\n=== All RAM pages with writers (0xfef20000..0xfef40000) ===\n");
        Map<Long, Integer> pageCount = new TreeMap<>();
        AddressIterator ait = rm.getReferenceSourceIterator(
            asp.getAddress(0x10040000L), true);
        while (ait.hasNext() && !monitor.isCancelled()) {
            Address src = ait.next();
            for (Reference ref : rm.getReferencesFrom(src)) {
                if (!ref.getReferenceType().isWrite()) continue;
                long to = ref.getToAddress().getOffset();
                if (to >= 0xfef20000L && to < 0xfef40000L) {
                    pageCount.merge(to & 0xFFFFF000L, 1, Integer::sum);
                }
            }
        }
        for (Map.Entry<Long,Integer> e : pageCount.entrySet()) {
            r.append(String.format("  page 0x%x: %d write-refs\n", e.getKey(), e.getValue()));
        }

        // 3. Look for APA-specific signatures: functions with both "park" range speeds (low: 0.5 kph, 8 kph cal)
        //    The cal values were: +0x0140 = 0.5 kph (APA min), +0x0144 = 8.0 kph (APA max)
        //    These would appear at fef20140/fef20144 in RAM.
        r.append("\n=== APA speed-gate reads (fef20140, fef20144) ===\n");
        for (long t : new long[]{0xfef20140L, 0xfef20144L, 0xfef20114L, 0xfef200c4L}) {
            Address a = asp.getAddress(t);
            ReferenceIterator refs = rm.getReferencesTo(a);
            Set<Function> readers = new LinkedHashSet<>();
            while (refs.hasNext()) {
                Reference ref = refs.next();
                if (ref.getReferenceType().isRead()) {
                    Function f = fm.getFunctionContaining(ref.getFromAddress());
                    if (f != null) readers.add(f);
                }
            }
            r.append(String.format("\nfef%05x: %d readers\n", t & 0xFFFFFL, readers.size()));
            int n=0; for (Function f : readers) {
                r.append(String.format("  %s @0x%x (%dB)\n", f.getName(),
                    f.getEntryPoint().getOffset(), f.getBody().getNumAddresses()));
                if (++n >= 10) break;
            }
        }

        Files.writeString(out.resolve("_calmap.txt"), r.toString());
        println("wrote _calmap.txt");
    }
}
