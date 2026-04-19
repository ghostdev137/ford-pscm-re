// Dump specific functions by address with callers and a local instruction window.
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

public class DumpFunctionTargets extends GhidraScript {
    private long parseLongArg(String value) {
        String s = value.trim().toLowerCase();
        if (s.startsWith("0x")) {
            return Long.parseUnsignedLong(s.substring(2), 16);
        }
        return Long.parseLong(s);
    }

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length == 0) {
            println("usage: DumpFunctionTargets.java <addr> [<addr> ...]");
            return;
        }

        Path out = Paths.get(System.getenv().getOrDefault(
            "DUMP_FUNCTION_TARGETS_OUT",
            "/tmp/ghidra_dump_function_targets"));
        Files.createDirectories(out);

        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);

        FunctionManager fm = currentProgram.getFunctionManager();
        ReferenceManager rm = currentProgram.getReferenceManager();

        for (String arg : args) {
            long target = parseLongArg(arg);
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

        di.dispose();
    }
}
