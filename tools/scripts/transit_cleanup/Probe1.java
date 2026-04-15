// @category Transit
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.mem.Memory;
public class Probe1 extends GhidraScript {
    public void run() throws Exception {
        FunctionManager fm = currentProgram.getFunctionManager();
        Memory mem = currentProgram.getMemory();
        Listing L = currentProgram.getListing();
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        long[] addrs = {0x01000400L, 0x01000090L, 0x01000520L, 0x01001176L};
        for (long a : addrs) {
            Address A = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(a);
            Function f = fm.getFunctionAt(A);
            if (f == null) { println("no func at " + A); continue; }
            println("=== " + A + " body=" + f.getBody().getMinAddress() + ".." + f.getBody().getMaxAddress() + " size=" + f.getBody().getNumAddresses());
            // list instructions
            InstructionIterator it = L.getInstructions(f.getBody(), true);
            int n = 0;
            while (it.hasNext() && n < 30) {
                Instruction ins = it.next();
                println(String.format("  %s  %-20s  %s", ins.getAddress(), ins.getBytes().length>0?bytesHex(ins.getBytes()):"", ins.toString()));
                n++;
            }
            DecompileResults dr = di.decompileFunction(f, 15, monitor);
            if (dr != null && dr.decompileCompleted()) {
                String c = dr.getDecompiledFunction().getC();
                for (String line : c.split("\n")) println("  | " + line);
            }
        }
    }
    String bytesHex(byte[] b){ StringBuilder s=new StringBuilder(); for(byte x:b) s.append(String.format("%02x",x&0xff)); return s.toString(); }
}
