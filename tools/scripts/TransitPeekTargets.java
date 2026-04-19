// Dump raw instruction windows and decompilations for selected Transit addresses.
// @category Pipeline
// @runtime Java
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileOptions;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSet;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.ReferenceManager;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

public class TransitPeekTargets extends GhidraScript {
    private static final long[] TARGETS = {
        0x010140C8L,
        0x01017F38L,
        0x0101A9ACL,
        0x0102085CL,
        0x01020906L,
        0x010E9A6AL,
        0x010E9E7CL,
        0x0106964EL,
        0x010CF970L,
        0x010B3B38L,
        0x010B3B4AL,
        0x010B5266L,
        0x010B7390L,
        0x010B7D98L,
        0x0107348EL,
        0x01074CF8L,
        0x0107C6D8L,
        0x010772E2L,
        0x010788E2L,
        0x01077B1EL,
        0x011078BAL,
        0x01107BC4L,
    };

    @Override
    public void run() throws Exception {
        Path outDir = Paths.get(System.getProperty(
            "transit.peek.out",
            "/tmp/pscm/transit_peek_targets"));
        Files.createDirectories(outDir);

        ReferenceManager rm = currentProgram.getReferenceManager();
        DecompInterface di = new DecompInterface();
        di.setOptions(new DecompileOptions());
        di.toggleCCode(true);
        di.toggleSyntaxTree(true);
        di.setSimplificationStyle("decompile");
        di.openProgram(currentProgram);

        for (long off : TARGETS) {
            Address a = toAddr(off);
            StringBuilder sb = new StringBuilder();
            sb.append(String.format("target=0x%08x\n\n", off));

            try {
                new DisassembleCommand(new AddressSet(a, a.add(0x80)), null, true)
                    .applyTo(currentProgram, monitor);
            } catch (Exception ignored) {
            }

            Function f = getFunctionContaining(a);
            if (f != null) {
                sb.append(String.format("function=%s entry=0x%08x size=%d\n\n",
                    f.getName(), f.getEntryPoint().getOffset(), f.getBody().getNumAddresses()));
                sb.append("refs_to_entry:\n");
                ReferenceIterator rit = rm.getReferencesTo(f.getEntryPoint());
                int rc = 0;
                while (rit.hasNext()) {
                    Reference ref = rit.next();
                    sb.append(String.format("  0x%08x -> 0x%08x  %s\n",
                        ref.getFromAddress().getOffset(),
                        f.getEntryPoint().getOffset(),
                        ref.getReferenceType()));
                    rc++;
                }
                if (rc == 0) {
                    sb.append("  (none)\n");
                }
                sb.append("\n");
            } else {
                sb.append("function=(none)\n\n");
            }

            sb.append("instruction_window:\n");
            Address start = a.subtract(0x20);
            Address end = a.add(0x60);
            InstructionIterator it = currentProgram.getListing().getInstructions(start, true);
            int count = 0;
            while (it.hasNext()) {
                Instruction ins = it.next();
                if (ins.getAddress().compareTo(end) > 0) {
                    break;
                }
                sb.append(String.format("  0x%08x  %s\n", ins.getAddress().getOffset(), ins.toString()));
                count++;
            }
            if (count == 0) {
                sb.append("  (no instructions)\n");
            }
            sb.append("\n");

            if (f != null) {
                sb.append("decompile:\n\n");
                DecompileResults dr = di.decompileFunction(f, 45, monitor);
                if (dr != null && dr.decompileCompleted() && dr.getDecompiledFunction() != null) {
                    sb.append(dr.getDecompiledFunction().getC());
                    sb.append("\n");
                } else if (dr != null) {
                    sb.append("decompile_failed: ");
                    sb.append(dr.getErrorMessage());
                    sb.append("\n");
                } else {
                    sb.append("decompile_returned_null\n");
                }
            }

            Files.writeString(outDir.resolve(String.format("%08x.txt", off)), sb.toString());
        }

        println("wrote peek target dumps to " + outDir);
    }
}
