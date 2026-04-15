# RH850 GHS Switch Table Detector for Ghidra
# ===========================================
# Detects inline jump tables produced by Green Hills Software compiler
# targeting RH850/V850E2 and marks them as data so the disassembler
# doesn't misinterpret table entries as instructions.
#
# Handles two table formats:
#   1. 16-bit relative offset tables (sld.hu pattern — most common on RH850 G3KH)
#   2. 32-bit absolute address tables (jmp [reg] with full pointer entries)
#
# RUNTIME: Ghidra 12 dropped Jython. Run via PyGhidra:
#   ghidra has builtin PyGhidra since 11.2; invoke via Script Manager with
#   a .py file using the PyGhidra interpreter, OR via headless:
#     analyzeHeadless <project> <name> -process <program>
#       -scriptPath <dir> -postScript rh850_switch_table_detector.py
#   If PyGhidra isn't available, this file should be ported to Java
#   (straight-line translation; Ghidra's Java API is already used here).
#
# @category V850
# @author Claude / Ross

from ghidra.program.model.data import WordDataType, DWordDataType, PointerDataType
from ghidra.program.model.symbol import RefType, SourceType
from ghidra.program.model.listing import CodeUnit
from ghidra.program.model.address import AddressSet
from ghidra.app.cmd.disassemble import DisassembleCommand
import struct

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MIN_TABLE_ENTRIES   = 3       # Minimum entries to consider it a real table
MAX_TABLE_ENTRIES   = 512     # Sanity cap — no switch has 512 cases
MAX_BRANCH_OFFSET   = 0x10000 # 64 KiB — max reasonable relative offset
ALIGNMENT           = 2       # RH850 minimum instruction alignment (halfword)
DRY_RUN             = False   # Set True to preview without modifying the program

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

listing = currentProgram.getListing()
memory  = currentProgram.getMemory()
space   = currentProgram.getAddressFactory().getDefaultAddressSpace()
fm      = currentProgram.getFunctionManager()

def addr(offset):
    """Create an Address from a numeric offset."""
    return space.getAddress(offset)

def read_u16(address):
    """Read unsigned 16-bit little-endian value at address."""
    try:
        b0 = memory.getByte(address) & 0xFF
        b1 = memory.getByte(address.add(1)) & 0xFF
        return b0 | (b1 << 8)
    except:
        return None

def read_u32(address):
    """Read unsigned 32-bit little-endian value at address."""
    try:
        b0 = memory.getByte(address) & 0xFF
        b1 = memory.getByte(address.add(1)) & 0xFF
        b2 = memory.getByte(address.add(2)) & 0xFF
        b3 = memory.getByte(address.add(3)) & 0xFF
        return b0 | (b1 << 8) | (b2 << 16) | (b3 << 24)
    except:
        return None

def is_executable(address):
    """Check if address falls in an executable memory block."""
    block = memory.getBlock(address)
    return block is not None and block.isExecute()

def get_enclosing_function_bounds(address):
    """
    Get (start, end) of the enclosing function, or a conservative estimate
    based on neighboring seeded function starts.
    """
    func = fm.getFunctionContaining(address)
    if func is not None:
        body = func.getBody()
        return (body.getMinAddress(), body.getMaxAddress())

    prev_func = fm.getFunctionBefore(address)
    next_func = fm.getFunctionAfter(address)

    low = prev_func.getEntryPoint() if prev_func else address.subtract(0x10000)
    high = next_func.getEntryPoint() if next_func else address.add(0x10000)

    return (low, high)

def is_nop_padding(address):
    """Check if address contains NOP padding (0x0000)."""
    val = read_u16(address)
    return val == 0x0000

def is_indirect_jump(insn):
    """
    Check if an instruction is an indirect jump (jmp [reg]).
    On RH850, this is typically:
      jmp [rN]         — opcode varies by register
      switch rN        — dedicated switch instruction on some RH850 variants
    """
    if insn is None:
        return False
    mnemonic = insn.getMnemonicString().lower()
    if mnemonic in ("jmp", "switch"):
        num_ops = insn.getNumOperands()
        if num_ops > 0:
            op_type = insn.getOperandType(0)
            # Constants from ghidra.program.model.lang.OperandType
            OP_REG  = 0x200     # REGISTER
            OP_ADDR = 0x2000    # ADDRESS
            # Direct jump to address => not a table dispatch
            if (op_type & OP_ADDR) != 0 and (op_type & OP_REG) == 0:
                return False
            return True
    return False

def is_branch_higher(insn):
    """Check if instruction is a 'bh' (branch if higher, unsigned) — the GHS bounds check."""
    if insn is None:
        return False
    mnemonic = insn.getMnemonicString().lower()
    return mnemonic in ("bh", "bnh")

def scan_backwards_for_bounds_check(insn, max_lookback=8):
    """
    Walk backwards from the indirect jump looking for the cmp+bh pattern
    that indicates a switch bounds check. Returns the max case value if found.
    """
    current = insn
    for i in range(max_lookback):
        current = listing.getInstructionBefore(current.getAddress())
        if current is None:
            break
        mnemonic = current.getMnemonicString().lower()
        if mnemonic == "cmp":
            check = listing.getInstructionAfter(current.getAddress())
            if check is not None and is_branch_higher(check):
                try:
                    scalar = current.getScalar(0)
                    if scalar is not None:
                        return int(scalar.getValue())
                except:
                    pass
                return None
    return None

# ---------------------------------------------------------------------------
# Core: Try to detect a jump table starting at a given address
# ---------------------------------------------------------------------------

def try_detect_table_16bit(table_start, func_low, func_high, base_addr, max_cases=None):
    """
    Try to interpret bytes at table_start as a 16-bit relative offset table.
    base_addr is typically the address of the instruction after the jmp.
    """
    results = []

    for scale in (2, 1):
        entries = []
        for i in range(MAX_TABLE_ENTRIES):
            entry_addr = table_start.add(i * 2)
            if entry_addr.compareTo(func_high) > 0:
                break
            val = read_u16(entry_addr)
            if val is None:
                break
            target_offset = val * scale
            if target_offset > MAX_BRANCH_OFFSET:
                break
            try:
                target = base_addr.add(target_offset)
            except:
                break
            if not is_executable(target):
                break
            if target.getOffset() % ALIGNMENT != 0:
                break
            if target.compareTo(func_low) < 0:
                break
            if target.compareTo(func_high.add(0x1000)) > 0:
                break
            entries.append((entry_addr, target))
            if max_cases is not None and len(entries) >= max_cases + 1:
                break

        if len(entries) >= MIN_TABLE_ENTRIES:
            results.append((entries, scale, 2))

    if results:
        results.sort(key=lambda x: len(x[0]), reverse=True)
        return results[0]
    return None

def try_detect_table_32bit(table_start, func_low, func_high, max_cases=None):
    """
    Try to interpret bytes at table_start as a 32-bit absolute address table.
    """
    entries = []
    for i in range(MAX_TABLE_ENTRIES):
        entry_addr = table_start.add(i * 4)
        if entry_addr.compareTo(func_high) > 0:
            break
        val = read_u32(entry_addr)
        if val is None:
            break
        try:
            target = addr(val)
        except:
            break
        if not is_executable(target):
            break
        if val % ALIGNMENT != 0:
            break
        if target.compareTo(func_low) < 0:
            break
        if target.compareTo(func_high.add(0x1000)) > 0:
            break
        entries.append((entry_addr, target))
        if max_cases is not None and len(entries) >= max_cases + 1:
            break

    if len(entries) >= MIN_TABLE_ENTRIES:
        return (entries, 1, 4)
    return None

# ---------------------------------------------------------------------------
# Main scan
# ---------------------------------------------------------------------------

def run():
    tables_found = 0
    entries_total = 0
    bytes_cleared = 0

    insn = listing.getInstructionAt(currentProgram.getMinAddress())
    if insn is None:
        insn = listing.getInstructionAfter(currentProgram.getMinAddress())

    while insn is not None:
        if is_indirect_jump(insn):
            jmp_addr = insn.getAddress()
            jmp_end = insn.getMaxAddress().add(1)

            func_low, func_high = get_enclosing_function_bounds(jmp_addr)

            table_start = jmp_end
            if table_start.getOffset() % 4 != 0 and is_nop_padding(table_start):
                table_start = table_start.add(2)

            max_cases = scan_backwards_for_bounds_check(insn)
            base_addr = jmp_end

            result = try_detect_table_16bit(table_start, func_low, func_high, base_addr, max_cases)

            if result is None:
                aligned_start = table_start
                if aligned_start.getOffset() % 4 != 0:
                    pad = 4 - (aligned_start.getOffset() % 4)
                    aligned_start = aligned_start.add(pad)
                result = try_detect_table_32bit(aligned_start, func_low, func_high, max_cases)
                if result is not None:
                    table_start = aligned_start

            if result is not None:
                entries, scale, entry_size = result
                count = len(entries)
                table_end = table_start.add(count * entry_size)

                if DRY_RUN:
                    print("[DRY RUN] Table at %s: %d entries (%d-bit, scale=%d)" % (
                        table_start, count, entry_size * 8, scale))
                    for ea, target in entries:
                        print("  %s -> %s" % (ea, target))
                else:
                    clear_start = table_start
                    clear_end = table_end.subtract(1)
                    existing = listing.getInstructionAt(clear_start)
                    if existing is None:
                        existing = listing.getInstructionAfter(clear_start)

                    cleared = AddressSet()
                    while existing is not None and existing.getAddress().compareTo(clear_end) <= 0:
                        cleared.add(existing.getAddress(), existing.getMaxAddress())
                        next_insn = listing.getInstructionAfter(existing.getMaxAddress())
                        listing.clearCodeUnits(existing.getAddress(), existing.getMaxAddress(), False)
                        existing = next_insn

                    dtype = WordDataType() if entry_size == 2 else DWordDataType()
                    for ea, target in entries:
                        try:
                            listing.createData(ea, dtype)
                        except:
                            pass
                        try:
                            cu = listing.getCodeUnitAt(ea)
                            if cu is not None:
                                cu.addMnemonicReference(target, RefType.COMPUTED_JUMP, SourceType.ANALYSIS)
                        except:
                            pass

                    try:
                        cu = listing.getCodeUnitAt(table_start)
                        if cu is not None:
                            cu.setComment(CodeUnit.PLATE_COMMENT,
                                "GHS switch table: %d entries, %d-bit %s (scale=%d)\nDetected by rh850_switch_table_detector.py" % (
                                    count, entry_size * 8,
                                    "relative" if entry_size == 2 else "absolute",
                                    scale))
                    except:
                        pass

                    for ea, target in entries:
                        existing_insn = listing.getInstructionAt(target)
                        if existing_insn is None:
                            try:
                                cmd = DisassembleCommand(target, None, True)
                                cmd.applyTo(currentProgram)
                            except:
                                pass

                    print("Table at %s: %d entries (%d-bit, scale=%d)" % (
                        table_start, count, entry_size * 8, scale))
                    bytes_cleared += cleared.getNumAddresses()

                tables_found += 1
                entries_total += count

        insn = listing.getInstructionAfter(insn.getMaxAddress())

    print("=" * 60)
    print("RH850 Switch Table Detector — Complete")
    print("  Tables found:   %d" % tables_found)
    print("  Total entries:  %d" % entries_total)
    print("  Bytes cleared:  %d (mis-disassembled insns removed)" % bytes_cleared)
    if DRY_RUN:
        print("  *** DRY RUN — no changes made ***")
    print("=" * 60)

run()
