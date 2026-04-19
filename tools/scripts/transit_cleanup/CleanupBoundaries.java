// Boundary cleanup: delete pure-padding pseudo-functions, trim real functions at last RET,
// clear overlapping / jump-table data, remove stale bad-insn bookmarks.
// @category Transit
// @runtime Java
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.symbol.FlowType;
import ghidra.program.model.symbol.Reference;
import java.util.*;

public class CleanupBoundaries extends GhidraScript {
    private static final long[][] KNOWN_DATA_RANGES = {
        { 0x01000000L, 0x010053FFL },
        { 0x01008400L, 0x010093FFL },
        { 0x0100BB20L, 0x0100D21FL }
    };
    private static final int ASCII_PREFIX_WINDOW = 64;
    private static final int EARLY_FLOW_WINDOW = 8;
    private static final int HALT_FLOW_WINDOW = 64;
    private static final int STRUCTURED_WORD_WINDOW = 32;
    private static final int QUALITY_PREFIX_WINDOW = 16;
    private static final Set<String> RARE_MNEMONICS = new HashSet<>(Arrays.asList(
        "divh", "divhu", "mulh", "sld.h", "sld.b", "sld.w",
        "sst.h", "sst.b", "sst.w", "mac", "macu", "dbtrap"));

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

        int passPad=0, passA=0, passB=0, passC=0, passD=0, passRange=0, passSuspect=0, passHalt=0;
        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);

        // Pass RANGE: delete seeded pseudo-functions that land inside known descriptor tables.
        try {
        for (Function f : funcs) {
            if (monitor.isCancelled()) break;
            try {
                Address a = f.getEntryPoint();
                if (!isKnownDataSeedRegion(a)) continue;
                Address maxA = f.getBody().getMaxAddress();
                try { L.clearCodeUnits(a, maxA, false); } catch (Exception e) {}
                fm.removeFunction(a);
                for (long i = a.getOffset(); i <= maxA.getOffset(); i++) {
                    try {
                        Address ba = sp.getAddress(i);
                        for (Bookmark b : bm.getBookmarks(ba)) {
                            if ("Error".equalsIgnoreCase(b.getTypeString())) bm.removeBookmark(b);
                        }
                    } catch (Exception e) {}
                }
                passRange++;
            } catch (Exception e) {}
        }

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

        // Pass E: iteratively remove orphaned seeded functions that still look like
        // strings/data or branch to nowhere. This is mainly for cross-variant seeds.
        boolean changed;
        do {
            changed = false;
            funcs.clear();
            for (Function f : fm.getFunctions(true)) funcs.add(f);
            funcs.sort((a,b) -> a.getEntryPoint().compareTo(b.getEntryPoint()));

            for (Function f : funcs) {
                if (monitor.isCancelled()) break;
                if (!isSuspectOrphanFunction(f, fm, L, mem, bm)) continue;
                if (removeFunctionRange(f, fm, L, bm, sp)) {
                    passSuspect++;
                    changed = true;
                }
            }
        } while (changed && !monitor.isCancelled());

        // Pass F: final orphan sweep for functions that still decompile into
        // halt_baddata and have no inbound executable refs.
        funcs.clear();
        for (Function f : fm.getFunctions(true)) funcs.add(f);
        funcs.sort((a,b) -> a.getEntryPoint().compareTo(b.getEntryPoint()));
        for (Function f : funcs) {
            if (monitor.isCancelled()) break;
            if (hasInboundTrustedReferenceFromOtherFunction(f.getEntryPoint(), f, fm, L, mem)) continue;
            if (!hasHaltBaddataDecompile(f, decompiler)) continue;
            if (removeFunctionRange(f, fm, L, bm, sp)) {
                passHalt++;
            }
        }
        } finally {
            decompiler.dispose();
        }

        println("CLEANUP passRange(data_seed)=" + passRange + " passPAD=" + passPad + " passA(trim_pad)=" + passA + " passB(overlap)=" + passB + " passD(stale_bm)=" + passD + " passE(suspect_orphan)=" + passSuspect + " passF(halt_orphan)=" + passHalt);
        println("Total funcs now: " + fm.getFunctionCount());
    }

    private boolean isKnownDataSeedRegion(Address addr) {
        long off = addr.getOffset();
        for (long[] range : KNOWN_DATA_RANGES) {
            if (off >= range[0] && off <= range[1]) {
                return true;
            }
        }
        return false;
    }

    private boolean isSuspectOrphanFunction(Function f, FunctionManager fm, Listing listing, Memory mem,
            BookmarkManager bm) {
        Address entry = f.getEntryPoint();
        if (hasInboundTrustedReferenceFromOtherFunction(entry, f, fm, listing, mem)) {
            return false;
        }
        return isIntrinsicallySuspicious(f, listing, mem) && hasBodyQualityFailure(f, listing, bm);
    }

    private boolean hasInboundExecutableReferenceFromOtherFunction(Address entry, Function self,
            FunctionManager fm) {
        for (Reference ref : getReferencesTo(entry)) {
            if (ref == null) continue;
            Address from = ref.getFromAddress();
            if (from == null || from.equals(entry)) continue;
            if (!isExecutableAddress(from)) continue;
            Function caller = fm.getFunctionContaining(from);
            if (caller == null) continue;
            if (!caller.getEntryPoint().equals(self.getEntryPoint())) {
                return true;
            }
        }
        return false;
    }

    private boolean hasInboundTrustedReferenceFromOtherFunction(Address entry, Function self,
            FunctionManager fm, Listing listing, Memory mem) {
        for (Reference ref : getReferencesTo(entry)) {
            if (ref == null) continue;
            Address from = ref.getFromAddress();
            if (from == null || from.equals(entry)) continue;
            if (!isExecutableAddress(from)) continue;
            Function caller = fm.getFunctionContaining(from);
            if (caller == null) continue;
            if (!caller.getEntryPoint().equals(self.getEntryPoint()) &&
                    isTrustedCaller(caller, listing, mem)) {
                return true;
            }
        }
        return false;
    }

    private boolean isTrustedCaller(Function caller, Listing listing, Memory mem) {
        if (isIntrinsicallySuspicious(caller, listing, mem)) {
            return false;
        }
        return !hasBodyQualityFailure(caller, listing, currentProgram.getBookmarkManager());
    }

    private boolean isIntrinsicallySuspicious(Function f, Listing listing, Memory mem) {
        Address entry = f.getEntryPoint();
        return isKnownDataSeedRegion(entry) ||
            startsAfterTerminalSplit(entry, listing) ||
            startsWithNopPadding(f, listing) ||
            hasSuspiciousAsciiPrefix(f, mem) ||
            hasStructuredWordPrefix(f, mem) ||
            hasImpossibleDirectFlowWindow(f, listing, EARLY_FLOW_WINDOW);
    }

    private boolean hasBodyQualityFailure(Function f, Listing listing, BookmarkManager bm) {
        int signals = 0;
        if (hasBadBookmarksInBody(f, bm)) signals++;
        if (hasUnknownOrUndefinedPrefix(f, listing)) signals++;
        if (hasRareOpcodePrefix(f, listing)) signals++;
        return signals >= 2;
    }

    private boolean hasBadBookmarksInBody(Function f, BookmarkManager bm) {
        for (AddressRange r : f.getBody()) {
            for (long off = r.getMinAddress().getOffset(); off <= r.getMaxAddress().getOffset(); off++) {
                try {
                    Address addr = currentAddress.getAddressSpace().getAddress(off);
                    for (Bookmark bookmark : bm.getBookmarks(addr)) {
                        String type = bookmark.getTypeString();
                        String category = bookmark.getCategory();
                        if ("Error".equalsIgnoreCase(type)) {
                            return true;
                        }
                        if (category != null) {
                            String lc = category.toLowerCase();
                            if (lc.contains("bad") || lc.contains("disass")) {
                                return true;
                            }
                        }
                    }
                } catch (Exception e) {
                    break;
                }
            }
        }
        return false;
    }

    private boolean hasUnknownOrUndefinedPrefix(Function f, Listing listing) {
        InstructionIterator it = listing.getInstructions(f.getBody(), true);
        int seen = 0;
        while (it.hasNext() && seen < QUALITY_PREFIX_WINDOW) {
            Instruction ins = it.next();
            seen++;
            String mnem = ins.getMnemonicString();
            if (mnem == null) {
                return true;
            }
            String lower = mnem.toLowerCase();
            if (lower.startsWith("unk_") || lower.startsWith("??")) {
                return true;
            }
        }

        Address entry = f.getEntryPoint();
        Address cursor = entry;
        long max = Math.min(f.getBody().getNumAddresses(), 16);
        for (int i = 0; i < max; i++) {
            CodeUnit cu = listing.getCodeUnitContaining(cursor);
            if (cu == null) {
                return true;
            }
            if (listing.getInstructionAt(cursor) == null && listing.getDefinedDataAt(cursor) == null) {
                return true;
            }
            try {
                cursor = cursor.add(1);
            } catch (Exception e) {
                break;
            }
        }
        return false;
    }

    private boolean hasRareOpcodePrefix(Function f, Listing listing) {
        InstructionIterator it = listing.getInstructions(f.getBody(), true);
        int seen = 0;
        int rare = 0;
        while (it.hasNext() && seen < QUALITY_PREFIX_WINDOW) {
            Instruction ins = it.next();
            seen++;
            String lower = ins.getMnemonicString().toLowerCase();
            if (RARE_MNEMONICS.contains(lower)) {
                rare++;
            }
        }
        return seen >= 4 && rare >= 3;
    }

    private boolean startsWithNopPadding(Function f, Listing listing) {
        InstructionIterator it = listing.getInstructions(f.getBody(), true);
        int seen = 0;
        int nops = 0;
        int consecutive = 0;
        int maxConsecutive = 0;
        while (it.hasNext() && seen < QUALITY_PREFIX_WINDOW) {
            Instruction ins = it.next();
            seen++;
            if ("nop".equalsIgnoreCase(ins.getMnemonicString())) {
                nops++;
                consecutive++;
                maxConsecutive = Math.max(maxConsecutive, consecutive);
            } else {
                consecutive = 0;
            }
        }
        return maxConsecutive >= 4 || (seen >= 8 && nops * 2 >= seen);
    }

    private boolean hasHaltBaddataDecompile(Function f, DecompInterface decompiler) {
        try {
            DecompileResults results = decompiler.decompileFunction(f, 10, monitor);
            if (results == null || !results.decompileCompleted() || results.getDecompiledFunction() == null) {
                return false;
            }
            String c = results.getDecompiledFunction().getC();
            return c != null && c.contains("halt_baddata");
        } catch (Exception e) {
            return false;
        }
    }

    private boolean hasSuspiciousAsciiPrefix(Function f, Memory mem) {
        Address entry = f.getEntryPoint();
        int window = Math.min(ASCII_PREFIX_WINDOW, (int) Math.max(1, f.getBody().getNumAddresses()));
        int printable = 0;
        int zero = 0;
        int maxRun = 0;
        int run = 0;
        for (int i = 0; i < window; i++) {
            try {
                int b = mem.getByte(entry.add(i)) & 0xff;
                boolean isPrintable = b >= 0x20 && b <= 0x7e;
                if (isPrintable) {
                    printable++;
                    run++;
                    if (run > maxRun) maxRun = run;
                } else {
                    run = 0;
                }
                if (b == 0) zero++;
            } catch (Exception e) {
                break;
            }
        }
        return maxRun >= 8 || (window >= 16 && printable * 100 >= window * 55 && zero * 4 <= window);
    }

    private boolean hasImpossibleDirectFlowWindow(Function f, Listing listing, int window) {
        InstructionIterator it = listing.getInstructions(f.getBody(), true);
        int seen = 0;
        while (it.hasNext() && seen < window) {
            Instruction ins = it.next();
            seen++;
            FlowType ft = ins.getFlowType();
            if (!(ft.isJump() || ft.isCall() || ft.isTerminal())) continue;
            Address[] flows = ins.getFlows();
            if (flows == null || flows.length == 0) continue;
            for (Address target : flows) {
                if (target == null) continue;
                if (!isExecutableAddress(target)) {
                    return true;
                }
                if (isKnownDataSeedRegion(target)) {
                    return true;
                }
            }
        }
        return false;
    }

    private boolean startsAfterTerminalSplit(Address entry, Listing listing) {
        Instruction prev = listing.getInstructionBefore(entry);
        if (prev == null) return false;
        try {
            if (!prev.getMaxAddress().add(1).equals(entry)) {
                return false;
            }
        } catch (Exception e) {
            return false;
        }
        FlowType ft = prev.getFlowType();
        String mn = prev.getMnemonicString().toLowerCase();
        return ft.isTerminal() || mn.equals("dispose") || mn.equals("jr") || mn.equals("jmp") ||
            mn.equals("eiret") || mn.equals("feret") || mn.equals("ctret") || mn.equals("dbret");
    }

    private boolean hasStructuredWordPrefix(Function f, Memory mem) {
        Address entry = f.getEntryPoint();
        int window = Math.min(STRUCTURED_WORD_WINDOW, (int) Math.max(4, f.getBody().getNumAddresses()));
        int structuredWords = 0;
        Map<Integer, Integer> wordFreq = new HashMap<>();
        for (int i = 0; i + 3 < window; i += 4) {
            try {
                int b0 = mem.getByte(entry.add(i)) & 0xff;
                int b1 = mem.getByte(entry.add(i + 1)) & 0xff;
                int b2 = mem.getByte(entry.add(i + 2)) & 0xff;
                int b3 = mem.getByte(entry.add(i + 3)) & 0xff;
                int word = (b0 << 24) | (b1 << 16) | (b2 << 8) | b3;
                wordFreq.put(word, wordFreq.getOrDefault(word, 0) + 1);
                if ((b0 == 0 && b1 == 0) || (b2 == 0 && b3 == 0)) {
                    structuredWords++;
                }
            } catch (Exception e) {
                break;
            }
        }
        if (structuredWords >= 4) {
            return true;
        }
        for (Integer count : wordFreq.values()) {
            if (count.intValue() >= 3) {
                return true;
            }
        }
        return false;
    }

    private boolean isExecutableAddress(Address addr) {
        try {
            return currentProgram.getMemory().getBlock(addr) != null &&
                currentProgram.getMemory().getBlock(addr).isExecute();
        } catch (Exception e) {
            return false;
        }
    }

    private boolean removeFunctionRange(Function f, FunctionManager fm, Listing listing,
            BookmarkManager bm, AddressSpace sp) {
        try {
            Address a = f.getEntryPoint();
            Address maxA = f.getBody().getMaxAddress();
            try { listing.clearCodeUnits(a, maxA, false); } catch (Exception e) {}
            fm.removeFunction(a);
            for (long i = a.getOffset(); i <= maxA.getOffset(); i++) {
                try {
                    Address ba = sp.getAddress(i);
                    for (Bookmark b : bm.getBookmarks(ba)) {
                        if ("Error".equalsIgnoreCase(b.getTypeString())) bm.removeBookmark(b);
                    }
                } catch (Exception e) {}
            }
            return true;
        } catch (Exception e) {
            return false;
        }
    }
}
