// Find the actual GP value and LCA output torque global address
// @category Pipeline
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import ghidra.program.model.scalar.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;

public class F150LCAOutput extends GhidraScript {
    @Override
    public void run() throws Exception {
        Path out = Paths.get("/tmp/pscm/f150_lca");
        Files.createDirectories(out);
        StringBuilder sb = new StringBuilder();

        AddressFactory af = currentProgram.getAddressFactory();
        AddressSpace asp = af.getDefaultAddressSpace();
        FunctionManager fm = currentProgram.getFunctionManager();
        Listing L = currentProgram.getListing();
        ReferenceManager rm = currentProgram.getReferenceManager();

        // Strategy: FUN_10097c28 uses st.b r6,-0x929d[gp] and st.w r17,-0x92b8[gp]
        // We need GP. Let's find functions near 10097c28 that use gp-relative addressing
        // AND resolve to known addresses, then back-compute GP.
        //
        // Better: look at FUN_10097c18 which does: ld.bu -0x15088[gp],r10
        // and FUN_101ad86c calls it as: DAT_fef23842 = FUN_10097c18()
        // So: gp - 0x15088 = 0xfef23842
        // => gp = 0xfef23842 + 0x15088 = 0xfef388ca
        // ... that seems too high. Let me recalculate:
        // 0xfef23842 + 0x15088 = ?
        long gpFromC18 = 0xfef23842L + 0x15088L;
        sb.append(String.format("GP estimate from FUN_10097c18 (-0x15088): 0x%x\n", gpFromC18));
        // 0xfef23842 + 0x15088 = 0xfef388ca - seems wrong, likely signed offset
        // Actually for V850 instruction: ld.bu disp16[reg] - disp is signed 16-bit
        // -0x15088 overflows 16-bit. Let's check: 0x15088 as negative 16-bit...
        // Actually in V850E3 LDBU encoding uses larger displacement. But -0x15088 in
        // 2's complement for signed 17-bit is valid (V850E3 can have 23-bit displacement)
        // More likely: disasm shows -0x15088[gp] with gp pointing to some area
        // Let's try a different approach: scan FUN_10097c28's known writes and find Ghidra refs

        // Look at all references FROM instructions in FUN_10097c28
        sb.append("\n=== All data refs from FUN_10097c28 ===\n");
        Function f28 = fm.getFunctionAt(asp.getAddress(0x10097c28L));
        if (f28 != null) {
            InstructionIterator it = L.getInstructions(f28.getBody(), true);
            while (it.hasNext()) {
                Instruction ins = it.next();
                for (Reference r : ins.getReferencesFrom()) {
                    if (!r.getReferenceType().isCall() && !r.getReferenceType().isJump()) {
                        sb.append(String.format("  %s: %s -> 0x%x type=%s\n",
                            ins.getAddress(), ins.getMnemonicString(),
                            r.getToAddress().getOffset(), r.getReferenceType()));
                    }
                }
            }
        }

        // Also look at FUN_10097c18 to resolve its read address
        sb.append("\n=== All data refs from FUN_10097c18 ===\n");
        Function f18 = fm.getFunctionAt(asp.getAddress(0x10097c18L));
        if (f18 != null) {
            InstructionIterator it = L.getInstructions(f18.getBody(), true);
            while (it.hasNext()) {
                Instruction ins = it.next();
                sb.append(String.format("  %s: %s\n", ins.getAddress(), ins));
                for (Reference r : ins.getReferencesFrom()) {
                    if (!r.getReferenceType().isCall() && !r.getReferenceType().isJump()) {
                        sb.append(String.format("    -> 0x%x type=%s\n",
                            r.getToAddress().getOffset(), r.getReferenceType()));
                    }
                }
            }
        }

        // Scan all functions for writes to addresses in fef21a00-fef21bff range
        // (parallel to LKA output at fef21a78) - LCA output might be at similar offset
        sb.append("\n=== Functions writing to fef21xxx range (output candidates) ===\n");
        Map<Function, List<Long>> fef21Writers = new LinkedHashMap<>();
        for (long addr = 0xfef21a00L; addr < 0xfef22000L; addr += 2) {
            Address a2 = asp.getAddress(addr);
            ReferenceIterator refs = rm.getReferencesTo(a2);
            while (refs.hasNext()) {
                Reference r = refs.next();
                if (r.getReferenceType().isWrite()) {
                    Function wf = fm.getFunctionContaining(r.getFromAddress());
                    if (wf != null) {
                        fef21Writers.computeIfAbsent(wf, k -> new ArrayList<>()).add(addr);
                    }
                }
            }
        }
        fef21Writers.forEach((f, addrs) -> {
            sb.append(String.format("  %s @ 0x%x  writes=%d\n",
                f.getName(), f.getEntryPoint().getOffset(), addrs.size()));
            addrs.forEach(a -> sb.append(String.format("    0x%x\n", a)));
        });

        // The LCA torque output might be via FUN_10097c28 which is a Com_Send shim
        // Let's find what address it sends to by examining ALL xrefs to its outputs
        // or by looking at functions that READ what FUN_10097c28 wrote
        // Alternatively: find similar functions (same size ~50) near 10097c28
        // and see if any has a resolved write ref
        sb.append("\n=== Functions near 10097c28 that write to resolved addresses ===\n");
        for (long t = 0x10097c00L; t < 0x10097e00L; t += 2) {
            Function fn = fm.getFunctionAt(asp.getAddress(t));
            if (fn == null || fn.getBody().getNumAddresses() > 200) continue;
            InstructionIterator it = L.getInstructions(fn.getBody(), true);
            while (it.hasNext()) {
                Instruction ins = it.next();
                for (Reference r : ins.getReferencesFrom()) {
                    if (r.getReferenceType().isWrite()) {
                        long wa = r.getToAddress().getOffset();
                        if (wa >= 0xfef00000L && wa < 0xfff00000L) {
                            sb.append(String.format("  FUN_%08x writes 0x%x (at insn %s)\n",
                                t, wa, ins.getAddress()));
                        }
                    }
                }
            }
        }

        // Find what FUN_101af6da does (called after FUN_101aef34 in FUN_101a9fa2)
        sb.append("\n=== FUN_101af6da (called after FUN_101aef34) ===\n");
        Function faf6da = fm.getFunctionAt(asp.getAddress(0x101af6daL));
        if (faf6da != null) {
            sb.append(String.format("size=%d\n", faf6da.getBody().getNumAddresses()));
            InstructionIterator it = L.getInstructions(faf6da.getBody(), true);
            while (it.hasNext()) {
                Instruction ins = it.next();
                sb.append(String.format("  %s: %s\n", ins.getAddress(), ins));
                for (Reference r : ins.getReferencesFrom()) {
                    if (!r.getReferenceType().isJump()) {
                        sb.append(String.format("    -> 0x%x type=%s\n",
                            r.getToAddress().getOffset(), r.getReferenceType()));
                    }
                }
            }
        }

        Files.writeString(out.resolve("_lca_output.txt"), sb.toString());
        println("wrote _lca_output.txt (" + sb.length() + " bytes)");
    }
}
