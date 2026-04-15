// Boundary cleanup: delete pure-padding pseudo-functions, trim real functions at last RET,
// clear overlapping / jump-table data, remove stale bad-insn bookmarks.
// @category Transit
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.symbol.FlowType;
import java.util.*;

public class CleanupBoundaries extends GhidraScript {
    @Override
    public void run() throws Exception {
        FunctionManager fm = currentProgram.getFunctionManager();
        Listing L = currentProgram.getListing();
        Memory mem = currentProgram.getMemory();
        BookmarkManager bm = currentProgram.getBookmarkManager();
        AddressSpace sp = currentProgram.getAddressFactory().getDefaultAddressSpace();

        // snapshot funcs
        List<Function> funcs = new ArrayList<>();
        for (Function f : fm.getFunctions(true)) funcs.add(f);
        funcs.sort((a,b) -> a.getEntryPoint().compareTo(b.getEntryPoint()));

        int passPad=0, passA=0, passB=0, passC=0, passD=0;

        // Pass PAD: delete funcs whose first 8 bytes are all 0xFF (padding-seeded pseudo-functions)
        for (Function f : funcs) {
            if (monitor.isCancelled()) break;
            try {
                Address a = f.getEntryPoint();
                boolean allFF = true;
                int check = Math.min(16, (int)f.getBody().getNumAddresses());
                for (int i=0;i<check;i++) {
                    int b = mem.getByte(a.add(i)) & 0xff;
                    if (b != 0xff) { allFF = false; break; }
                }
                if (allFF) {
                    Address maxA = f.getBody().getMaxAddress();
                    try { L.clearCodeUnits(a, maxA, false); } catch (Exception e) {}
                    fm.removeFunction(a);
                    // remove bad bookmarks in range
                    for (long i = a.getOffset(); i <= maxA.getOffset(); i++) {
                        try {
                            Address ba = sp.getAddress(i);
                            for (Bookmark b : bm.getBookmarks(ba)) {
                                if ("Error".equalsIgnoreCase(b.getTypeString())) bm.removeBookmark(b);
                            }
                        } catch (Exception e) {}
                    }
                    passPad++;
                }
            } catch (Exception e) {}
        }

        // rebuild sorted list
        funcs.clear();
        for (Function f : fm.getFunctions(true)) funcs.add(f);
        funcs.sort((a,b) -> a.getEntryPoint().compareTo(b.getEntryPoint()));

        // Pass A: trim trailing 0xFF after last return in body
        for (Function f : funcs) {
            if (monitor.isCancelled()) break;
            try {
                AddressSetView body = f.getBody();
                Address maxA = body.getMaxAddress();
                Address lastRet = null;
                for (AddressRange r : body) {
                    InstructionIterator it2 = L.getInstructions(new AddressSet(r.getMinAddress(), r.getMaxAddress()), true);
                    while (it2.hasNext()) {
                        Instruction ins = it2.next();
                        FlowType ft = ins.getFlowType();
                        String mn = ins.getMnemonicString().toLowerCase();
                        if (ft.isTerminal() || mn.equals("jmp") || mn.equals("dispose") || mn.equals("jr")) {
                            lastRet = ins.getMaxAddress();
                        }
                    }
                }
                if (lastRet != null && lastRet.compareTo(maxA) < 0) {
                    Address after = lastRet.add(1);
                    long nbytes = maxA.subtract(after) + 1;
                    if (nbytes > 0 && nbytes < 256) {
                        int ff=0;
                        for (long i=0;i<nbytes;i++){ int b=mem.getByte(after.add(i))&0xff; if (b==0xff) ff++; }
                        if (ff >= nbytes*0.6) {
                            try {
                                L.clearCodeUnits(after, maxA, false);
                                fm.getFunctionAt(f.getEntryPoint()).setBody(new AddressSet(f.getEntryPoint(), lastRet));
                                passA++;
                                for (long i=0;i<nbytes;i++){
                                    Address ba = after.add(i);
                                    for (Bookmark b : bm.getBookmarks(ba))
                                        if ("Error".equalsIgnoreCase(b.getTypeString())) bm.removeBookmark(b);
                                }
                            } catch (Exception e) {}
                        }
                    }
                }
            } catch (Exception e) {}
        }

        // Pass B: overlap into next function
        for (int i=0;i<funcs.size()-1;i++) {
            Function f = funcs.get(i);
            Function nxt = funcs.get(i+1);
            if (fm.getFunctionAt(f.getEntryPoint())==null) continue;
            if (fm.getFunctionAt(nxt.getEntryPoint())==null) continue;
            Address nxtStart = nxt.getEntryPoint();
            AddressSetView body = f.getBody();
            if (body.contains(nxtStart) && !body.getMinAddress().equals(nxtStart)) {
                Address newMax = nxtStart.subtract(1);
                if (newMax.compareTo(f.getEntryPoint()) >= 0) {
                    try {
                        fm.getFunctionAt(f.getEntryPoint()).setBody(new AddressSet(f.getEntryPoint(), newMax));
                        passB++;
                    } catch (Exception e) {}
                }
            }
        }

        // Pass D: remove bad bookmarks where no instruction exists anymore
        List<Bookmark> toRm = new ArrayList<>();
        Iterator<Bookmark> bit = bm.getBookmarksIterator();
        while (bit.hasNext()) {
            Bookmark b = bit.next();
            if (!"Error".equalsIgnoreCase(b.getTypeString())) continue;
            Address ba = b.getAddress();
            if (L.getInstructionAt(ba) == null) toRm.add(b);
        }
        for (Bookmark b : toRm) { bm.removeBookmark(b); passD++; }

        println("CLEANUP passPAD=" + passPad + " passA(trim_pad)=" + passA + " passB(overlap)=" + passB + " passD(stale_bm)=" + passD);
        println("Total funcs now: " + fm.getFunctionCount());
    }
}
