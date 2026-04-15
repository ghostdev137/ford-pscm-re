// Force disassembly from Transit reset vector + run analysis.
// @category Pipeline
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.app.services.DataTypeManagerService;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.app.plugin.core.analysis.AutoAnalysisManager;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.util.CodeUnitInsertionException;
import ghidra.program.model.mem.Memory;

public class TransitForceAnalyze extends GhidraScript {
    @Override
    public void run() throws Exception {
        AddressFactory af = currentProgram.getAddressFactory();
        Address entry = af.getDefaultAddressSpace().getAddress(0x01002000L);
        println("Disassembling from " + entry);
        DisassembleCommand cmd = new DisassembleCommand(entry, null, true);
        cmd.applyTo(currentProgram, monitor);
        println("Initial disasm done; now creating function at entry.");
        try {
            Function f = createFunction(entry, "_reset");
            println("Created: " + f);
        } catch (Exception e) { println("createFunction err: " + e); }

        // Run the auto-analyzer
        AutoAnalysisManager mgr = AutoAnalysisManager.getAnalysisManager(currentProgram);
        mgr.reAnalyzeAll(null);
        mgr.startAnalysis(monitor);
        println("Analysis triggered.");
    }
}
