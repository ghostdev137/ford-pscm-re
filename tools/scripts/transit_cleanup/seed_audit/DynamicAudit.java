// Phase 5 dynamic seed audit. Runs over current Ghidra project (which already
// has all phase-4 seeded functions). For every function, decides keep/reject
// based on heuristics 4-5.
//
// Writes TSV to $AUDIT_OUT (default /tmp/ghidra_phase5/dynamic_audit.tsv)
// with columns: addr, decision, reason, halt_baddata, insn_count, first_mnems
//
// @category Transit
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.mem.Memory;
import java.io.*;
import java.util.*;

public class DynamicAudit extends GhidraScript {
    @Override
    public void run() throws Exception {
        String outp = System.getenv().getOrDefault("AUDIT_OUT", "/tmp/ghidra_phase5/dynamic_audit.tsv");
        PrintWriter pw = new PrintWriter(new FileWriter(outp));
        pw.println("addr\tdecision\treason\thalt_baddata\tinsn_count\tfirst_mnems");

        FunctionManager fm = currentProgram.getFunctionManager();
        Listing listing = currentProgram.getListing();
        BookmarkManager bm = currentProgram.getBookmarkManager();

        // collect bad-bookmark addrs
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
        println("bad bookmark addrs: " + badBmAddrs.size());

        // rare opcodes that frequently appear when data is mis-decoded as v850e3
        Set<String> rare = new HashSet<>(Arrays.asList(
            "divh","mulh","sld.h","sld.b","sld.w","sst.h","sst.b","sst.w",
            "divhu","mac","macu","dbtrap"));

        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);

        int total=0, kept=0, rej_halt=0, rej_tiny=0, rej_badbm=0, rej_rare=0;

        FunctionIterator fit = fm.getFunctions(true);
        while (fit.hasNext()) {
            if (monitor.isCancelled()) break;
            Function f = fit.next();
            total++;
            Address ep = f.getEntryPoint();
            long start = ep.getOffset();

            // collect first up to 8 instructions from function body
            List<Instruction> first = new ArrayList<>();
            InstructionIterator iit = listing.getInstructions(f.getBody(), true);
            while (iit.hasNext() && first.size() < 8) first.add(iit.next());

            StringBuilder mn = new StringBuilder();
            int rareCount = 0;
            for (Instruction i : first) {
                String m = i.getMnemonicString().toLowerCase();
                if (mn.length()>0) mn.append(',');
                mn.append(m);
                if (rare.contains(m)) rareCount++;
            }

            // bad bookmark inside body?
            boolean hasBadBm = false;
            for (AddressRange r : f.getBody()) {
                long min=r.getMinAddress().getOffset(), max=r.getMaxAddress().getOffset();
                for (long a=min; a<=max; a++) if (badBmAddrs.contains(a)) { hasBadBm=true; break; }
                if (hasBadBm) break;
            }

            boolean hasHalt = false;
            try {
                DecompileResults dr = di.decompileFunction(f, 15, monitor);
                if (dr != null && dr.decompileCompleted()) {
                    String c = dr.getDecompiledFunction().getC();
                    if (c != null && c.contains("halt_baddata")) hasHalt = true;
                }
            } catch (Exception e) {}

            String decision = "KEEP";
            String reason = "ok";

            if (hasHalt) {
                decision="REJECT"; reason="halt_baddata"; rej_halt++;
            } else if (hasBadBm) {
                decision="REJECT"; reason="bad_bm"; rej_badbm++;
            } else if (first.size() <= 2) {
                decision="REJECT"; reason="too_short"; rej_tiny++;
            } else if (first.size() >= 4 && rareCount >= 3) {
                decision="REJECT"; reason="rare_opcodes"; rej_rare++;
            } else {
                kept++;
            }

            pw.println(String.format("%08x\t%s\t%s\t%s\t%d\t%s",
                    start, decision, reason, hasHalt, first.size(), mn.toString()));

            if ((total & 0xff) == 0) println("audit progress: " + total);
        }
        pw.close();
        di.dispose();
        println("AUDIT total="+total+" kept="+kept+" rej_halt="+rej_halt+
                " rej_badbm="+rej_badbm+" rej_tiny="+rej_tiny+" rej_rare="+rej_rare);
    }
}
