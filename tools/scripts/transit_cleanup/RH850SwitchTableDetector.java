// RH850 GHS Switch Table Detector (Java port of rh850_switch_table_detector.py)
// ==============================================================================
// Detects inline jump tables produced by the Ford/GHS compiler targeting
// RH850/V850E2 and marks them as data so the disassembler doesn't walk into
// table entries as if they were instructions.
//
// Handles two table formats:
//   1. 16-bit relative offset tables (sld.hu + jmp[reg] pattern)
//   2. 32-bit absolute address tables
//
// @category Transit
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.program.model.address.*;
import ghidra.program.model.data.*;
import ghidra.program.model.lang.OperandType;
import ghidra.program.model.listing.*;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.scalar.Scalar;
import ghidra.program.model.symbol.RefType;
import ghidra.program.model.symbol.SourceType;

import java.util.ArrayList;
import java.util.List;

public class RH850SwitchTableDetector extends GhidraScript {

    // Tuning
    static final int  MIN_TABLE_ENTRIES = 3;
    static final int  MAX_TABLE_ENTRIES = 512;
    static final long MAX_BRANCH_OFFSET = 0x10000L;
    static final int  ALIGNMENT = 2;
    static final boolean DRY_RUN = false;

    private Listing listing;
    private Memory memory;
    private AddressSpace space;
    private FunctionManager fm;

    int tablesFound = 0;
    int entriesTotal = 0;
    long bytesCleared = 0;

    @Override
    public void run() throws Exception {
        listing = currentProgram.getListing();
        memory  = currentProgram.getMemory();
        space   = currentProgram.getAddressFactory().getDefaultAddressSpace();
        fm      = currentProgram.getFunctionManager();

        Instruction insn = listing.getInstructionAt(currentProgram.getMinAddress());
        if (insn == null) insn = listing.getInstructionAfter(currentProgram.getMinAddress());

        while (insn != null) {
            if (monitor.isCancelled()) break;
            if (isIndirectJump(insn)) {
                try {
                    handleIndirectJump(insn);
                } catch (Exception e) {
                    // continue
                }
            }
            // re-fetch because we may have cleared/created data
            Address next = insn.getMaxAddress().add(1);
            insn = listing.getInstructionAfter(next);
            if (insn == null) break;
        }

        println("============================================================");
        println("RH850 Switch Table Detector — Complete");
        println("  Tables found:   " + tablesFound);
        println("  Total entries:  " + entriesTotal);
        println("  Bytes cleared:  " + bytesCleared);
        if (DRY_RUN) println("  *** DRY RUN — no changes made ***");
        println("============================================================");
    }

    // ---------------- helpers ----------------

    Address addr(long off) { return space.getAddress(off); }

    Integer readU16(Address a) {
        try {
            int b0 = memory.getByte(a) & 0xFF;
            int b1 = memory.getByte(a.add(1)) & 0xFF;
            return b0 | (b1 << 8);
        } catch (Exception e) { return null; }
    }

    Long readU32(Address a) {
        try {
            long b0 = memory.getByte(a) & 0xFF;
            long b1 = memory.getByte(a.add(1)) & 0xFF;
            long b2 = memory.getByte(a.add(2)) & 0xFF;
            long b3 = memory.getByte(a.add(3)) & 0xFF;
            return b0 | (b1 << 8) | (b2 << 16) | (b3 << 24);
        } catch (Exception e) { return null; }
    }

    boolean isExecutable(Address a) {
        var block = memory.getBlock(a);
        return block != null && block.isExecute();
    }

    Address[] getEnclosingFunctionBounds(Address a) {
        Function f = fm.getFunctionContaining(a);
        if (f != null) {
            var body = f.getBody();
            return new Address[]{ body.getMinAddress(), body.getMaxAddress() };
        }
        Function next = null;
        var it = fm.getFunctions(a, true);
        if (it.hasNext()) next = it.next();
        Function prev = null;
        var itb = fm.getFunctions(a, false);
        if (itb.hasNext()) {
            Function f0 = itb.next();
            // f0 may be the function at/after a; skip if so
            if (f0.getEntryPoint().compareTo(a) >= 0 && itb.hasNext()) f0 = itb.next();
            prev = f0;
        }
        Address low;
        try { low = prev != null ? prev.getEntryPoint() : a.subtract(0x10000); }
        catch (Exception e) { low = a; }
        Address high;
        try { high = next != null ? next.getEntryPoint() : a.add(0x10000); }
        catch (Exception e) { high = a; }
        return new Address[]{ low, high };
    }

    boolean isNopPadding(Address a) {
        Integer v = readU16(a);
        return v != null && v == 0x0000;
    }

    boolean isIndirectJump(Instruction insn) {
        if (insn == null) return false;
        String m = insn.getMnemonicString().toLowerCase();
        if (!(m.equals("jmp") || m.equals("switch"))) return false;
        if (insn.getNumOperands() <= 0) return false;
        int type = insn.getOperandType(0);
        boolean hasReg  = (type & OperandType.REGISTER) != 0;
        boolean hasAddr = (type & OperandType.ADDRESS)  != 0;
        if (hasAddr && !hasReg) return false; // direct jump
        return true;
    }

    boolean isBranchHigher(Instruction insn) {
        if (insn == null) return false;
        String m = insn.getMnemonicString().toLowerCase();
        return m.equals("bh") || m.equals("bnh");
    }

    Integer scanBackwardsForBoundsCheck(Instruction insn) {
        Instruction cur = insn;
        for (int i = 0; i < 8; i++) {
            cur = listing.getInstructionBefore(cur.getAddress());
            if (cur == null) break;
            String m = cur.getMnemonicString().toLowerCase();
            if (m.equals("cmp")) {
                Instruction after = listing.getInstructionAfter(cur.getAddress());
                if (after != null && isBranchHigher(after)) {
                    Scalar s = cur.getScalar(0);
                    if (s != null) return (int) s.getValue();
                    return null;
                }
            }
        }
        return null;
    }

    // Result holder
    static class TableResult {
        List<Address[]> entries;   // [entryAddr, target]
        int scale;
        int entrySize;
        TableResult(List<Address[]> e, int s, int es) { entries = e; scale = s; entrySize = es; }
    }

    TableResult tryDetect16(Address tableStart, Address funcLow, Address funcHigh,
                             Address baseAddr, Integer maxCases) {
        TableResult best = null;
        for (int scale : new int[]{2, 1}) {
            List<Address[]> entries = new ArrayList<>();
            for (int i = 0; i < MAX_TABLE_ENTRIES; i++) {
                Address ea;
                try { ea = tableStart.add(i * 2L); } catch (Exception e) { break; }
                if (ea.compareTo(funcHigh) > 0) break;
                Integer v = readU16(ea);
                if (v == null) break;
                long off = (long) v * scale;
                if (off > MAX_BRANCH_OFFSET) break;
                Address target;
                try { target = baseAddr.add(off); } catch (Exception e) { break; }
                if (!isExecutable(target)) break;
                if (target.getOffset() % ALIGNMENT != 0) break;
                if (target.compareTo(funcLow) < 0) break;
                try {
                    if (target.compareTo(funcHigh.add(0x1000)) > 0) break;
                } catch (Exception e) { break; }
                entries.add(new Address[]{ea, target});
                if (maxCases != null && entries.size() >= maxCases + 1) break;
            }
            if (entries.size() >= MIN_TABLE_ENTRIES) {
                if (best == null || entries.size() > best.entries.size()) {
                    best = new TableResult(entries, scale, 2);
                }
            }
        }
        return best;
    }

    TableResult tryDetect32(Address tableStart, Address funcLow, Address funcHigh, Integer maxCases) {
        List<Address[]> entries = new ArrayList<>();
        for (int i = 0; i < MAX_TABLE_ENTRIES; i++) {
            Address ea;
            try { ea = tableStart.add(i * 4L); } catch (Exception e) { break; }
            if (ea.compareTo(funcHigh) > 0) break;
            Long v = readU32(ea);
            if (v == null) break;
            Address target;
            try { target = addr(v); } catch (Exception e) { break; }
            if (!isExecutable(target)) break;
            if (v % ALIGNMENT != 0) break;
            if (target.compareTo(funcLow) < 0) break;
            try {
                if (target.compareTo(funcHigh.add(0x1000)) > 0) break;
            } catch (Exception e) { break; }
            entries.add(new Address[]{ea, target});
            if (maxCases != null && entries.size() >= maxCases + 1) break;
        }
        if (entries.size() >= MIN_TABLE_ENTRIES) return new TableResult(entries, 1, 4);
        return null;
    }

    void handleIndirectJump(Instruction insn) throws Exception {
        Address jmpAddr = insn.getAddress();
        Address jmpEnd  = insn.getMaxAddress().add(1);

        Address[] bounds = getEnclosingFunctionBounds(jmpAddr);
        Address funcLow = bounds[0], funcHigh = bounds[1];

        Address tableStart = jmpEnd;
        if (tableStart.getOffset() % 4 != 0 && isNopPadding(tableStart)) {
            tableStart = tableStart.add(2);
        }

        Integer maxCases = scanBackwardsForBoundsCheck(insn);
        Address baseAddr = jmpEnd;

        TableResult result = tryDetect16(tableStart, funcLow, funcHigh, baseAddr, maxCases);
        if (result == null) {
            Address aligned = tableStart;
            if (aligned.getOffset() % 4 != 0) {
                aligned = aligned.add(4 - (aligned.getOffset() % 4));
            }
            result = tryDetect32(aligned, funcLow, funcHigh, maxCases);
            if (result != null) tableStart = aligned;
        }
        if (result == null) return;

        int count = result.entries.size();
        Address tableEnd = tableStart.add((long) count * result.entrySize);

        if (DRY_RUN) {
            println(String.format("[DRY RUN] Table at %s: %d entries (%d-bit, scale=%d)",
                    tableStart, count, result.entrySize * 8, result.scale));
            return;
        }

        // Clear any instructions in the table range
        Address clearEnd = tableEnd.subtract(1);
        Instruction existing = listing.getInstructionAt(tableStart);
        if (existing == null) existing = listing.getInstructionAfter(tableStart);
        AddressSet cleared = new AddressSet();
        while (existing != null && existing.getAddress().compareTo(clearEnd) <= 0) {
            cleared.add(existing.getAddress(), existing.getMaxAddress());
            Instruction nextI = listing.getInstructionAfter(existing.getMaxAddress());
            try {
                listing.clearCodeUnits(existing.getAddress(), existing.getMaxAddress(), false);
            } catch (Exception e) {}
            existing = nextI;
        }

        DataType dtype = (result.entrySize == 2) ? new WordDataType() : new DWordDataType();
        for (Address[] pair : result.entries) {
            try { listing.createData(pair[0], dtype); } catch (Exception e) {}
            try {
                CodeUnit cu = listing.getCodeUnitAt(pair[0]);
                if (cu != null) cu.addMnemonicReference(pair[1], RefType.COMPUTED_JUMP, SourceType.ANALYSIS);
            } catch (Exception e) {}
        }
        try {
            CodeUnit cu = listing.getCodeUnitAt(tableStart);
            if (cu != null) {
                cu.setComment(CodeUnit.PLATE_COMMENT, String.format(
                        "GHS switch table: %d entries, %d-bit %s (scale=%d)\nDetected by RH850SwitchTableDetector",
                        count, result.entrySize * 8,
                        result.entrySize == 2 ? "relative" : "absolute", result.scale));
            }
        } catch (Exception e) {}

        // Re-disassemble targets
        for (Address[] pair : result.entries) {
            Instruction atTgt = listing.getInstructionAt(pair[1]);
            if (atTgt == null) {
                try {
                    DisassembleCommand cmd = new DisassembleCommand(pair[1], null, true);
                    cmd.applyTo(currentProgram);
                } catch (Exception e) {}
            }
        }

        println(String.format("Table at %s: %d entries (%d-bit, scale=%d)",
                tableStart, count, result.entrySize * 8, result.scale));
        bytesCleared += cleared.getNumAddresses();
        tablesFound++;
        entriesTotal += count;
    }
}
