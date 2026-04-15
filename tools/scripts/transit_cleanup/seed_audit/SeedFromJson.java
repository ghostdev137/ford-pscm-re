// Seeds functions from /tmp/pscm/entries.json at pointer-table addresses.
// @category Transit
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import java.io.*;
import java.util.*;

public class SeedFromJson extends GhidraScript {
    @Override
    public void run() throws Exception {
        String path = System.getenv().getOrDefault("SEED_JSON", "/tmp/pscm/entries.json");
        BufferedReader br = new BufferedReader(new FileReader(path));
        StringBuilder sb = new StringBuilder();
        String line;
        while ((line = br.readLine()) != null) sb.append(line);
        br.close();
        String s = sb.toString().trim();
        if (s.startsWith("[")) s = s.substring(1);
        if (s.endsWith("]")) s = s.substring(0, s.length()-1);
        String[] parts = s.split(",");
        AddressFactory af = currentProgram.getAddressFactory();
        FunctionManager fm = currentProgram.getFunctionManager();

        int created = 0, skipped = 0, failed = 0;
        for (String p : parts) {
            p = p.trim();
            if (p.isEmpty()) continue;
            long off;
            try { off = Long.parseLong(p); } catch (Exception e) { continue; }
            if (off < 0x01000000L || off > 0x010FFFF0L) { skipped++; continue; }
            if ((off & 1L) != 0) off &= ~1L;
            Address a = af.getDefaultAddressSpace().getAddress(off);
            if (fm.getFunctionAt(a) != null) { skipped++; continue; }
            try {
                // disassemble at address first
                disassemble(a);
                Function f = createFunction(a, null);
                if (f != null) created++; else failed++;
            } catch (Exception e) { failed++; }
        }
        println("Seed: created=" + created + " skipped=" + skipped + " failed=" + failed);
        println("Total funcs now: " + fm.getFunctionCount());
    }
}
