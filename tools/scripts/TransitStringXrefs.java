// List xrefs to interesting Transit block0 strings/data-table addresses and
// resolve the containing functions.
// @category Probe
// @runtime Java

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressFactory;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.ReferenceManager;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

public class TransitStringXrefs extends GhidraScript {
    private static final long[][] TARGETS = {
        {0x0100245cL, 0}, // NvM_SetRamBlockStatus string
        {0x010024b4L, 0}, // NvM_ReadBlock string
        {0x01002504L, 0}, // NvM_WriteBlock string
        {0x01002a60L, 0}, // nvmAcceptWriteBlockRequest string
        {0x01002abCL, 0}, // nvmAcceptSingleBlockRequest string
        {0x01002b50L, 0}, // PDU descriptor table
        {0x01002b78L, 0}, // 0x3CC PDU entry
        {0x01002c20L, 0}, // 0x0730 PDU entry
        {0x0100dbe0L, 0}, // DID table incl F10A
        {0x0100dbf4L, 0}, // DID table incl F188
    };

    @Override
    public void run() throws Exception {
        Path out = Paths.get("/tmp/pscm/transit_lca_map/string_xrefs.txt");
        Files.createDirectories(out.getParent());

        AddressFactory af = currentProgram.getAddressFactory();
        FunctionManager fm = currentProgram.getFunctionManager();
        ReferenceManager rm = currentProgram.getReferenceManager();
        StringBuilder sb = new StringBuilder();

        for (long[] entry : TARGETS) {
            long raw = entry[0];
            Address a = af.getDefaultAddressSpace().getAddress(raw);
            sb.append(String.format("TARGET 0x%08x\n", raw));
            ReferenceIterator it = rm.getReferencesTo(a);
            int count = 0;
            while (it.hasNext()) {
                Reference r = it.next();
                Function f = fm.getFunctionContaining(r.getFromAddress());
                sb.append(String.format("  from 0x%08x  type=%s  func=%s\n",
                    r.getFromAddress().getOffset(),
                    r.getReferenceType().getName(),
                    f != null ? f.getName() + "@0x" + Long.toHexString(f.getEntryPoint().getOffset()) : "?"));
                count++;
            }
            sb.append(String.format("  total_refs=%d\n\n", count));
        }

        Files.writeString(out, sb.toString());
        println(sb.toString());
    }
}
