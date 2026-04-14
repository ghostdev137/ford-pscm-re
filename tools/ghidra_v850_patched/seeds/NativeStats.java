import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;

/* Stats-only: let Ghidra auto-analyze fully, then count clean decompiles.
 * Matches methodology from the F-150 99.97% measurement earlier in the session. */
public class NativeStats extends GhidraScript {
    @Override
    public void run() throws Exception {
        DecompInterface ifc = new DecompInterface();
        ifc.openProgram(currentProgram);
        int total = 0, clean = 0, failed = 0;
        FunctionIterator fit = currentProgram.getFunctionManager().getFunctions(true);
        while (fit.hasNext()) {
            if (monitor.isCancelled()) break;
            Function f = fit.next();
            if (f.isExternal() || f.isThunk()) continue;
            total++;
            DecompileResults res = ifc.decompileFunction(f, 60, monitor);
            if (res != null && res.decompileCompleted() && res.getDecompiledFunction() != null) clean++;
            else failed++;
        }
        println(String.format("RESULT tag=native total=%d clean=%d failed=%d pct=%.2f%%",
            total, clean, failed, total == 0 ? 0.0 : 100.0 * clean / total));
    }
}
