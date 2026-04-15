// Find any register-init that composes to a 0x101Dxxxx / 0x101Exxxx / 0x101Fxxxx flash address,
// and also dump tp / ep init sequences.
// @category Pipeline
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;

public class F150FindCalInit extends GhidraScript {
    @Override
    public void run() throws Exception {
        Listing L = currentProgram.getListing();
        InstructionIterator it = L.getInstructions(true);
        Instruction prev = null;
        int calCandidates = 0, tpEpInits = 0;
        while (it.hasNext() && !monitor.isCancelled()) {
            Instruction ins = it.next();
            String m = ins.getMnemonicString();
            if ("movhi".equalsIgnoreCase(m)) {
                if (ins.getNumOperands() >= 3) {
                    try {
                        Object[] r = ins.getOpObjects(0);
                        if (r != null && r.length > 0 && r[0] instanceof ghidra.program.model.scalar.Scalar) {
                            long imm = ((ghidra.program.model.scalar.Scalar)r[0]).getSignedValue();
                            long hi = (imm & 0xFFFF) << 16;
                            // Interesting flash-cal upper halves
                            if (hi == 0x101D0000L || hi == 0x101E0000L || hi == 0x101F0000L || hi == 0x10200000L
                                || hi == 0x10100000L || hi == 0x101C0000L) {
                                String dest = ins.getDefaultOperandRepresentation(2);
                                println(String.format("  %s  movhi 0x%04x,r0,%s  (hi=0x%08x)",
                                    ins.getAddress(), imm & 0xFFFF, dest, hi));
                                calCandidates++;
                            }
                        }
                    } catch (Exception e) {}
                    String dest = ins.getDefaultOperandRepresentation(2);
                    if ("tp".equals(dest) || "ep".equals(dest) || "r5".equals(dest) || "r30".equals(dest)) {
                        prev = ins;
                        continue;
                    }
                }
            }
            if (prev != null && ("addi".equalsIgnoreCase(m) || "movea".equalsIgnoreCase(m))) {
                String dest = ins.getDefaultOperandRepresentation(2);
                if (dest.equals(prev.getDefaultOperandRepresentation(2))) {
                    println(String.format("  TP/EP init: %s: %s | %s: %s",
                        prev.getAddress(), prev, ins.getAddress(), ins));
                    tpEpInits++;
                }
            }
            prev = null;
        }
        println("cal-upper movhi hits: " + calCandidates);
        println("tp/ep init pairs: " + tpEpInits);
    }
}
