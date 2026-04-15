// Analyze F150 APA speed-gate code paths to assess safety of patching speed limits.
// @category Pipeline
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;

public class F150APASpeedCheck extends GhidraScript {
    @Override
    public void run() throws Exception {
        Path out = Paths.get("/tmp/pscm/f150_apa");
        AddressFactory af = currentProgram.getAddressFactory();
        AddressSpace asp = af.getDefaultAddressSpace();
        ReferenceManager rm = currentProgram.getReferenceManager();
        FunctionManager fm = currentProgram.getFunctionManager();
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        StringBuilder r = new StringBuilder();

        // Known F150 APA speed gates from earlier cal_findings
        long[] apaGates = {
            0xfef20140L,  // APA min speed 0.5 kph (float32 LE)
            0xfef20144L,  // APA max speed 8.0 kph
            0xfef20114L,  // LKA min speed 10.0 m/s
            0xfef200c4L,  // LDW gate 10.0
        };

        for (long t : apaGates) {
            Address a = asp.getAddress(t);
            r.append(String.format("\n=== fef%05x ===\n", t & 0xFFFFFL));
            ReferenceIterator refs = rm.getReferencesTo(a);
            Set<Function> readers = new LinkedHashSet<>();
            while (refs.hasNext()) {
                Reference ref = refs.next();
                if (ref.getReferenceType().isRead()) {
                    Function f = fm.getFunctionContaining(ref.getFromAddress());
                    if (f != null) readers.add(f);
                }
            }
            if (readers.isEmpty()) {
                r.append("  NO direct readers (may be read via FP register or indirect)\n");
                continue;
            }
            for (Function f : readers) {
                r.append(String.format("  READ by %s @0x%x (%dB)\n",
                    f.getName(), f.getEntryPoint().getOffset(), f.getBody().getNumAddresses()));
                // Decompile to see actual usage
                DecompileResults res = di.decompileFunction(f, 60, monitor);
                if (res != null && res.getDecompiledFunction() != null) {
                    String code = res.getDecompiledFunction().getC();
                    // Find the lines that reference this address
                    String hex = String.format("%x", t & 0xFFFFFL);
                    String[] lines = code.split("\n");
                    for (int i = 0; i < lines.length; i++) {
                        if (lines[i].toLowerCase().contains("fef"+hex)
                            || lines[i].toLowerCase().contains("_0"+hex.substring(hex.length()-4))) {
                            int from = Math.max(0, i-2);
                            int to = Math.min(lines.length, i+4);
                            r.append("    context:\n");
                            for (int k = from; k < to; k++)
                                r.append("      " + lines[k] + "\n");
                            r.append("    ---\n");
                            break;
                        }
                    }
                }
            }
        }

        Files.writeString(out.resolve("_speed_gates.txt"), r.toString());
        println("wrote _speed_gates.txt");
    }
}
