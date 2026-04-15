// Count headless Ghidra decompile outcomes for the F-150 full ELF.
// @category Probe
// @runtime Java

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;

public class F150LiftReport extends GhidraScript {
    @Override
    public void run() throws Exception {
        FunctionManager fm = currentProgram.getFunctionManager();
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);

        int total = 0;
        int completed = 0;
        int clean = 0;
        int warnings = 0;
        int baddata = 0;
        int failed = 0;

        for (Function f : fm.getFunctions(true)) {
            total++;
            DecompileResults r = di.decompileFunction(f, 30, monitor);
            if (r == null || !r.decompileCompleted() || r.getDecompiledFunction() == null) {
                failed++;
                continue;
            }

            completed++;
            String code = r.getDecompiledFunction().getC();
            if (code.contains("halt_baddata")) {
                baddata++;
            } else if (code.contains("WARNING")) {
                warnings++;
            } else {
                clean++;
            }
        }

        println("RESULT total=" + total
            + " completed=" + completed
            + " clean=" + clean
            + " warnings=" + warnings
            + " baddata=" + baddata
            + " failed=" + failed);
    }
}
