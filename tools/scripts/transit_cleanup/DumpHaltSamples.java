// Dumps decompile + disasm for a few halt_baddata functions to understand root cause.
// @category Transit
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;

public class DumpHaltSamples extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] targets = {"01007b0c","01008394","0100d388","0100cc88","01002028"};
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        FunctionManager fm = currentProgram.getFunctionManager();
        Listing listing = currentProgram.getListing();
        for (String t : targets) {
            Address a = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(Long.parseLong(t,16));
            Function f = fm.getFunctionAt(a);
            if (f==null){ println("NO FUNC "+t); continue; }
            println("==== FUNCTION "+t+" size="+f.getBody().getNumAddresses()+" ====");
            // disasm
            InstructionIterator it = listing.getInstructions(f.getBody(), true);
            int n=0;
            while (it.hasNext() && n<40) {
                Instruction ins = it.next();
                println(String.format("  %s  %-10s %s", ins.getAddress(), ins.getMnemonicString(), ins.toString()));
                n++;
            }
            DecompileResults dr = di.decompileFunction(f, 15, monitor);
            if (dr != null && dr.decompileCompleted()) {
                String c = dr.getDecompiledFunction().getC();
                String[] lines = c.split("\n");
                for (int i=0;i<Math.min(40,lines.length);i++) println("    | "+lines[i]);
            }
            println("");
        }
        di.dispose();
    }
}
