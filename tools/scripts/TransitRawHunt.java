// Transit APA lockout hunt via raw instruction-level pattern matching.
// No decompilation (SLEIGH decompile broken on r1115). Just disasm + walk instructions.
//
// Fingerprint (ISA-agnostic adaptation of F150 pattern):
//   Within a ~64-byte window, find:
//     (a) 2x jarl calls
//     (b) A st.b writing some source register rS to [base + disp1]
//     (c) Within 20 bytes, another st.b writing SAME rS to [base + disp2] (disp1 != disp2)
//   Base register can be gp (like F150) or ep (likely on Transit).
//
// @category Pipeline
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.lang.Register;
import ghidra.program.model.scalar.Scalar;
import java.io.*;
import java.nio.file.*;
import java.util.*;

public class TransitRawHunt extends GhidraScript {
    @Override
    public void run() throws Exception {
        Path out = Paths.get("/tmp/pscm/transit_apa");
        Files.createDirectories(out);
        StringBuilder sb = new StringBuilder();
        Listing L = currentProgram.getListing();
        AddressFactory af = currentProgram.getAddressFactory();

        // 1) Force-disassemble blk0 code region if not already done
        Address start = af.getDefaultAddressSpace().getAddress(0x01002000L);
        Address end = af.getDefaultAddressSpace().getAddress(0x010FFFFFL);
        sb.append("Disassembling " + start + " to " + end + "\n");
        DisassembleCommand cmd = new DisassembleCommand(new AddressSet(start, end), null, true);
        cmd.applyTo(currentProgram, monitor);

        // 2) Collect all instructions into a linear list
        List<Instruction> insns = new ArrayList<>();
        InstructionIterator it = L.getInstructions(new AddressSet(start, end), true);
        while (it.hasNext()) insns.add(it.next());
        sb.append("Total instructions: " + insns.size() + "\n");

        // Helper: is this a st.b-like instruction writing [base + disp]?
        // Returns {srcReg, disp, base} or null.
        // 3) Sliding window hunt. For each st.b insn, search within next 32 insns for a matching sibling.
        List<String> hits = new ArrayList<>();
        for (int i = 0; i < insns.size(); i++) {
            Instruction a = insns.get(i);
            String am = a.getMnemonicString().toLowerCase();
            if (!am.equals("st.b") && !am.equals("sst.b")) continue;
            Object[] aOps0 = a.getOpObjects(0); // source reg
            Object[] aOps1 = a.getOpObjects(1); // [disp, base]
            int aSrcReg = -1; long aDisp = 0; String aBase = "";
            for (Object o : aOps0) if (o instanceof Register) aSrcReg = ((Register)o).getOffset();
            for (Object o : aOps1) {
                if (o instanceof Scalar) aDisp = ((Scalar)o).getSignedValue();
                if (o instanceof Register) aBase = ((Register)o).getName();
            }
            if (aSrcReg < 0 || aBase.isEmpty()) continue;

            // Search next up to 32 insns for sibling
            for (int j = i + 1; j < Math.min(i + 32, insns.size()); j++) {
                Instruction b = insns.get(j);
                String bm = b.getMnemonicString().toLowerCase();
                if (!bm.equals("st.b") && !bm.equals("sst.b")) continue;
                Object[] bOps0 = b.getOpObjects(0);
                Object[] bOps1 = b.getOpObjects(1);
                int bSrcReg = -1; long bDisp = 0; String bBase = "";
                for (Object o : bOps0) if (o instanceof Register) bSrcReg = ((Register)o).getOffset();
                for (Object o : bOps1) {
                    if (o instanceof Scalar) bDisp = ((Scalar)o).getSignedValue();
                    if (o instanceof Register) bBase = ((Register)o).getName();
                }
                if (bSrcReg == aSrcReg && bBase.equals(aBase) && bDisp != aDisp) {
                    // count jarl before a (within 64 insns earlier)
                    int jarlCount = 0;
                    int scanStart = Math.max(0, i - 32);
                    for (int k = scanStart; k < i; k++) {
                        String km = insns.get(k).getMnemonicString().toLowerCase();
                        if (km.equals("jarl")) jarlCount++;
                    }
                    if (jarlCount >= 2) {
                        String line = String.format("PAIR @0x%08x %s -> @0x%08x %s  src=reg%d base=%s disp1=0x%x disp2=0x%x jarls_before=%d",
                            a.getAddress().getOffset(), a.toString(),
                            b.getAddress().getOffset(), b.toString(),
                            aSrcReg, aBase, aDisp, bDisp, jarlCount);
                        hits.add(line);
                    }
                    break;  // only record nearest sibling
                }
            }
        }

        sb.append("\n=== Candidate lockout sites (" + hits.size() + ") ===\n");
        for (String h : hits) sb.append(h + "\n");

        // 4) For each hit, also dump the surrounding context (24 insns preceding the pair)
        sb.append("\n=== Context for each hit ===\n");
        for (String h : hits) {
            long addr = Long.parseLong(h.substring(h.indexOf("0x") + 2, h.indexOf(' ', h.indexOf("0x"))), 16);
            sb.append("\n-- " + h + " --\n");
            // find that insn in list
            for (int i = 0; i < insns.size(); i++) {
                if (insns.get(i).getAddress().getOffset() == addr) {
                    int from = Math.max(0, i - 24);
                    for (int k = from; k <= Math.min(insns.size()-1, i + 10); k++) {
                        sb.append(String.format("  %08x  %s\n", insns.get(k).getAddress().getOffset(), insns.get(k).toString()));
                    }
                    break;
                }
            }
        }

        Files.writeString(out.resolve("_raw_hunt.txt"), sb.toString());
        println("done: " + hits.size() + " pair hits");
    }
}
