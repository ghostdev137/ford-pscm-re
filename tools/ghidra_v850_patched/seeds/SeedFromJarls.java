import ghidra.app.script.GhidraScript;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.app.cmd.function.CreateFunctionCmd;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSet;
import java.io.BufferedReader;
import java.io.FileReader;

/* Pre-script: seeds known-call-targets as function starts before auto-analysis.
 * Reads a file of hex addresses (one per line), disassembles each, then
 * creates a function. Ghidra's cascade does the rest. */
public class SeedFromJarls extends GhidraScript {
    @Override
    public void run() throws Exception {
        String path = "/tmp/transit_decode_stats/jarl_targets_valid.txt";
        BufferedReader br = new BufferedReader(new FileReader(path));
        String line;
        int seeded = 0;
        int failed = 0;
        while ((line = br.readLine()) != null) {
            line = line.trim();
            if (line.isEmpty()) continue;
            try {
                long n = Long.parseLong(line, 16);
                Address a = toAddr(n);
                if (currentProgram.getMemory().getBlock(a) == null) continue;
                // Disassemble first
                DisassembleCommand dc = new DisassembleCommand(a, null, true);
                dc.applyTo(currentProgram, monitor);
                // Then create function
                CreateFunctionCmd cfc = new CreateFunctionCmd(a);
                if (cfc.applyTo(currentProgram, monitor)) seeded++;
                else failed++;
            } catch (Exception e) {
                failed++;
            }
        }
        br.close();
        println("SeedFromJarls: seeded=" + seeded + " failed=" + failed);
    }
}
