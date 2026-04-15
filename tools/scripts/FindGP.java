// Find V850 gp init: scan all instructions for ones writing to register 'gp' (r4)
// @category Pipeline
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.lang.Register;
import ghidra.program.model.scalar.Scalar;
import java.nio.file.*;

public class FindGP extends GhidraScript {
    @Override
    public void run() throws Exception {
        Listing L = currentProgram.getListing();
        StringBuilder sb = new StringBuilder();
        // Start at entry point
        Address entry = currentProgram.getImageBase().add(0);
        // Iterate from entry; look at first 100 insns for movhi/movea with 'gp' in toString
        Function start = getFirstFunction();
        sb.append("First function: " + start.getName() + " @" + start.getEntryPoint() + "\n");
        // Actually scan entry point area
        AddressFactory af = currentProgram.getAddressFactory();
        Address a = af.getDefaultAddressSpace().getAddress(0x10040000L);
        Instruction ins = L.getInstructionAt(a);
        if (ins == null) {
            // Disassemble at entry
            disassemble(a);
            ins = L.getInstructionAt(a);
        }
        int n = 0;
        long hi = -1, lo = -1;
        while (ins != null && n++ < 100) {
            String s = ins.toString();
            if (s.contains("gp")) {
                sb.append(String.format("  0x%08x  %s\n", ins.getAddress().getOffset(), s));
                // parse scalar operands
                String m = ins.getMnemonicString().toLowerCase();
                if (m.equals("movhi")) {
                    for (Object o : ins.getOpObjects(0)) if (o instanceof Scalar) hi = ((Scalar)o).getUnsignedValue();
                } else if (m.equals("movea") || m.equals("mov")) {
                    for (Object o : ins.getOpObjects(0)) if (o instanceof Scalar) lo = ((Scalar)o).getSignedValue();
                }
                if (hi >= 0 && lo != -1) { sb.append(String.format("GP = (0x%x<<16)+0x%x = 0x%08x\n", hi, lo, (hi<<16)+lo)); break; }
            }
            ins = ins.getNext();
        }
        Files.writeString(Paths.get("/tmp/pscm/f150_apa/_gp.txt"), sb.toString());
        println("wrote _gp.txt");
    }
}
