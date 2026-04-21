// Count functions in the current program. Quick diagnostic.
// @category Transit
// @runtime Java
import ghidra.app.script.GhidraScript;
public class CountFunctions extends GhidraScript {
    @Override
    public void run() {
        long n = 0;
        for (var f : currentProgram.getFunctionManager().getFunctions(true)) n++;
        println("total_functions=" + n);
    }
}
