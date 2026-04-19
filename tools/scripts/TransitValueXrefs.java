// Scan loaded memory for timer-like literal values and report code references.
// @category Probe
// @runtime Java

import java.util.ArrayList;
import java.util.List;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSetView;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.Listing;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;

public class TransitValueXrefs extends GhidraScript {
    private static final int[] VALUES16 = { 0x00ea, 0x02bc, 0x1b58 };
    private static final int[] VALUES32 = { 234, 700, 7000 };

    @Override
    public void run() throws Exception {
        Memory mem = currentProgram.getMemory();
        Listing listing = currentProgram.getListing();

        println("Transit timer-like literal scan");
        println("==============================");

        for (int value : VALUES16) {
            scan16(mem, listing, value);
        }
        for (int value : VALUES32) {
            scan32(mem, listing, value);
        }
    }

    private void scan16(Memory mem, Listing listing, int value) throws Exception {
        List<Address> little = new ArrayList<>();
        List<Address> big = new ArrayList<>();

        for (MemoryBlock block : mem.getBlocks()) {
            if (!block.isInitialized()) {
                continue;
            }
            Address start = block.getStart();
            long size = block.getSize();
            for (long off = 0; off + 1 < size; off++) {
                Address a = start.add(off);
                int b0 = mem.getByte(a) & 0xff;
                int b1 = mem.getByte(a.add(1)) & 0xff;
                int le = b0 | (b1 << 8);
                int be = (b0 << 8) | b1;
                if (le == value) {
                    little.add(a);
                }
                if (be == value) {
                    big.add(a);
                }
            }
        }

        println(String.format("\n16-bit value 0x%04x (%d)", value, value));
        dumpHits("LE", little, listing);
        dumpHits("BE", big, listing);
    }

    private void scan32(Memory mem, Listing listing, int value) throws Exception {
        List<Address> little = new ArrayList<>();
        List<Address> big = new ArrayList<>();

        for (MemoryBlock block : mem.getBlocks()) {
            if (!block.isInitialized()) {
                continue;
            }
            Address start = block.getStart();
            long size = block.getSize();
            for (long off = 0; off + 3 < size; off++) {
                Address a = start.add(off);
                int b0 = mem.getByte(a) & 0xff;
                int b1 = mem.getByte(a.add(1)) & 0xff;
                int b2 = mem.getByte(a.add(2)) & 0xff;
                int b3 = mem.getByte(a.add(3)) & 0xff;
                int le = b0 | (b1 << 8) | (b2 << 16) | (b3 << 24);
                int be = (b0 << 24) | (b1 << 16) | (b2 << 8) | b3;
                if (le == value) {
                    little.add(a);
                }
                if (be == value) {
                    big.add(a);
                }
            }
        }

        println(String.format("\n32-bit value 0x%08x (%d)", value, value));
        dumpHits("LE", little, listing);
        dumpHits("BE", big, listing);
    }

    private void dumpHits(String endian, List<Address> hits, Listing listing) {
        println(String.format("  %s hits: %d", endian, hits.size()));
        int shown = 0;
        for (Address a : hits) {
            if (shown >= 20) {
                break;
            }
            println(String.format("    %s", a));
            dumpRefs(a, listing);
            shown++;
        }
    }

    private void dumpRefs(Address addr, Listing listing) {
        ReferenceIterator refs = currentProgram.getReferenceManager().getReferencesTo(addr);
        int count = 0;
        while (refs.hasNext() && count < 8) {
            Reference ref = refs.next();
            Address from = ref.getFromAddress();
            Function f = listing.getFunctionContaining(from);
            Instruction ins = listing.getInstructionAt(from);
            String fn = f == null ? "(no func)" :
                String.format("%s @ %s", f.getName(), f.getEntryPoint());
            String text = ins == null ? "(no insn)" : ins.toString();
            println(String.format("      <- %s  %s  %s", from, fn, text));
            count++;
        }
    }
}
