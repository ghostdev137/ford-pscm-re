// Measures function quality: halt_baddata, bad-insn bookmarks, sizes.
// Writes TSV to $MEASURE_OUT (default /tmp/transit_cleanup/measure.tsv)
// @category Transit
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.mem.Memory;
import java.io.*;
import java.util.*;

public class MeasureQuality extends GhidraScript {
    @Override
    public void run() throws Exception {
        String outp = System.getenv().getOrDefault("MEASURE_OUT", "/tmp/transit_cleanup/measure.tsv");
        PrintWriter pw = new PrintWriter(new FileWriter(outp));
        pw.println("addr\tsize\thas_halt_baddata\thas_bad_bm\ttrailing_byte");
        FunctionManager fm = currentProgram.getFunctionManager();
        Memory mem = currentProgram.getMemory();
        BookmarkManager bm = currentProgram.getBookmarkManager();

        // collect bad bookmark addresses
        Set<Long> badBmAddrs = new HashSet<>();
        Iterator<Bookmark> bit = bm.getBookmarksIterator();
        while (bit.hasNext()) {
            Bookmark b = bit.next();
            String t = b.getTypeString();
            String c = b.getCategory();
            if ("Error".equalsIgnoreCase(t) || (c != null && (c.toLowerCase().contains("bad") || c.toLowerCase().contains("disass")))) {
                badBmAddrs.add(b.getAddress().getOffset());
            }
        }

        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);

        int total=0, haltCount=0, badBmCount=0;
        List<Long> sizes = new ArrayList<>();

        FunctionIterator fit = fm.getFunctions(true);
        int i=0;
        while (fit.hasNext()) {
            if (monitor.isCancelled()) break;
            Function f = fit.next();
            total++;
            long start = f.getEntryPoint().getOffset();
            AddressSetView body = f.getBody();
            long size = body.getNumAddresses();
            sizes.add(size);

            boolean hasBadBm = false;
            for (AddressRange r : body) {
                for (long a = r.getMinAddress().getOffset(); a <= r.getMaxAddress().getOffset(); a++) {
                    if (badBmAddrs.contains(a)) { hasBadBm = true; break; }
                }
                if (hasBadBm) break;
            }
            if (hasBadBm) badBmCount++;

            boolean hasHalt = false;
            if (i < 100000) {  // limit decompile
                try {
                    DecompileResults dr = di.decompileFunction(f, 15, monitor);
                    if (dr != null && dr.decompileCompleted()) {
                        String c = dr.getDecompiledFunction().getC();
                        if (c != null && c.contains("halt_baddata")) { hasHalt = true; haltCount++; }
                    }
                } catch (Exception e) {}
            }

            String tb = "";
            try {
                Address maxA = body.getMaxAddress();
                Address next = maxA.add(1);
                byte b0 = mem.getByte(next);
                tb = String.format("%02X", b0 & 0xff);
            } catch (Exception e) {}

            pw.println(String.format("%08x\t%d\t%s\t%s\t%s", start, size, hasHalt, hasBadBm, tb));
            i++;
        }
        pw.close();
        di.dispose();
        Collections.sort(sizes);
        long med = sizes.isEmpty()?0:sizes.get(sizes.size()/2);
        println("MEASURE total=" + total + " halt_baddata=" + haltCount + " bad_bm=" + badBmCount + " median_size=" + med);
        // also write summary
        PrintWriter sp = new PrintWriter(new FileWriter(outp + ".summary"));
        sp.println("total=" + total);
        sp.println("halt_baddata=" + haltCount);
        sp.println("bad_bm=" + badBmCount);
        sp.println("median_size=" + med);
        sp.close();
    }
}
