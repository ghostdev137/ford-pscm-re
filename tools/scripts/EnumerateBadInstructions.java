// Enumerate all locations where the V850 SLEIGH failed to decode.
// For each bad-instruction site, grab the 4-byte raw pattern and group
// by op0510 / op2126 fields so we can see which opcode groups still need
// SLEIGH stubs.
// @category Transit
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.BookmarkManager;
import ghidra.program.model.listing.Bookmark;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.listing.Listing;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.mem.MemoryAccessException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Iterator;
import java.util.Map;
import java.util.TreeMap;

public class EnumerateBadInstructions extends GhidraScript {
    @Override
    public void run() throws Exception {
        String outDir = System.getenv().getOrDefault("BAD_INSTR_OUT", "/tmp/pscm/bad_instr");
        Files.createDirectories(Paths.get(outDir));

        Listing listing = currentProgram.getListing();
        Memory mem = currentProgram.getMemory();
        BookmarkManager bm = currentProgram.getBookmarkManager();

        StringBuilder siteLog = new StringBuilder();
        Map<String, Integer> byOp = new TreeMap<>();
        Map<String, Integer> byByteHW0 = new TreeMap<>();
        int totalSites = 0;

        // Method A: walk bookmarks of type "Error" (Ghidra marks bad decode here)
        Iterator<Bookmark> it = bm.getBookmarksIterator();
        while (it.hasNext() && !monitor.isCancelled()) {
            Bookmark b = it.next();
            String typ = b.getType().getTypeString();
            String cat = b.getCategory();
            if (!"Error".equals(typ) && !"BAD_INSTRUCTION".equals(cat)
                && !cat.toLowerCase().contains("bad")) continue;
            Address a = b.getAddress();
            try {
                int b0 = mem.getByte(a) & 0xFF;
                int b1 = mem.getByte(a.add(1)) & 0xFF;
                int b2 = mem.getByte(a.add(2)) & 0xFF;
                int b3 = mem.getByte(a.add(3)) & 0xFF;
                int hw0 = b0 | (b1 << 8);
                int hw1 = b2 | (b3 << 8);
                int op0510 = (hw0 >> 5) & 0x3f;
                int op2126 = (hw1 >> 5) & 0x3f;
                String keyA = String.format("op0510=0x%02x", op0510);
                String keyB = String.format("op0510=0x%02x/op2126=0x%02x", op0510, op2126);
                byOp.merge(keyB, 1, Integer::sum);
                byByteHW0.merge(String.format("%04x", hw0), 1, Integer::sum);
                totalSites++;
                if (totalSites <= 200) {
                    siteLog.append(String.format("  0x%08x  bytes=%02x %02x %02x %02x  hw0=%04x  hw1=%04x  op0510=0x%02x  op2126=0x%02x  (bm=%s/%s)\n",
                        a.getOffset(), b0, b1, b2, b3, hw0, hw1, op0510, op2126, typ, cat));
                }
            } catch (MemoryAccessException ex) {
                /* skip */
            }
        }

        // Method B: walk every instruction and check if it's `halt_baddata()`-like
        // by looking at the "bad" mnemonic or unusual length.
        int halts = 0;
        InstructionIterator iit = listing.getInstructions(true);
        while (iit.hasNext()) {
            if (monitor.isCancelled()) break;
            Instruction ins = iit.next();
            String mn = ins.getMnemonicString().toLowerCase();
            if (mn.contains("baddata") || mn.equals("??") || mn.equals("halt")) {
                halts++;
            }
        }

        StringBuilder summary = new StringBuilder();
        summary.append(String.format("Total error-bookmark sites: %d\n", totalSites));
        summary.append(String.format("Halt/bad mnemonics seen: %d\n", halts));
        summary.append("\n=== Sites grouped by op0510/op2126 ===\n");
        byOp.entrySet().stream()
            .sorted((a, b) -> Integer.compare(b.getValue(), a.getValue()))
            .limit(60)
            .forEach(e -> summary.append(String.format("  %-30s  %d\n", e.getKey(), e.getValue())));

        summary.append("\n=== Top hw0 (first 16-bit word) patterns ===\n");
        byByteHW0.entrySet().stream()
            .sorted((a, b) -> Integer.compare(b.getValue(), a.getValue()))
            .limit(30)
            .forEach(e -> summary.append(String.format("  hw0=%s  %d\n", e.getKey(), e.getValue())));

        Files.writeString(Paths.get(outDir, "summary.txt"), summary.toString());
        Files.writeString(Paths.get(outDir, "sites.txt"), siteLog.toString());
        println(summary.toString());
    }
}
