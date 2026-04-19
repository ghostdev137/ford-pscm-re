// Disable noisy analyzers for seed-audit runs.
// @category Transit
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.framework.options.Options;

public class SeedAuditSetOptions extends GhidraScript {
    @Override
    public void run() throws Exception {
        Options opts = currentProgram.getOptions("Analyzers");
        String[] names = {
            "Aggressive Instruction Finder",
            "Aggressive Instruction Finder.Create Analysis Bookmarks"
        };
        for (String n : names) {
            try {
                opts.setBoolean(n, false);
                println("disabled: " + n);
            } catch (Exception e) {
                println("skip " + n + ": " + e);
            }
        }
        for (String n : new String[] {
            "Decompiler Switch Analysis",
            "Non-Returning Functions - Discovered",
            "Function Start Search",
            "Decompiler Parameter ID"
        }) {
            try {
                opts.setBoolean(n, true);
            } catch (Exception e) {
                // Seed-audit is best-effort only.
            }
        }
    }
}
