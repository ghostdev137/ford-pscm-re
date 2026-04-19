// Repair verified offcut instruction sites gathered from the seeded-analysis log.
// @category Transit
// @runtime Java

import ghidra.app.script.GhidraScript;
import ghidra.app.script.ScriptMessage;
import ghidra.app.util.PseudoDisassembler;
import ghidra.app.util.PseudoInstruction;
import ghidra.program.disassemble.Disassembler;
import ghidra.program.model.address.Address;
import ghidra.program.model.lang.InsufficientBytesException;
import ghidra.program.model.lang.UnknownContextException;
import ghidra.program.model.lang.UnknownInstructionException;
import ghidra.program.model.listing.Bookmark;
import ghidra.program.model.listing.BookmarkManager;
import ghidra.program.model.listing.BookmarkType;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.Listing;
import ghidra.program.model.symbol.RefType;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceManager;
import ghidra.util.Msg;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class TransitTargetedOffcutRepair extends GhidraScript {
    private static final Pattern OFFCUT_PATTERN = Pattern.compile(
        "Invalid delay slot or offcut instruction found at\\s+([0-9A-Fa-f]+)"
    );
    private static final String INFO_BOOKMARK_CATEGORY = "Transit Offcut";
    private static final String INFO_BOOKMARK_COMMENT = "Transit targeted offcut fix";

    private Listing listing;
    private BookmarkManager bookmarkManager;
    private ReferenceManager referenceManager;
    private int alignment;

    @Override
    public void run() throws Exception {
        listing = currentProgram.getListing();
        bookmarkManager = currentProgram.getBookmarkManager();
        referenceManager = currentProgram.getReferenceManager();
        alignment = currentProgram.getLanguage().getInstructionAlignment();

        String rawPath = System.getenv("TRANSIT_ANALYSIS_LOG");
        if (rawPath == null || rawPath.isBlank()) {
            println("TransitTargetedOffcutRepair: no TRANSIT_ANALYSIS_LOG");
            return;
        }

        Path logPath = Path.of(rawPath);
        if (!Files.isRegularFile(logPath)) {
            println("TransitTargetedOffcutRepair: missing log " + logPath);
            return;
        }

        LinkedHashSet<Long> targets = parseTargets(Files.readString(logPath));
        int fixed = 0;
        int skippedNoInstr = 0;
        int skippedNotOffcut = 0;
        int skippedValidation = 0;
        int skippedNoJumpRef = 0;

        for (long value : targets) {
            if (monitor.isCancelled()) {
                break;
            }

            Address offcutAddress = toAddr(value);
            Instruction base = listing.getInstructionContaining(offcutAddress);
            if (base == null) {
                skippedNoInstr++;
                continue;
            }
            if (base.getMinAddress().equals(offcutAddress)) {
                skippedNotOffcut++;
                continue;
            }
            if ((offcutAddress.getOffset() % alignment) != 0) {
                skippedValidation++;
                continue;
            }
            if (!hasJumpReference(offcutAddress)) {
                skippedNoJumpRef++;
                continue;
            }
            if (base.isLengthOverridden()) {
                skippedValidation++;
                continue;
            }
            if (!canDisassembleAt(base, offcutAddress)) {
                skippedValidation++;
                continue;
            }

            try {
                base.setLengthOverride((int) offcutAddress.subtract(base.getMinAddress()));
                disassemble(offcutAddress);
                fixBookmark(offcutAddress);
                fixed++;
            } catch (Exception e) {
                Msg.error(this, new ScriptMessage("Failed targeted offcut repair at " + offcutAddress), e);
                skippedValidation++;
            }
        }

        println(
            "TransitTargetedOffcutRepair: targets=" + targets.size() +
            " fixed=" + fixed +
            " skipped_no_instr=" + skippedNoInstr +
            " skipped_not_offcut=" + skippedNotOffcut +
            " skipped_no_jump_ref=" + skippedNoJumpRef +
            " skipped_validation=" + skippedValidation
        );
    }

    private LinkedHashSet<Long> parseTargets(String text) {
        LinkedHashSet<Long> values = new LinkedHashSet<>();
        Matcher matcher = OFFCUT_PATTERN.matcher(text);
        while (matcher.find()) {
            values.add(Long.parseUnsignedLong(matcher.group(1), 16));
        }
        return values;
    }

    private boolean hasJumpReference(Address address) {
        List<Reference> refs = new ArrayList<>();
        for (Reference ref : getReferencesTo(address)) {
            refs.add(ref);
        }
        for (Reference ref : refs) {
            RefType type = ref.getReferenceType();
            if (type != null && type.isJump()) {
                return true;
            }
        }
        return false;
    }

    private void fixBookmark(Address at) {
        Bookmark bookmark = bookmarkManager.getBookmark(
            at,
            BookmarkType.ERROR,
            Disassembler.ERROR_BOOKMARK_CATEGORY
        );
        if (bookmark != null) {
            bookmarkManager.removeBookmark(bookmark);
        }
        bookmarkManager.setBookmark(at, BookmarkType.INFO, INFO_BOOKMARK_CATEGORY, INFO_BOOKMARK_COMMENT);
    }

    private boolean canDisassembleAt(Instruction base, Address address) {
        try {
            PseudoDisassembler pdis = new PseudoDisassembler(currentProgram);
            PseudoInstruction testInstr = pdis.disassemble(address);
            return testInstr != null && testInstr.getMaxAddress().equals(base.getMaxAddress());
        } catch (InsufficientBytesException | UnknownInstructionException | UnknownContextException e) {
            Msg.warn(this, "Could not validate offcut at " + address + ": " + e.getMessage());
            return false;
        }
    }
}
