// Dump raw bytes + disassembly at the F150 APA lockout patch sites.
// @category Pipeline
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.mem.Memory;
import java.nio.file.*;

public class F150DumpPatchBytes extends GhidraScript {
    @Override
    public void run() throws Exception {
        StringBuilder sb = new StringBuilder();
        Listing L = currentProgram.getListing();
        Memory mem = currentProgram.getMemory();
        long[] addrs = { 0x100a7852L, 0x100a7854L, 0x100a7858L, 0x100a785aL, 0x100a785cL, 0x100a785eL, 0x100a7864L };
        for (long la : addrs) {
            Address a = toAddr(la);
            Instruction ins = L.getInstructionAt(a);
            int len = ins == null ? 4 : ins.getLength();
            byte[] buf = new byte[len];
            mem.getBytes(a, buf);
            StringBuilder hex = new StringBuilder();
            for (byte b : buf) hex.append(String.format("%02x ", b & 0xff));
            sb.append(String.format("%08x  %-14s  %s\n", la, hex.toString().trim(), ins==null?"(no insn)":ins.toString()));
        }
        Files.writeString(Paths.get("/tmp/pscm/f150_apa/_patch_bytes.txt"), sb.toString());
        println("wrote _patch_bytes.txt");
    }
}
