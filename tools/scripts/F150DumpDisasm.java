// Dump asm for FUN_101a4d56 + FUN_101a4e4a (patch targets)
// @category Pipeline
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import java.io.*;
import java.nio.file.*;

public class F150DumpDisasm extends GhidraScript {
    @Override
    public void run() throws Exception {
        Path out = Paths.get("/tmp/pscm/f150_lka");
        FunctionManager fm = currentProgram.getFunctionManager();
        AddressFactory af = currentProgram.getAddressFactory();
        Listing L = currentProgram.getListing();
        for (long t : new long[]{0x101a4d56L, 0x101a4e4aL}) {
            Address a = af.getDefaultAddressSpace().getAddress(t);
            Function f = fm.getFunctionAt(a);
            if (f==null) continue;
            StringBuilder sb = new StringBuilder();
            sb.append(String.format("# %s @0x%08x size=%d\n", f.getName(), t, f.getBody().getNumAddresses()));
            InstructionIterator it = L.getInstructions(f.getBody(), true);
            while (it.hasNext()) {
                Instruction ins = it.next();
                byte[] bytes = ins.getBytes();
                StringBuilder hex = new StringBuilder();
                for (byte b : bytes) hex.append(String.format("%02x ", b & 0xFF));
                sb.append(String.format("0x%08x  %-12s  %s\n",
                    ins.getAddress().getOffset(), hex.toString().trim(), ins.toString()));
            }
            Files.writeString(out.resolve(String.format("asm_%08x.txt", t)), sb.toString());
            println("wrote asm for 0x" + Long.toHexString(t));
        }
    }
}
