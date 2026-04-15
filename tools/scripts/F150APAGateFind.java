// Find F150 APA speed gate — the float comparison that enforces max speed for APA.
// Look inside the APA task hierarchy for float reads that match 0.5f / 8.0f patterns.
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

public class F150APAGateFind extends GhidraScript {
    @Override
    public void run() throws Exception {
        Path out = Paths.get("/tmp/pscm/f150_apa");
        Listing L = currentProgram.getListing();
        AddressFactory af = currentProgram.getAddressFactory();
        FunctionManager fm = currentProgram.getFunctionManager();
        StringBuilder r = new StringBuilder();

        // Float constants for APA speed gates (F150 cal_findings)
        // 0.5 kph → float 0x3F000000 (APA min at cal+0x140)
        // 8.0 kph → float 0x41000000 (APA max at cal+0x144)
        // 10.0 kph → float 0x41200000 (LKA min at cal+0x114)
        int[] targets = {0x3F000000, 0x41000000, 0x41200000};
        String[] names = {"0.5f (APA min)", "8.0f (APA max)", "10.0f (LKA min)"};

        r.append("=== F150 APA/LKA speed-gate constant scan ===\n");
        for (int k = 0; k < targets.length; k++) {
            int val = targets[k];
            r.append(String.format("\nConstant 0x%08x = %s\n", val, names[k]));
            InstructionIterator it = L.getInstructions(true);
            int hits = 0;
            Set<Function> funcs = new LinkedHashSet<>();
            while (it.hasNext() && !monitor.isCancelled() && hits < 30) {
                Instruction ins = it.next();
                for (int op = 0; op < ins.getNumOperands(); op++) {
                    for (Object o : ins.getOpObjects(op)) {
                        if (o instanceof ghidra.program.model.scalar.Scalar) {
                            long v = ((ghidra.program.model.scalar.Scalar)o).getUnsignedValue();
                            if (v == (val & 0xFFFFFFFFL)) {
                                Function f = fm.getFunctionContaining(ins.getAddress());
                                if (f != null && !funcs.contains(f)) {
                                    funcs.add(f);
                                    r.append(String.format("  @0x%08x in %s (size=%d)\n",
                                        ins.getAddress().getOffset(), f.getName(),
                                        f.getBody().getNumAddresses()));
                                    hits++;
                                }
                            }
                        }
                    }
                }
            }
            if (funcs.isEmpty()) r.append("  (no hits)\n");
        }

        // Also look for `cmpf.s` / `bge`/`blt` patterns near APA functions — these are the comparisons
        r.append("\n=== Float compares inside APA handler region (0x10180000-0x101a0000) ===\n");
        InstructionIterator it = L.getInstructions(true);
        while (it.hasNext() && !monitor.isCancelled()) {
            Instruction ins = it.next();
            long a = ins.getAddress().getOffset();
            if (a < 0x10180000L || a > 0x101a0000L) continue;
            String m = ins.getMnemonicString().toLowerCase();
            if (m.contains("cmpf") || m.equals("cmpf.s") || m.equals("cmpf.d")) {
                Function f = fm.getFunctionContaining(ins.getAddress());
                r.append(String.format("  @0x%08x  %s  in %s\n",
                    a, ins.toString(), f != null ? f.getName() : "?"));
            }
        }

        Files.writeString(out.resolve("_speed_gate_code.txt"), r.toString());
        println("wrote _speed_gate_code.txt");
    }
}
