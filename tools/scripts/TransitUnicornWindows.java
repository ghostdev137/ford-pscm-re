// Dump narrow instruction windows for the exact Transit Unicorn trace targets.
// @category Probe
// @runtime Java

import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSet;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

public class TransitUnicornWindows extends GhidraScript {
    private static final long[] TARGETS = {
        0x0108f484L,
        0x0108f494L,
        0x0108d914L,
        0x0108d924L,
        0x010bc360L,
    };

    @Override
    public void run() throws Exception {
        Path outDir = Paths.get(System.getProperty(
            "transit.unicorn.out",
            "/tmp/pscm/transit_unicorn_windows"));
        Files.createDirectories(outDir);

        for (long target : TARGETS) {
            Address start = toAddr(target - 0x20);
            Address end = toAddr(target + 0x80);
            new DisassembleCommand(new AddressSet(start, end), null, true)
                .applyTo(currentProgram, monitor);

            StringBuilder sb = new StringBuilder();
            sb.append(String.format("target=0x%08x\n\n", target));

            InstructionIterator it = currentProgram.getListing().getInstructions(start, true);
            while (it.hasNext()) {
                Instruction ins = it.next();
                if (ins.getAddress().compareTo(end) > 0) {
                    break;
                }
                sb.append(String.format("0x%08x  %s\n", ins.getAddress().getOffset(), ins.toString()));
            }

            Files.writeString(outDir.resolve(String.format("%08x.txt", target)), sb.toString());
            println("wrote 0x" + Long.toHexString(target));
        }
    }
}
