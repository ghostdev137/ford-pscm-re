// Dump raw instruction/data windows around interesting literal addresses.
// @category Probe
// @runtime Java

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSet;
import ghidra.program.model.listing.Data;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.ReferenceManager;

public class TransitLiteralPeek extends GhidraScript {
    private static final long[] TARGETS = {
        0x01043155L,
        0x0108c4c9L,
        0x0108c5edL,
        0x0105cfd9L,
        0x0105ec04L,
        0x0105ec38L,
        0x01074b5eL,
        0x01074fbcL,
        0x01081ed5L,
        0x01090410L,
        0x0109fc36L,
        0x0109b730L,
        0x010a1403L,
        0x010a1433L,
        0x010abedeL,
    };

    @Override
    public void run() throws Exception {
        Path outDir = Paths.get("/tmp/pscm/transit_literal_peek");
        Files.createDirectories(outDir);
        ReferenceManager rm = currentProgram.getReferenceManager();

        for (long off : TARGETS) {
            Address a = toAddr(off);
            StringBuilder sb = new StringBuilder();
            sb.append(String.format("target=0x%08x\n\n", off));

            Data d = getDataAt(a);
            if (d != null) {
                sb.append("data_at_target: ").append(d.toString()).append("\n\n");
            }

            sb.append("refs_to_target:\n");
            ReferenceIterator rit = rm.getReferencesTo(a);
            int rc = 0;
            while (rit.hasNext()) {
                Reference ref = rit.next();
                sb.append(String.format("  0x%08x -> 0x%08x  %s\n",
                    ref.getFromAddress().getOffset(), off, ref.getReferenceType()));
                rc++;
            }
            if (rc == 0) {
                sb.append("  (none)\n");
            }
            sb.append("\n");

            try {
                new DisassembleCommand(new AddressSet(a.subtract(0x20), a.add(0x40)), null, true)
                    .applyTo(currentProgram, monitor);
            } catch (Exception ignored) {
            }

            sb.append("instruction_window:\n");
            InstructionIterator it = currentProgram.getListing().getInstructions(a.subtract(0x20), true);
            while (it.hasNext()) {
                Instruction ins = it.next();
                if (ins.getAddress().compareTo(a.add(0x40)) > 0) {
                    break;
                }
                sb.append(String.format("  0x%08x  %s\n", ins.getAddress().getOffset(), ins.toString()));
            }
            sb.append("\nbytes:\n");
            for (long cur = off - 0x10; cur < off + 0x20; cur += 0x10) {
                Address line = toAddr(cur);
                byte[] buf = new byte[0x10];
                currentProgram.getMemory().getBytes(line, buf);
                sb.append(String.format("  0x%08x  ", cur));
                for (byte b : buf) {
                    sb.append(String.format("%02x", b & 0xff));
                }
                sb.append("\n");
            }

            Files.writeString(outDir.resolve(String.format("%08x.txt", off)), sb.toString());
        }

        println("wrote literal peeks to " + outDir);
    }
}
