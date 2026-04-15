// Find the APA "reject if speed > max" early return in F150.
// Scan APA main handler for early-exit patterns: cmpf.s followed by conditional branch that skips most of the function.
// @category Pipeline
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import java.io.*;
import java.nio.file.*;

public class F150APAReject extends GhidraScript {
    @Override
    public void run() throws Exception {
        Path out = Paths.get("/tmp/pscm/f150_apa");
        AddressFactory af = currentProgram.getAddressFactory();
        Listing L = currentProgram.getListing();
        FunctionManager fm = currentProgram.getFunctionManager();
        StringBuilder sb = new StringBuilder();

        // Scan APA handler + task + helpers for cmpf.s + conditional branch forward to end of function
        long[] funcs = {0x1017fd92L, 0x10183a8aL, 0x1018466eL, 0x101848acL};
        for (long fAddr : funcs) {
            Address a = af.getDefaultAddressSpace().getAddress(fAddr);
            Function f = fm.getFunctionAt(a);
            if (f == null) continue;
            long lo = f.getEntryPoint().getOffset();
            long hi = f.getBody().getMaxAddress().getOffset();
            sb.append(String.format("\n=== %s @0x%x (size=%d) ===\n", f.getName(), lo, hi-lo));

            // Find cmpf.s / cmpf.d / cmp instructions followed by conditional branch
            InstructionIterator it = L.getInstructions(f.getBody(), true);
            Instruction prev = null;
            while (it.hasNext()) {
                Instruction ins = it.next();
                String m = ins.getMnemonicString().toLowerCase();
                // look at branches that follow a compare
                if (prev != null) {
                    String pm = prev.getMnemonicString().toLowerCase();
                    if ((pm.startsWith("cmpf") || pm.equals("cmp")) &&
                        (m.startsWith("b") && !m.equals("bsh") && !m.equals("bsw"))) {
                        // if branch target is near end of func, it's an early-exit
                        Address[] flows = ins.getFlows();
                        long target = (flows != null && flows.length > 0) ? flows[0].getOffset() : 0;
                        long dist = target - ins.getAddress().getOffset();
                        if (dist > 50 && target < hi) {  // forward branch
                            sb.append(String.format("  0x%08x  %s -> 0x%08x (fwd %d bytes)\n",
                                prev.getAddress().getOffset(), prev.toString(),
                                target, dist));
                            sb.append(String.format("  0x%08x  %s  (branch)\n\n",
                                ins.getAddress().getOffset(), ins.toString()));
                        }
                    }
                }
                prev = ins;
            }
        }

        Files.writeString(out.resolve("_early_exit_scan.txt"), sb.toString());
        println("wrote _early_exit_scan.txt");
    }
}
