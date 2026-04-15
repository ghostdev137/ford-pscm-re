// Dump rate-limiter FUN_101a3b84 asm for overflow analysis + scan strategy for init-table markers.
// @category Pipeline
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.mem.*;
import java.io.*;
import java.nio.file.*;

public class F150RateLimitAsm extends GhidraScript {
    @Override
    public void run() throws Exception {
        Path out = Paths.get("/tmp/pscm/f150_lka");
        Listing L = currentProgram.getListing();
        AddressFactory af = currentProgram.getAddressFactory();
        AddressSpace asp = af.getDefaultAddressSpace();
        FunctionManager fm = currentProgram.getFunctionManager();

        // Dump all asm for rate-limiter
        Address a = asp.getAddress(0x101a3b84L);
        Function f = fm.getFunctionAt(a);
        StringBuilder sb = new StringBuilder();
        sb.append(String.format("# FUN_101a3b84 rate-limiter size=%d\n\n", f.getBody().getNumAddresses()));
        InstructionIterator it = L.getInstructions(f.getBody(), true);
        while (it.hasNext()) {
            Instruction ins = it.next();
            byte[] b = ins.getBytes();
            StringBuilder hex = new StringBuilder();
            for (byte x : b) hex.append(String.format("%02x ", x & 0xFF));
            sb.append(String.format("0x%08x  %-18s %s\n",
                ins.getAddress().getOffset(), hex.toString().trim(), ins));
        }
        Files.writeString(out.resolve("asm_101a3b84.txt"), sb.toString());
        println("wrote asm_101a3b84.txt (" + sb.length() + " bytes)");

        // Scan first 2MB of strategy for 0x001000EF init-table markers (big-endian bytes 00 10 00 EF)
        Memory mem = currentProgram.getMemory();
        StringBuilder initR = new StringBuilder("# Init table entries (marker 0x001000EF BE)\n\n");
        long base = 0x10040000L;
        for (long p = base; p < base + 0x1c0000L; p += 4) {
            try {
                Address addr = asp.getAddress(p);
                byte b0 = mem.getByte(addr);
                byte b1 = mem.getByte(addr.add(1));
                byte b2 = mem.getByte(addr.add(2));
                byte b3 = mem.getByte(addr.add(3));
                if (b0==0x00 && b1==0x10 && b2==0x00 && b3==(byte)0xEF) {
                    // Read next 12 bytes
                    long ram_end = 0, ram_start = 0, ctrl = 0;
                    for (int i=0;i<4;i++) ram_end = (ram_end<<8) | (mem.getByte(addr.add(4+i))&0xFF);
                    for (int i=0;i<4;i++) ram_start = (ram_start<<8) | (mem.getByte(addr.add(8+i))&0xFF);
                    for (int i=0;i<4;i++) ctrl = (ctrl<<8) | (mem.getByte(addr.add(12+i))&0xFF);
                    initR.append(String.format("@0x%08x  rs=0x%08x  re=0x%08x  ctrl=0x%08x  op=0x%02x\n",
                        p, ram_start, ram_end, ctrl, (ctrl>>24)&0xFFL));
                }
            } catch (MemoryAccessException e) { }
            if (monitor.isCancelled()) break;
        }
        Files.writeString(out.resolve("init_table.txt"), initR.toString());
        println("wrote init_table.txt");
    }
}
