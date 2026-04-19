// Dump callers, interesting instructions, and decompilation for functions given as script args.
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
import ghidra.program.model.listing.Listing;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.ReferenceManager;

import java.nio.file.Files;
import java.nio.file.Path;

public class DumpFunctionsByAddr extends GhidraScript {
    @Override
    public void run() throws Exception {
        if (getScriptArgs().length == 0) {
            println("usage: DumpFunctionsByAddr <addr> [addr...]");
            return;
        }

        Path out = Path.of(System.getenv().getOrDefault("DUMP_FUNCS_OUT", "/tmp/pscm/f150_timer_funcs"));
        Files.createDirectories(out);
        FunctionManager fm = currentProgram.getFunctionManager();
        ReferenceManager rm = currentProgram.getReferenceManager();
        Listing listing = currentProgram.getListing();
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);

        for (String raw : getScriptArgs()) {
            long target = Long.decode(raw);
            Address a = toAddr(target);
            Function f = fm.getFunctionAt(a);
            if (f == null) {
                f = fm.getFunctionContaining(a);
            }
            if (f == null) {
                println("no function at " + raw);
                continue;
            }

            StringBuilder sb = new StringBuilder();
            sb.append(String.format("// %s @ 0x%08x size=%d\n",
                f.getName(), f.getEntryPoint().getOffset(), f.getBody().getNumAddresses()));
            sb.append("// CALLERS:\n");
            ReferenceIterator refs = rm.getReferencesTo(f.getEntryPoint());
            while (refs.hasNext()) {
                Reference r = refs.next();
                if (!r.getReferenceType().isCall() && !r.getReferenceType().isJump()) {
                    continue;
                }
                Function caller = fm.getFunctionContaining(r.getFromAddress());
                sb.append(String.format("//   from 0x%08x in %s\n",
                    r.getFromAddress().getOffset(),
                    caller != null ? caller.getName() + String.format(" @ 0x%08x", caller.getEntryPoint().getOffset()) : "<no function>"));
            }

            sb.append("\n// ASM:\n");
            InstructionIterator it = listing.getInstructions(f.getBody(), true);
            while (it.hasNext()) {
                Instruction ins = it.next();
                String text = ins.toString().toLowerCase();
                if (text.contains("0x2710") || text.contains("0x27100") || text.contains("0x5dc")
                        || text.contains("0x12c") || text.contains("timer") || text.contains("cmp")
                        || text.contains("blt") || text.contains("bgt") || text.contains("jarl")) {
                    sb.append(String.format("//   %s  %s\n", ins.getAddress(), ins));
                }
            }

            sb.append("\n// DECOMPILE:\n");
            DecompileResults res = di.decompileFunction(f, 60, monitor);
            if (res != null && res.decompileCompleted() && res.getDecompiledFunction() != null) {
                sb.append(res.getDecompiledFunction().getC());
            } else {
                sb.append("// decompile failed\n");
            }

            Files.writeString(out.resolve(String.format("%08x_%s.c",
                f.getEntryPoint().getOffset(), f.getName())), sb.toString());
            println("wrote 0x" + Long.toHexString(f.getEntryPoint().getOffset()));
        }

        di.dispose();
    }
}
