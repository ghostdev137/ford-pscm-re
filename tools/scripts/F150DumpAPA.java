// Dump APA-related F150 functions: 0x10183A8A (APA 0x3A8 handler) + callers + callees
// @category Pipeline
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;

public class F150DumpAPA extends GhidraScript {
    @Override
    public void run() throws Exception {
        Path out = Paths.get("/tmp/pscm/f150_apa");
        Files.createDirectories(out);
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        FunctionManager fm = currentProgram.getFunctionManager();
        ReferenceManager rm = currentProgram.getReferenceManager();
        AddressFactory af = currentProgram.getAddressFactory();

        // Primary APA handler + neighbors (for the known addresses)
        long[] targets = {
            0x10183a8aL,   // APA 0x3A8 handler (3042B)
            0x10041862L,   // CAN dispatch table location
        };
        for (long t : targets) {
            Address a = af.getDefaultAddressSpace().getAddress(t);
            Function f = fm.getFunctionAt(a);
            if (f == null) { println("no func 0x"+Long.toHexString(t)); continue; }
            StringBuilder sb = new StringBuilder();
            sb.append(String.format("// %s @0x%08x size=%d\n// CALLERS:\n", f.getName(), t, f.getBody().getNumAddresses()));
            int n=0;
            ReferenceIterator refs = rm.getReferencesTo(a);
            while (refs.hasNext() && n < 15) {
                Reference r = refs.next();
                if (r.getReferenceType().isCall() || r.getReferenceType().isJump()) {
                    Function caller = fm.getFunctionContaining(r.getFromAddress());
                    sb.append(String.format("//   from 0x%08x  in %s\n", r.getFromAddress().getOffset(),
                        caller != null ? caller.getName() : "?"));
                    n++;
                }
            }
            DecompileResults r = di.decompileFunction(f, 120, monitor);
            if (r != null && r.getDecompiledFunction() != null) sb.append(r.getDecompiledFunction().getC());
            Files.writeString(out.resolve(String.format("%08x.c", t)), sb.toString());
            println("wrote 0x" + Long.toHexString(t));
        }

        // Hunt for functions that reference the value 0x3A8 (decimal 936) as an immediate
        // This picks up dispatch table entries and any function comparing against that CAN ID
        println("\n=== functions with 0x3A8 references ===");
        Listing L = currentProgram.getListing();
        Set<Function> refFuncs = new LinkedHashSet<>();
        InstructionIterator it = L.getInstructions(true);
        while (it.hasNext() && !monitor.isCancelled()) {
            Instruction ins = it.next();
            for (int op = 0; op < ins.getNumOperands(); op++) {
                for (Object o : ins.getOpObjects(op)) {
                    if (o instanceof ghidra.program.model.scalar.Scalar) {
                        long v = ((ghidra.program.model.scalar.Scalar)o).getSignedValue();
                        if (v == 0x3A8L) {
                            Function f = fm.getFunctionContaining(ins.getAddress());
                            if (f != null) refFuncs.add(f);
                        }
                    }
                }
            }
        }
        StringBuilder listSb = new StringBuilder("Functions immediate-referencing 0x3A8:\n");
        for (Function f : refFuncs) {
            listSb.append(String.format("  %s @0x%08x size=%d\n",
                f.getName(), f.getEntryPoint().getOffset(), f.getBody().getNumAddresses()));
            println("  refs 0x3A8: " + f.getName() + " @0x" + Long.toHexString(f.getEntryPoint().getOffset()));
        }
        Files.writeString(out.resolve("_refs_3a8.txt"), listSb.toString());
        println("wrote _refs_3a8.txt");
    }
}
