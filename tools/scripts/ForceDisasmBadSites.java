// Attempt to clear + re-disassemble every bad-instruction bookmark site.
// Reports how many succeed, and for each failure, logs the bytes + why.
// Target: the 1747+ sites with hw0=0x02E0..0x02FF (JR/JARL disp32 family)
// which SHOULD decode with the current SLEIGH.
// @category Transit
// @runtime Java
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Bookmark;
import ghidra.program.model.listing.BookmarkManager;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.Listing;
import ghidra.program.model.mem.Memory;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

public class ForceDisasmBadSites extends GhidraScript {
    @Override
    public void run() throws Exception {
        String outDir = "/tmp/pscm/bad_transit";
        Files.createDirectories(Paths.get(outDir));

        Listing listing = currentProgram.getListing();
        Memory mem = currentProgram.getMemory();
        BookmarkManager bm = currentProgram.getBookmarkManager();

        List<Address> siteAddrs = new ArrayList<>();
        Iterator<Bookmark> it = bm.getBookmarksIterator();
        while (it.hasNext() && !monitor.isCancelled()) {
            Bookmark b = it.next();
            if (!"Error".equals(b.getType().getTypeString())) continue;
            siteAddrs.add(b.getAddress());
        }
        println("Found " + siteAddrs.size() + " error-bookmark sites");

        int tried = 0, success = 0, stillBad = 0, jarlClass = 0;
        StringBuilder log = new StringBuilder();

        for (Address a : siteAddrs) {
            if (monitor.isCancelled()) break;
            tried++;
            int b0, b1, b2, b3, hw0;
            try {
                b0 = mem.getByte(a) & 0xFF;
                b1 = mem.getByte(a.add(1)) & 0xFF;
                b2 = mem.getByte(a.add(2)) & 0xFF;
                b3 = mem.getByte(a.add(3)) & 0xFF;
                hw0 = b0 | (b1 << 8);
            } catch (Exception ex) { continue; }
            // Filter: only hw0=0x02E0..0x02FF (JR/JARL disp32 family)
            if (hw0 < 0x02E0 || hw0 > 0x02FF) continue;
            jarlClass++;

            // Clear any existing code/data at this address
            try { clearListing(a, a.add(5)); }
            catch (Exception e) { /* ignore */ }

            // Try disassemble
            DisassembleCommand dc = new DisassembleCommand(a, null, true);
            boolean ok = dc.applyTo(currentProgram, monitor);
            Instruction ins = listing.getInstructionAt(a);
            if (ok && ins != null && !ins.getMnemonicString().toLowerCase().contains("bad")) {
                success++;
                if (success <= 10) {
                    log.append(String.format("SUCCESS @0x%08x  hw0=%04x  %s\n",
                        a.getOffset(), hw0, ins.toString()));
                }
            } else {
                stillBad++;
                if (stillBad <= 20) {
                    log.append(String.format("FAIL @0x%08x  hw0=%04x  bytes=%02x %02x %02x %02x%s\n",
                        a.getOffset(), hw0, b0, b1, b2, b3,
                        ins != null ? "  got=" + ins.toString() : "  no-instruction"));
                }
            }
        }
        log.insert(0, String.format("JR/JARL-class sites tried: %d; success=%d; stillBad=%d\n",
            jarlClass, success, stillBad));
        Files.writeString(Paths.get(outDir, "force_disasm_result.txt"), log.toString());
        println(log.toString().split("\n")[0]);
    }
}
