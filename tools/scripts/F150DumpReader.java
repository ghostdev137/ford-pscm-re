// Dump asm for FUN_100968ea (shared angle reader)
// @category Pipeline
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import java.io.*;
import java.nio.file.*;

public class F150DumpReader extends GhidraScript {
    @Override
    public void run() throws Exception {
        AddressFactory af = currentProgram.getAddressFactory();
        FunctionManager fm = currentProgram.getFunctionManager();
        Listing L = currentProgram.getListing();
        Address a = af.getDefaultAddressSpace().getAddress(0x100968eaL);
        Function f = fm.getFunctionAt(a);
        StringBuilder sb = new StringBuilder();
        InstructionIterator it = L.getInstructions(f.getBody(), true);
        while (it.hasNext()) {
            Instruction ins = it.next();
            byte[] bytes = ins.getBytes();
            StringBuilder hex = new StringBuilder();
            for (byte b : bytes) hex.append(String.format("%02x ", b & 0xFF));
            sb.append(String.format("0x%08x  %-18s %s\n",
                ins.getAddress().getOffset(), hex.toString().trim(), ins));
        }
        Files.writeString(Paths.get("/tmp/pscm/f150_lka/asm_100968ea.txt"), sb.toString());
        println("wrote asm_100968ea.txt");
    }
}
