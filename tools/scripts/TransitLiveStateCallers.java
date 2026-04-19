// Dump callers of the Transit live-state setter functions.
// @category Pipeline
// @runtime Java
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileOptions;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.ReferenceManager;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.LinkedHashMap;
import java.util.Map;

public class TransitLiveStateCallers extends GhidraScript {
    private static final long[] TARGETS = {
        0x01020906L,
        0x0101A9ACL,
    };

    @Override
    public void run() throws Exception {
        Path outDir = Paths.get(System.getProperty(
            "transit.livestate.out",
            "/tmp/pscm/transit_live_state_callers"));
        Files.createDirectories(outDir);

        ReferenceManager rm = currentProgram.getReferenceManager();
        DecompInterface di = new DecompInterface();
        di.setOptions(new DecompileOptions());
        di.toggleCCode(true);
        di.toggleSyntaxTree(true);
        di.setSimplificationStyle("decompile");
        di.openProgram(currentProgram);

        for (long targetOff : TARGETS) {
            Address target = toAddr(targetOff);
            Function targetFn = getFunctionContaining(target);
            StringBuilder sb = new StringBuilder();
            sb.append(String.format("target=0x%08x\n", targetOff));
            if (targetFn == null) {
                sb.append("target_function=(none)\n");
                Files.writeString(outDir.resolve(String.format("%08x.txt", targetOff)), sb.toString());
                continue;
            }
            sb.append(String.format("target_function=%s entry=0x%08x size=%d\n\n",
                targetFn.getName(), targetFn.getEntryPoint().getOffset(), targetFn.getBody().getNumAddresses()));

            Map<Long, Function> callers = new LinkedHashMap<>();
            ReferenceIterator rit = rm.getReferencesTo(targetFn.getEntryPoint());
            while (rit.hasNext()) {
                Reference ref = rit.next();
                Function caller = getFunctionContaining(ref.getFromAddress());
                if (caller != null) {
                    callers.put(caller.getEntryPoint().getOffset(), caller);
                }
                sb.append(String.format("xref 0x%08x -> 0x%08x  %s  %s\n",
                    ref.getFromAddress().getOffset(),
                    targetFn.getEntryPoint().getOffset(),
                    ref.getReferenceType(),
                    caller == null ? "(none)" :
                        String.format("%s @ 0x%08x", caller.getName(), caller.getEntryPoint().getOffset())));
            }
            if (callers.isEmpty()) {
                sb.append("xref (none)\n");
            }
            sb.append("\n");

            for (Function caller : callers.values()) {
                sb.append(String.format("caller=%s entry=0x%08x size=%d\n",
                    caller.getName(), caller.getEntryPoint().getOffset(), caller.getBody().getNumAddresses()));
                appendWindow(sb, caller.getEntryPoint(), 0x20, 0x90);
                sb.append("\n");
                DecompileResults dr = di.decompileFunction(caller, 60, monitor);
                if (dr != null && dr.decompileCompleted() && dr.getDecompiledFunction() != null) {
                    sb.append(dr.getDecompiledFunction().getC());
                } else if (dr != null) {
                    sb.append("decompile_failed: ").append(dr.getErrorMessage()).append("\n");
                } else {
                    sb.append("decompile_returned_null\n");
                }
                sb.append("\n\n");
            }

            Files.writeString(outDir.resolve(String.format("%08x.txt", targetOff)), sb.toString());
        }

        println("wrote live state caller dumps to " + outDir);
    }

    private void appendWindow(StringBuilder sb, Address startAddr, long before, long after) {
        Address start = startAddr.subtract(before);
        Address end = startAddr.add(after);
        InstructionIterator it = currentProgram.getListing().getInstructions(start, true);
        sb.append("instruction_window:\n");
        while (it.hasNext()) {
            Instruction ins = it.next();
            if (ins.getAddress().compareTo(end) > 0) {
                break;
            }
            sb.append(String.format("  0x%08x  %s\n", ins.getAddress().getOffset(), ins.toString()));
        }
    }
}
