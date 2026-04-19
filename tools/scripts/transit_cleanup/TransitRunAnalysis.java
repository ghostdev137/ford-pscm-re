// Run seeded analysis explicitly from a post-script after setting analyzer options.
// This bypasses the default headless auto-analysis path, which may still run
// analyzers like Function Start Search even when disabled.
// @category Transit
// @runtime Java
import ghidra.app.plugin.core.analysis.AutoAnalysisManager;
import ghidra.app.script.GhidraScript;

import java.util.Map;

public class TransitRunAnalysis extends GhidraScript {
    @Override
    public void run() throws Exception {
        runScript("SetOptions.java", new String[0], state);

        Map<String, String> options = getCurrentAnalysisOptionsAndValues(currentProgram);
        String[] interesting = {
            "Function Start Search",
            "Shared Return Calls",
            "Decompiler Parameter ID",
            "Call Convention ID",
            "Non-Returning Functions - Discovered",
            "Aggressive Instruction Finder"
        };
        for (String option : interesting) {
            String value = options.get(option);
            if (value != null) {
                println("analysis option " + option + "=" + value);
            }
        }

        AutoAnalysisManager mgr = AutoAnalysisManager.getAnalysisManager(currentProgram);
        mgr.reAnalyzeAll(currentProgram.getMemory());
        mgr.startAnalysis(monitor, false);
        println("analysis task summary:");
        println(mgr.getTaskTimesString());
    }
}
