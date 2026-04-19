// Report surviving suspicious no-ref functions after cleanup.
// @category Transit
// @runtime Java

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressRange;
import ghidra.program.model.listing.Bookmark;
import ghidra.program.model.listing.BookmarkManager;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.listing.Listing;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.symbol.FlowType;
import ghidra.program.model.symbol.Reference;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

public class TransitBogusFunctionReport extends GhidraScript {
    private static final long[][] KNOWN_DATA_RANGES = {
        { 0x01000000L, 0x010053FFL },
        { 0x01008400L, 0x010093FFL },
        { 0x0100BB20L, 0x0100D21FL }
    };
    private static final int QUALITY_PREFIX_WINDOW = 16;
    private static final int HALT_FLOW_WINDOW = 64;

    private static class Entry {
        final long address;
        final long size;
        final int score;

        Entry(long address, long size, int score) {
            this.address = address;
            this.size = size;
            this.score = score;
        }
    }

    @Override
    public void run() throws Exception {
        FunctionManager fm = currentProgram.getFunctionManager();
        Listing listing = currentProgram.getListing();
        Memory memory = currentProgram.getMemory();
        BookmarkManager bm = currentProgram.getBookmarkManager();

        List<Entry> suspicious = new ArrayList<>();
        int noRefCount = 0;
        for (Function fn : fm.getFunctions(true)) {
            if (monitor.isCancelled()) {
                break;
            }
            if (hasInboundTrustedReferenceFromOtherFunction(fn.getEntryPoint(), fn, fm, listing, memory, bm)) {
                continue;
            }
            noRefCount++;
            int score = suspicionScore(fn, listing, memory, bm);
            if (score >= 2) {
                suspicious.add(new Entry(
                    fn.getEntryPoint().getOffset(),
                    fn.getBody().getNumAddresses(),
                    score
                ));
            }
        }

        suspicious.sort(Comparator
            .comparingInt((Entry e) -> e.score).reversed()
            .thenComparingLong(e -> e.address));

        StringBuilder out = new StringBuilder();
        out.append("no_ref_count=").append(noRefCount).append("\n");
        out.append("suspicious_count=").append(suspicious.size()).append("\n");
        int limit = Math.min(32, suspicious.size());
        for (int i = 0; i < limit; i++) {
            Entry entry = suspicious.get(i);
            out.append(String.format("0x%08x\t%d\t%d%n", entry.address, entry.size, entry.score));
        }

        String outPath = System.getenv("TRANSIT_BOGUS_REPORT_OUT");
        if (outPath != null && !outPath.isBlank()) {
            Files.writeString(Path.of(outPath), out.toString());
        }
        print(out.toString());
    }

    private boolean hasInboundTrustedReferenceFromOtherFunction(
            Address entry,
            Function self,
            FunctionManager fm,
            Listing listing,
            Memory memory,
            BookmarkManager bm) {
        for (Reference ref : getReferencesTo(entry)) {
            if (ref == null) continue;
            Address from = ref.getFromAddress();
            if (from == null || from.equals(entry) || !isExecutable(from)) continue;
            Function caller = fm.getFunctionContaining(from);
            if (caller != null &&
                    !caller.getEntryPoint().equals(self.getEntryPoint()) &&
                    isTrustedCaller(caller, listing, memory, bm)) {
                return true;
            }
        }
        return false;
    }

    private boolean isTrustedCaller(
            Function caller,
            Listing listing,
            Memory memory,
            BookmarkManager bm) {
        return suspicionScore(caller, listing, memory, bm) < 2;
    }

    private int suspicionScore(Function fn, Listing listing, Memory memory, BookmarkManager bm) {
        int score = 0;
        if (isKnownDataSeedRegion(fn.getEntryPoint())) score++;
        if (hasBadBookmarksInBody(fn, bm)) score++;
        if (hasUnknownPrefix(fn, listing)) score++;
        if (startsWithPadding(fn, memory)) score++;
        if (hasImpossibleDirectFlowWindow(fn, listing, HALT_FLOW_WINDOW)) score++;
        return score;
    }

    private boolean isKnownDataSeedRegion(Address addr) {
        long off = addr.getOffset();
        for (long[] range : KNOWN_DATA_RANGES) {
            if (off >= range[0] && off <= range[1]) return true;
        }
        return false;
    }

    private boolean hasBadBookmarksInBody(Function fn, BookmarkManager bm) {
        for (AddressRange range : fn.getBody()) {
            for (long off = range.getMinAddress().getOffset(); off <= range.getMaxAddress().getOffset(); off++) {
                try {
                    Address addr = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(off);
                    for (Bookmark bookmark : bm.getBookmarks(addr)) {
                        if ("Error".equalsIgnoreCase(bookmark.getTypeString())) {
                            return true;
                        }
                    }
                } catch (Exception e) {
                    break;
                }
            }
        }
        return false;
    }

    private boolean hasUnknownPrefix(Function fn, Listing listing) {
        InstructionIterator it = listing.getInstructions(fn.getBody(), true);
        int seen = 0;
        while (it.hasNext() && seen < QUALITY_PREFIX_WINDOW) {
            Instruction ins = it.next();
            seen++;
            String mnem = ins.getMnemonicString();
            if (mnem == null) return true;
            String lower = mnem.toLowerCase();
            if (lower.startsWith("unk_") || lower.startsWith("??")) {
                return true;
            }
        }
        return false;
    }

    private boolean startsWithPadding(Function fn, Memory memory) {
        try {
            Address entry = fn.getEntryPoint();
            int check = Math.min(16, (int) fn.getBody().getNumAddresses());
            int ff = 0;
            for (int i = 0; i < check; i++) {
                int b = memory.getByte(entry.add(i)) & 0xff;
                if (b == 0xff || b == 0x00) {
                    ff++;
                }
            }
            return check > 0 && ff >= check * 3 / 4;
        } catch (Exception e) {
            return false;
        }
    }

    private boolean hasImpossibleDirectFlowWindow(Function fn, Listing listing, int window) {
        InstructionIterator it = listing.getInstructions(fn.getBody(), true);
        int seen = 0;
        while (it.hasNext() && seen < window) {
            Instruction ins = it.next();
            seen++;
            FlowType ft = ins.getFlowType();
            if (!(ft.isJump() || ft.isCall() || ft.isTerminal())) {
                continue;
            }
            Address[] flows = ins.getFlows();
            if (flows == null || flows.length == 0) {
                continue;
            }
            for (Address target : flows) {
                if (target == null) {
                    continue;
                }
                if (!isExecutable(target) || isKnownDataSeedRegion(target)) {
                    return true;
                }
            }
        }
        return false;
    }

    private boolean isExecutable(Address address) {
        MemoryBlock block = currentProgram.getMemory().getBlock(address);
        return block != null && block.isExecute();
    }
}
