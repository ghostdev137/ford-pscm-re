// Probe references and instruction windows around key Transit addresses.
// @category Pipeline
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.ReferenceManager;

public class TransitRefProbe extends GhidraScript {
    private static final long[] TARGETS = {
        0x010CE5DEL,
        0x010CE636L,
        0x010CE638L,
        0x010B4AD4L,
        0x010B4AD6L,
        0x010B4B10L,
        0x010B4B12L,
        0x010B4C98L,
        0x010B4CAAL,
        0x010B4CB0L,
    };

    @Override
    public void run() throws Exception {
        ReferenceManager rm = currentProgram.getReferenceManager();

        for (long off : TARGETS) {
            Address a = toAddr(off);
            println(String.format("== target 0x%08x ==", off));
            Function f = getFunctionContaining(a);
            if (f != null) {
                println(String.format("containing function: %s %s size=%d",
                    f.getEntryPoint(), f.getName(), f.getBody().getNumAddresses()));
            } else {
                println("containing function: (none)");
            }

            println("refs to target:");
            ReferenceIterator rit = rm.getReferencesTo(a);
            int refCount = 0;
            while (rit.hasNext()) {
                Reference ref = rit.next();
                Function rf = getFunctionContaining(ref.getFromAddress());
                println(String.format("  %s -> %s type=%s func=%s",
                    ref.getFromAddress(),
                    a,
                    ref.getReferenceType(),
                    rf == null ? "(none)" :
                        rf.getEntryPoint().toString() + " " + rf.getName()));
                refCount++;
            }
            if (refCount == 0) {
                println("  (none)");
            }

            println("instruction window:");
            Address start = a.subtract(0x10);
            InstructionIterator it = currentProgram.getListing().getInstructions(start, true);
            int shown = 0;
            while (it.hasNext() && shown < 16) {
                Instruction ins = it.next();
                if (ins.getAddress().compareTo(a.add(0x18)) > 0) {
                    break;
                }
                println(String.format("  %s  %s", ins.getAddress(), ins));
                shown++;
            }
            println("");
        }
    }
}
