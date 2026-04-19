// Explain why a function is or is not considered trusted by cleanup heuristics.
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
import ghidra.program.model.symbol.Reference;

public class TraceFunctionTrust extends GhidraScript {
    private static final long[][] KNOWN_DATA_RANGES = {
        { 0x01000000L, 0x010053FFL },
        { 0x01008400L, 0x010093FFL },
        { 0x0100BB20L, 0x0100D21FL }
    };
    private static final int QUALITY_PREFIX_WINDOW = 16;

    @Override
    public void run() throws Exception {
        if (getScriptArgs().length == 0) {
            println("usage: TraceFunctionTrust <addr> [addr...]");
            return;
        }

        FunctionManager fm = currentProgram.getFunctionManager();
        Listing listing = currentProgram.getListing();
        Memory memory = currentProgram.getMemory();
        BookmarkManager bm = currentProgram.getBookmarkManager();

        for (String raw : getScriptArgs()) {
            Address addr = toAddr(Long.decode(raw));
            Function fn = fm.getFunctionContaining(addr);
            println("");
            println("============================================================");
            println("target=" + addr);
            if (fn == null) {
                println("no containing function");
                continue;
            }

            println(String.format("function=%s entry=%s size=%d intrinsic=%s bodyFail=%s trustedCaller=%s",
                fn.getName(),
                fn.getEntryPoint(),
                fn.getBody().getNumAddresses(),
                isIntrinsicallySuspicious(fn, listing, memory),
                hasBodyQualityFailure(fn, listing, bm),
                hasInboundTrustedReferenceFromOtherFunction(fn.getEntryPoint(), fn, fm, listing, memory, bm)));

            for (Reference ref : getReferencesTo(fn.getEntryPoint())) {
                Address from = ref.getFromAddress();
                if (from == null || from.equals(fn.getEntryPoint()) || !isExecutable(from)) {
                    continue;
                }
                Function caller = fm.getFunctionContaining(from);
                println(String.format(
                    "  ref from=%s caller=%s callerEntry=%s intrinsic=%s bodyFail=%s trusted=%s",
                    from,
                    caller == null ? "<none>" : caller.getName(),
                    caller == null ? "<none>" : caller.getEntryPoint().toString(),
                    caller == null ? "?" : Boolean.toString(isIntrinsicallySuspicious(caller, listing, memory)),
                    caller == null ? "?" : Boolean.toString(hasBodyQualityFailure(caller, listing, bm)),
                    caller != null && !caller.getEntryPoint().equals(fn.getEntryPoint()) &&
                        !isIntrinsicallySuspicious(caller, listing, memory) &&
                        !hasBodyQualityFailure(caller, listing, bm)
                ));
            }
        }
    }

    private boolean hasInboundTrustedReferenceFromOtherFunction(
            Address entry,
            Function self,
            FunctionManager fm,
            Listing listing,
            Memory memory,
            BookmarkManager bm) {
        for (Reference ref : getReferencesTo(entry)) {
            Address from = ref.getFromAddress();
            if (from == null || from.equals(entry) || !isExecutable(from)) {
                continue;
            }
            Function caller = fm.getFunctionContaining(from);
            if (caller != null &&
                    !caller.getEntryPoint().equals(self.getEntryPoint()) &&
                    !isIntrinsicallySuspicious(caller, listing, memory) &&
                    !hasBodyQualityFailure(caller, listing, bm)) {
                return true;
            }
        }
        return false;
    }

    private boolean isIntrinsicallySuspicious(Function f, Listing listing, Memory memory) {
        return isKnownDataSeedRegion(f.getEntryPoint()) ||
            startsWithPadding(f, memory) ||
            hasUnknownPrefix(f, listing);
    }

    private boolean hasBodyQualityFailure(Function f, Listing listing, BookmarkManager bm) {
        return hasBadBookmarksInBody(f, bm) || hasUnknownPrefix(f, listing);
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

    private boolean hasBadBookmarksInBody(Function fn, BookmarkManager bm) {
        for (AddressRange range : fn.getBody()) {
            for (long off = range.getMinAddress().getOffset(); off <= range.getMaxAddress().getOffset(); off++) {
                Address addr = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(off);
                for (Bookmark bookmark : bm.getBookmarks(addr)) {
                    if ("Error".equalsIgnoreCase(bookmark.getTypeString())) {
                        return true;
                    }
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

    private boolean isExecutable(Address address) {
        MemoryBlock block = currentProgram.getMemory().getBlock(address);
        return block != null && block.isExecute();
    }
}
