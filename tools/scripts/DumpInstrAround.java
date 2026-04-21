// Dump instruction listing for a given address range.
// @category Transit
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSpace;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.Listing;
import java.nio.file.Files;
import java.nio.file.Paths;

public class DumpInstrAround extends GhidraScript {
    @Override
    public void run() throws Exception {
        long[] addrs = { 0x010a76d6L, 0x010d0ef6L, 0x010b2cd8L, 0x010923e2L, 0x010b428eL, 0x01010000L };
        AddressSpace sp = currentProgram.getAddressFactory().getDefaultAddressSpace();
        Listing listing = currentProgram.getListing();
        StringBuilder sb = new StringBuilder();

        for (long base : addrs) {
            sb.append(String.format("\n=== 0x%08x ===\n", base));
            Address a = sp.getAddress(base);
            for (int i = 0; i < 40; i++) {
                Instruction ins = listing.getInstructionAt(a);
                if (ins == null) {
                    sb.append(String.format("  0x%08x  <no instruction>\n", a.getOffset()));
                    a = a.add(2);
                    continue;
                }
                byte[] b = ins.getBytes();
                StringBuilder bs = new StringBuilder();
                for (byte by : b) bs.append(String.format("%02x ", by & 0xff));
                sb.append(String.format("  0x%08x  %-24s  %s\n", a.getOffset(), bs.toString(), ins.toString()));
                a = ins.getMaxAddress().add(1);
                if (a == null) break;
            }
        }
        Files.writeString(Paths.get("/tmp/pscm/transit_mdx/instr_dump.txt"), sb.toString());
        println("Wrote /tmp/pscm/transit_mdx/instr_dump.txt");
    }
}
