// Find cal flash offsets for _DAT_fef26405/6 and dump rate-limiter arithmetic context.
// @category Pipeline
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import java.io.*;
import java.nio.file.*;

public class F150CalOffsetsMath extends GhidraScript {
    @Override
    public void run() throws Exception {
        Path out = Paths.get("/tmp/pscm/f150_lka");
        Listing L = currentProgram.getListing();
        AddressFactory af = currentProgram.getAddressFactory();
        FunctionManager fm = currentProgram.getFunctionManager();
        StringBuilder r = new StringBuilder();

        // Dump FUN_101a3b84 (rate-limiter) instructions that reference fef21a6e or fef264xx
        Address a = af.getDefaultAddressSpace().getAddress(0x101a3b84L);
        Function f = fm.getFunctionAt(a);
        if (f == null) { println("no func"); return; }

        r.append(String.format("# FUN_101a3b84 (rate-limiter) size=%d\n",
            f.getBody().getNumAddresses()));

        // Dump asm where immediates look like 0xa6e, 0x6405, 0x6406 (low halfword portions of addresses)
        InstructionIterator it = L.getInstructions(f.getBody(), true);
        r.append("\n## Instructions referencing LKA angle input (fef21a6e) or rate cal (fef26405/6):\n");
        while (it.hasNext()) {
            Instruction ins = it.next();
            String t = ins.toString();
            // look for common offset patterns
            if (t.contains("0x1a6e") || t.contains("0x1a6c") || t.contains("0x1a70") || t.contains("0x1a72")
                || t.contains("0x6405") || t.contains("0x6406") || t.contains("0x640")
                || t.contains("0x101a") || t.contains("-0x10e")) {
                byte[] b = ins.getBytes();
                StringBuilder hex = new StringBuilder();
                for (byte x : b) hex.append(String.format("%02x ", x & 0xFF));
                r.append(String.format("  0x%08x  %-18s %s\n",
                    ins.getAddress().getOffset(), hex.toString().trim(), t));
            }
        }

        // Find the ROM-to-RAM init table: look for the 16-byte entries starting with 0x001000EF marker
        r.append("\n## Init table scan (marker 0x001000EF in strategy for RAM init descriptors):\n");
        Memory mem = currentProgram.getMemory();
        byte[] marker = {(byte)0xEF, 0x00, 0x10, 0x00};  // LE
        byte[] marker_be = {0x00, 0x10, 0x00, (byte)0xEF};  // BE
        Address start = af.getDefaultAddressSpace().getAddress(0x10040000L);
        Address end = af.getDefaultAddressSpace().getAddress(0x101BFC00L);
        // Scan linearly for BE marker
        for (long p = start.getOffset(); p < end.getOffset() - 16; p += 4) {
            try {
                byte[] buf = new byte[16];
                for (int i=0;i<16;i++) buf[i] = mem.getByte(start.getNewAddress(p+i));
                boolean matchBE = buf[0]==0x00 && buf[1]==0x10 && buf[2]==0x00 && buf[3]==(byte)0xEF;
                boolean matchLE = buf[3]==0x00 && buf[2]==0x10 && buf[1]==0x00 && buf[0]==(byte)0xEF;
                if (matchBE) {
                    // Entry: 4 bytes marker, 4 bytes ram_end, 4 bytes ram_start, 4 bytes ctrl
                    long ram_end_be = ((buf[4] & 0xFFL) << 24) | ((buf[5] & 0xFFL) << 16) | ((buf[6] & 0xFFL) << 8) | (buf[7] & 0xFFL);
                    long ram_start_be = ((buf[8] & 0xFFL) << 24) | ((buf[9] & 0xFFL) << 16) | ((buf[10] & 0xFFL) << 8) | (buf[11] & 0xFFL);
                    long ctrl_be = ((buf[12] & 0xFFL) << 24) | ((buf[13] & 0xFFL) << 16) | ((buf[14] & 0xFFL) << 8) | (buf[15] & 0xFFL);
                    r.append(String.format("  @0x%08x  ram_start=0x%08x ram_end=0x%08x ctrl=0x%08x  op=0x%02x\n",
                        p, ram_start_be, ram_end_be, ctrl_be, (ctrl_be>>24)&0xFF));
                    // Only print first 30
                    if (r.length() > 20000) break;
                }
            } catch (MemoryAccessException e) {}
        }

        Files.writeString(out.resolve("_rate_cal.txt"), r.toString());
        println("wrote _rate_cal.txt");
    }
}
