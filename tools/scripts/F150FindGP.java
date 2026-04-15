// Find actual GP (r4) value by looking at GP-relative reference resolution in Ghidra
// @category Pipeline
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import ghidra.program.model.lang.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;

public class F150FindGP extends GhidraScript {
    @Override
    public void run() throws Exception {
        Path out = Paths.get("/tmp/pscm/f150_lca");
        Files.createDirectories(out);
        StringBuilder sb = new StringBuilder();

        // Method 1: Look at register values in the program context
        // Ghidra stores register values in ProgramContext
        ProgramContext ctx = currentProgram.getProgramContext();
        Register gp = currentProgram.getLanguage().getRegister("gp");
        if (gp == null) gp = currentProgram.getLanguage().getRegister("r4");
        sb.append("GP register: " + gp + "\n");

        // Find a known address to check if context has a value
        AddressFactory af = currentProgram.getAddressFactory();
        AddressSpace asp = af.getDefaultAddressSpace();

        if (gp != null) {
            // Try scanning a range of addresses for GP context value
            long[] checkAddrs = {0x10186afaL, 0x101a392aL, 0x101ab934L, 0x10097c28L, 0x101a4e4aL};
            for (long ta : checkAddrs) {
                try {
                    Address a = asp.getAddress(ta);
                    RegisterValue rv = ctx.getRegisterValue(gp, a);
                    if (rv != null && rv.hasValue()) {
                        sb.append(String.format("  GP at 0x%x = 0x%x\n", ta, rv.getUnsignedValue().longValue()));
                    } else {
                        sb.append(String.format("  GP at 0x%x = no context\n", ta));
                    }
                } catch (Exception e) {
                    sb.append(String.format("  GP at 0x%x = error: %s\n", ta, e.getMessage()));
                }
            }
        }

        // Method 2: Look for the actual address that FUN_10097c28 writes to
        // by scanning xrefs to near FEF21xxx or FEF23xxx from within it
        FunctionManager fm = currentProgram.getFunctionManager();
        Listing L = currentProgram.getListing();

        sb.append("\n=== FUN_10097c28 disasm (to find what it writes) ===\n");
        Function f = fm.getFunctionAt(asp.getAddress(0x10097c28L));
        if (f != null) {
            InstructionIterator it = L.getInstructions(f.getBody(), true);
            while (it.hasNext()) {
                Instruction ins = it.next();
                sb.append(String.format("  %s: %s\n", ins.getAddress(), ins));
                for (Reference r : ins.getReferencesFrom()) {
                    sb.append(String.format("    -> ref %s type=%s\n", r.getToAddress(), r.getReferenceType()));
                }
            }
        }

        // Method 3: Look for functions known to write to specific LCA globals
        // and check what global FUN_10097c28 is known to write to
        // (look at its callers' context: FUN_101aef34 calls it with (DAT_fef23847, torque))
        // DAT_fef23847 is a mode byte; torque goes into the short write
        // Let's check: what does FUN_10097c18 (called by FUN_101ad86c) return?
        sb.append("\n=== FUN_10097c18 disasm ===\n");
        Function fc18 = fm.getFunctionAt(asp.getAddress(0x10097c18L));
        if (fc18 != null) {
            InstructionIterator it = L.getInstructions(fc18.getBody(), true);
            while (it.hasNext()) {
                Instruction ins = it.next();
                sb.append(String.format("  %s: %s\n", ins.getAddress(), ins));
                for (Reference r : ins.getReferencesFrom()) {
                    sb.append(String.format("    -> ref %s\n", r.getToAddress()));
                }
            }
        }

        // Method 4: find functions that have GP-relative reads of known LCA globals
        // by checking FUN_101aef34 disasm in detail
        sb.append("\n=== FUN_101aef34 disasm ===\n");
        Function fef34 = fm.getFunctionAt(asp.getAddress(0x101aef34L));
        if (fef34 != null) {
            InstructionIterator it = L.getInstructions(fef34.getBody(), true);
            while (it.hasNext()) {
                Instruction ins = it.next();
                sb.append(String.format("  %s: %s\n", ins.getAddress(), ins));
                for (Reference r : ins.getReferencesFrom()) {
                    sb.append(String.format("    -> ref %s type=%s\n", r.getToAddress(), r.getReferenceType()));
                }
            }
        }

        Files.writeString(out.resolve("_gp_hunt.txt"), sb.toString());
        println("wrote _gp_hunt.txt (" + sb.length() + " bytes)");
    }
}
