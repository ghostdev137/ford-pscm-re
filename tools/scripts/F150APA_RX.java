// Find F150 APA RX unpacker. APA task is FUN_1017fd92 — dump its sub-calls.
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

public class F150APA_RX extends GhidraScript {
    @Override
    public void run() throws Exception {
        Path out = Paths.get("/tmp/pscm/f150_apa");
        Files.createDirectories(out);
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        FunctionManager fm = currentProgram.getFunctionManager();
        ReferenceManager rm = currentProgram.getReferenceManager();
        AddressFactory af = currentProgram.getAddressFactory();

        // Dump APA task
        long[] toDump = {0x1017fd92L};
        for (long t : toDump) {
            Address a = af.getDefaultAddressSpace().getAddress(t);
            Function f = fm.getFunctionAt(a);
            if (f == null) continue;
            DecompileResults r = di.decompileFunction(f, 30, monitor);
            String code = (r != null && r.getDecompiledFunction() != null) ? r.getDecompiledFunction().getC() : "// failed";
            Files.writeString(out.resolve(String.format("%08x.c", t)),
                String.format("// %s size=%d\n%s", f.getName(), f.getBody().getNumAddresses(), code));
            println("wrote 0x" + Long.toHexString(t));
        }

        // Find the RX unpacker for APA: look for functions that have many consecutive jarl calls
        // In the address space 0x1018xxxx-0x1019xxxx (adjacent to APA handler)
        // Pattern: a function with 5+ calls, small size (<300B), writes to fef2xxxx
        println("\nHunting for APA RX unpacker candidates...");
        for (Function f : fm.getFunctions(true)) {
            long addr = f.getEntryPoint().getOffset();
            if (addr < 0x10180000L || addr > 0x101a0000L) continue;
            if (f.getBody().getNumAddresses() > 500) continue;
            // Count jarl instructions inside
            Listing L = currentProgram.getListing();
            InstructionIterator it = L.getInstructions(f.getBody(), true);
            int calls = 0;
            int numWrites = 0;
            while (it.hasNext()) {
                Instruction ins = it.next();
                String m = ins.getMnemonicString();
                if (m.equalsIgnoreCase("jarl")) calls++;
                for (Reference ref : ins.getReferencesFrom()) {
                    if (ref.getReferenceType().isWrite()
                        && ref.getToAddress().getOffset() >= 0xfef20000L
                        && ref.getToAddress().getOffset() < 0xfef30000L) {
                        numWrites++;
                    }
                }
            }
            if (calls >= 5 && numWrites >= 3) {
                println(String.format("  CAND %s @0x%x size=%d calls=%d writes=%d",
                    f.getName(), addr, f.getBody().getNumAddresses(), calls, numWrites));
            }
        }

        // Also: dump known big RX helper FUN_10183768 which APA main calls
        for (long t : new long[]{0x10183768L, 0x10183846L, 0x10183984L, 0x1018392eL}) {
            Address a = af.getDefaultAddressSpace().getAddress(t);
            Function f = fm.getFunctionAt(a);
            if (f == null) continue;
            DecompileResults r = di.decompileFunction(f, 60, monitor);
            String code = (r != null && r.getDecompiledFunction() != null) ? r.getDecompiledFunction().getC() : "// failed";
            Files.writeString(out.resolve(String.format("helper_%08x.c", t)),
                String.format("// %s size=%d\n%s", f.getName(), f.getBody().getNumAddresses(), code));
            println("wrote helper 0x" + Long.toHexString(t));
        }
    }
}
