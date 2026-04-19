// Dump specific Transit functions with callers and a local instruction window.
// @category Probe
// @runtime Java

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.ReferenceManager;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

public class TransitDumpMany extends GhidraScript {
    private static final long[] TARGETS = {
        0x01090ca6L,
        0x01093354L,
        0x010a11f2L,
        0x010a63eeL,
        0x0108dbeaL,
        0x010977d4L,
        0x010b9f90L,
        0x010b7274L,
        0x010b7390L,
        0x010b757eL,
        0x20ffde86L,
        0x20fff8a8L,
        0x210073beL,
        0x2100740eL,
        0x21007458L,
        0x210074e4L,
    };

    @Override
    public void run() throws Exception {
        Path out = Paths.get(System.getProperty(
            "transit.dumpmany.out",
            "/tmp/pscm/transit_lka_targets"));
        Files.createDirectories(out);

        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);

        FunctionManager fm = currentProgram.getFunctionManager();
        ReferenceManager rm = currentProgram.getReferenceManager();

        for (long target : TARGETS) {
            Address addr = toAddr(target);
            Function f = fm.getFunctionContaining(addr);
            StringBuilder sb = new StringBuilder();
            sb.append(String.format("target=0x%08x\n", target));
            if (f == null) {
                sb.append("function=(none)\n");
                Files.writeString(out.resolve(String.format("%08x.txt", target)), sb.toString());
                continue;
            }

            sb.append(String.format("function=%s entry=0x%08x size=%d\n\n",
                f.getName(), f.getEntryPoint().getOffset(), f.getBody().getNumAddresses()));

            sb.append("refs_to_entry:\n");
            ReferenceIterator refs = rm.getReferencesTo(f.getEntryPoint());
            int refCount = 0;
            while (refs.hasNext()) {
                Reference ref = refs.next();
                if (!ref.getReferenceType().isCall() && !ref.getReferenceType().isJump()) {
                    continue;
                }
                Function caller = fm.getFunctionContaining(ref.getFromAddress());
                sb.append(String.format("  0x%08x -> 0x%08x  %s  %s\n",
                    ref.getFromAddress().getOffset(),
                    f.getEntryPoint().getOffset(),
                    ref.getReferenceType(),
                    caller == null ? "(none)" :
                        String.format("%s @ 0x%08x", caller.getName(), caller.getEntryPoint().getOffset())));
                refCount++;
            }
            if (refCount == 0) {
                sb.append("  (none)\n");
            }

            sb.append("\ninstruction_window:\n");
            Address start = f.getEntryPoint().subtract(0x20);
            Address end = f.getEntryPoint().add(0x180);
            InstructionIterator it = currentProgram.getListing().getInstructions(start, true);
            while (it.hasNext()) {
                Instruction ins = it.next();
                if (ins.getAddress().compareTo(end) > 0) {
                    break;
                }
                sb.append(String.format("  0x%08x  %s\n",
                    ins.getAddress().getOffset(),
                    ins.toString()));
            }

            sb.append("\ndecompile:\n\n");
            DecompileResults dr = di.decompileFunction(f, 60, monitor);
            if (dr != null && dr.decompileCompleted() && dr.getDecompiledFunction() != null) {
                sb.append(dr.getDecompiledFunction().getC());
            } else if (dr != null) {
                sb.append("decompile_failed: ").append(dr.getErrorMessage()).append("\n");
            } else {
                sb.append("decompile_returned_null\n");
            }

            Files.writeString(out.resolve(String.format("%08x.txt", target)), sb.toString());
            println("wrote 0x" + Long.toHexString(target));
        }
    }
}
