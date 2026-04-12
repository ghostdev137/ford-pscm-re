#!/usr/bin/env python3
"""
V850 Recursive Descent Control Flow Tracer for Ford PSCM Firmware.

Since Unicorn Engine 2.1.4 does not include V850/RH850 support,
this implements a static recursive-descent control flow analysis
using our existing V850 decoder to build a ground-truth code map.

Approach:
  1. Load all firmware blocks into a unified memory model
  2. Discover entry points (PREPARE prologues, JARL targets, vector table)
  3. Follow control flow: decode each instruction, track branches/calls
  4. For conditional branches: add BOTH targets to the worklist
  5. For JARL: add call target as new function entry
  6. For JMP [reg]: stop (can't resolve statically)
  7. Output: set of all addresses that are definitively code

This solves code/data separation completely for reachable code.
"""

import struct
import sys
import os
import time
from collections import defaultdict

# Add tools dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v850.decoder import V850Decoder
from v850.models import sign_extend

BINS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'bins')
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'output')


class MemoryMap:
    """Unified memory model mapping address ranges to firmware blocks."""

    def __init__(self):
        self.regions = []  # list of (start, end, data, name)

    def add(self, start, data, name):
        end = start + len(data)
        self.regions.append((start, end, data, name))
        print(f"  Loaded {name}: {start:#010x} - {end:#010x} ({len(data):,} bytes)")

    def read(self, addr, size):
        """Read bytes from the memory map. Returns None if unmapped."""
        for start, end, data, name in self.regions:
            if start <= addr < end:
                offset = addr - start
                available = min(size, end - addr)
                if available < size:
                    return None
                return data[offset:offset + size]
        return None

    def read_u16(self, addr):
        b = self.read(addr, 2)
        if b is None:
            return None
        return struct.unpack_from('<H', b)[0]

    def read_u32(self, addr):
        b = self.read(addr, 4)
        if b is None:
            return None
        return struct.unpack_from('<I', b)[0]

    def is_mapped(self, addr):
        for start, end, data, name in self.regions:
            if start <= addr < end:
                return True
        return False

    def get_region(self, addr):
        for start, end, data, name in self.regions:
            if start <= addr < end:
                return name
        return None

    def get_block_data(self, addr):
        """Get (data, base_addr, name) for the block containing addr."""
        for start, end, data, name in self.regions:
            if start <= addr < end:
                return data, start, name
        return None, None, None


class ControlFlowTracer:
    """Recursive descent control flow tracer for V850 firmware."""

    def __init__(self, mem):
        self.mem = mem
        self.decoder = V850Decoder()

        # Analysis results
        self.code_addrs = set()           # All addresses confirmed as code
        self.function_entries = set()      # Addresses that are function entry points
        self.call_targets = set()          # All JARL/call target addresses
        self.branch_targets = set()        # All branch target addresses
        self.indirect_jumps = []           # Addresses with JMP [reg] (unresolvable)
        self.unmapped_refs = set()         # References to unmapped memory
        self.instruction_count = 0         # Total instructions decoded
        self.worklist = []                 # Addresses to explore
        self.explored = set()             # Addresses already processed as block starts
        self.errors = []                   # Decode errors

    def add_entry(self, addr, reason=""):
        """Add an address to the exploration worklist."""
        if addr not in self.explored and self.mem.is_mapped(addr):
            self.worklist.append(addr)
            self.function_entries.add(addr)
            if reason:
                pass  # Could log reason

    def trace_block(self, start_addr):
        """Trace a single basic block starting at start_addr.

        Follows linear execution until hitting a terminator:
        - Unconditional branch (JR, JMP [reg])
        - Return (JMP [lp], DISPOSE [lp])
        - Invalid/unmapped instruction
        - Address already traced (loop back)
        """
        addr = start_addr
        max_insns = 50000  # safety limit per block
        consecutive_nops = 0
        MAX_CONSECUTIVE_NOPS = 4  # Stop after 4 consecutive NOPs (likely data)

        for _ in range(max_insns):
            if addr in self.code_addrs:
                # Already traced this address - we've merged into known code
                break

            # Read instruction bytes
            data, base, name = self.mem.get_block_data(addr)
            if data is None:
                self.unmapped_refs.add(addr)
                break

            offset = addr - base
            insn = self.decoder.decode(data, offset, base)

            if insn is None:
                self.errors.append((addr, "decode_failed"))
                break

            # Skip padding
            if insn.mnemonic == '.fill':
                break

            if insn.mnemonic == '.dw':
                self.errors.append((addr, f"unknown_encoding_{insn.op_str}"))
                break

            # Detect NOP sleds (likely zero-filled data regions)
            if insn.mnemonic == 'nop':
                consecutive_nops += 1
                if consecutive_nops >= MAX_CONSECUTIVE_NOPS:
                    # Remove the NOPs we already marked as code
                    nop_start = addr - (consecutive_nops - 1) * 2
                    for nop_addr in range(nop_start, addr + 2):
                        self.code_addrs.discard(nop_addr)
                    self.instruction_count -= consecutive_nops
                    break
            else:
                consecutive_nops = 0

            # Mark all bytes of this instruction as code
            for b in range(addr, addr + insn.size):
                self.code_addrs.add(b)
            self.instruction_count += 1

            # Process control flow
            if insn.is_return:
                # End of function - stop tracing
                break

            if insn.mnemonic == 'halt':
                break

            if insn.mnemonic in ('reti', 'ctret'):
                break

            if insn.is_call and insn.branch_target is not None:
                # JARL - function call. Add target as new entry point.
                self.call_targets.add(insn.branch_target)
                if self.mem.is_mapped(insn.branch_target):
                    self.add_entry(insn.branch_target, f"call_from_{addr:#010x}")
                else:
                    self.unmapped_refs.add(insn.branch_target)
                # Execution continues after the call
                addr += insn.size
                continue

            if insn.is_branch:
                if insn.branch_target is not None:
                    self.branch_targets.add(insn.branch_target)

                    if insn.mnemonic in ('jr',):
                        # Unconditional jump - follow it
                        if self.mem.is_mapped(insn.branch_target):
                            addr = insn.branch_target
                            continue
                        else:
                            self.unmapped_refs.add(insn.branch_target)
                            break
                    elif insn.mnemonic.startswith('b'):
                        # Conditional branch - add both paths
                        # Fall-through:
                        fall_through = addr + insn.size
                        # Branch target:
                        if self.mem.is_mapped(insn.branch_target):
                            if insn.branch_target not in self.explored:
                                self.worklist.append(insn.branch_target)
                        else:
                            self.unmapped_refs.add(insn.branch_target)
                        # Continue with fall-through
                        addr = fall_through
                        continue
                else:
                    # JMP [reg] - can't resolve statically
                    self.indirect_jumps.append((addr, insn.op_str))
                    break

            if insn.mnemonic == 'switch':
                # SWITCH instruction - can't easily resolve table
                self.indirect_jumps.append((addr, f"switch {insn.op_str}"))
                break

            # Regular instruction - continue to next
            addr += insn.size

    def run(self):
        """Run the full recursive descent analysis."""
        print(f"\nStarting recursive descent with {len(self.worklist)} entry points...")

        iterations = 0
        while self.worklist:
            addr = self.worklist.pop()
            if addr in self.explored:
                continue
            self.explored.add(addr)
            self.trace_block(addr)
            iterations += 1

            if iterations % 500 == 0:
                print(f"  ... {iterations} blocks traced, "
                      f"{len(self.code_addrs)} code bytes, "
                      f"{len(self.worklist)} remaining")

        print(f"  Done: {iterations} blocks traced")

    def get_code_regions(self):
        """Group code addresses into contiguous regions."""
        if not self.code_addrs:
            return []

        sorted_addrs = sorted(self.code_addrs)
        regions = []
        region_start = sorted_addrs[0]
        prev = sorted_addrs[0]

        for addr in sorted_addrs[1:]:
            if addr != prev + 1:
                regions.append((region_start, prev + 1))
                region_start = addr
            prev = addr
        regions.append((region_start, prev + 1))

        return regions


def find_entry_points_from_jarls(mem, block_name, base_addr, data):
    """Find JARL targets within a block as entry points."""
    entries = set()
    end_addr = base_addr + len(data)

    for off in range(0, len(data) - 3, 2):
        hw0 = struct.unpack_from('<H', data, off)[0]

        # 32-bit JARL: (hw0 & 0x07C0) == 0x0780, reg2 != 0, hw1 bit0 == 0
        # Must exclude PREPARE: (hw0 & 0xFFE0) == 0x0780
        if (hw0 & 0x07C0) == 0x0780 and (hw0 & 0xFFE0) != 0x0780:
            if off + 4 <= len(data):
                hw1 = struct.unpack_from('<H', data, off + 2)[0]
                reg2 = (hw0 >> 11) & 0x1F
                if reg2 != 0 and (hw1 & 1) == 0:
                    raw22 = ((hw0 & 0x3F) << 16) | (hw1 & 0xFFFE)
                    if raw22 & 0x200000:
                        raw22 -= 0x400000
                    target = (base_addr + off + raw22) & 0xFFFFFFFF
                    if mem.is_mapped(target):
                        entries.add(target)

        # 48-bit JARL: (hw0 & 0xFFE0) == 0x02E0, reg1 != 0
        if (hw0 & 0xFFE0) == 0x02E0:
            reg1 = hw0 & 0x1F
            if reg1 != 0 and off + 6 <= len(data):
                hw1 = struct.unpack_from('<H', data, off + 2)[0]
                hw2 = struct.unpack_from('<H', data, off + 4)[0]
                disp32 = (hw2 << 16) | hw1
                if disp32 & 0x80000000:
                    disp32 -= 0x100000000
                target = (base_addr + off + disp32) & 0xFFFFFFFF
                if mem.is_mapped(target):
                    entries.add(target)

    return entries


def find_prepare_entries(data, base_addr):
    """Find PREPARE instructions as function prologues."""
    entries = set()
    for off in range(0, len(data) - 3, 2):
        hw0 = struct.unpack_from('<H', data, off)[0]
        if (hw0 & 0xFFE0) == 0x0780:
            entries.add(base_addr + off)
    return entries


def find_bcc_targets(data, base_addr, mem):
    """Find branch targets from Bcc instructions."""
    targets = set()
    for off in range(0, len(data) - 1, 2):
        hw = struct.unpack_from('<H', data, off)[0]
        if (hw & 0x0780) == 0x0580:
            cccc = hw & 0xF
            d_hi = (hw >> 11) & 0x1F
            d_lo = (hw >> 4) & 0x7
            disp9 = (d_hi << 4) | (d_lo << 1)
            sdisp = sign_extend(disp9, 9)
            target = (base_addr + off + sdisp) & 0xFFFFFFFF
            if mem.is_mapped(target):
                targets.add(target)
    return targets


def main():
    print("=" * 72)
    print("V850 PSCM Firmware Control Flow Tracer")
    print("=" * 72)

    # ---- Load firmware blocks ----
    print("\nLoading firmware blocks...")
    mem = MemoryMap()

    blocks = [
        ('transit_sbl.bin',            0x00000000, 'SBL/vectors'),
        ('transit_calibration_AH.bin', 0x00FD0000, 'calibration'),
        ('transit_strategy_AM.bin',    0x01000000, 'strategy'),
        ('transit_block1_ram.bin',     0x10000400, 'RAM_init'),
        ('transit_block2_ext.bin',     0x20FF0000, 'EPS_code'),
    ]

    loaded_blocks = {}
    for fname, base, name in blocks:
        path = os.path.join(BINS_DIR, fname)
        if os.path.exists(path):
            data = open(path, 'rb').read()
            mem.add(base, data, name)
            loaded_blocks[name] = (base, data)
        else:
            print(f"  WARNING: {fname} not found")

    # ---- Iterative entry point discovery ----
    # Phase 1: Seed from PREPARE prologues only (highest confidence)
    # Phase 2: Find JARL targets WITHIN confirmed code and add them
    # Phase 3: Repeat until no new code is found
    t0 = time.time()
    print("\nPhase 1: Seeding from PREPARE prologues...")
    tracer = ControlFlowTracer(mem)

    total_entries = 0

    # PREPARE prologues (highest confidence function entry points)
    for name, (base, data) in loaded_blocks.items():
        prep_entries = find_prepare_entries(data, base)
        for e in prep_entries:
            tracer.add_entry(e, f"prepare_in_{name}")
        if prep_entries:
            print(f"  {name}: {len(prep_entries)} PREPARE prologues")
            total_entries += len(prep_entries)

    # Vector table entries from SBL
    if 'SBL/vectors' in loaded_blocks:
        base, data = loaded_blocks['SBL/vectors']
        print("  SBL vector table:")
        for i in range(0, min(0x14, len(data)), 4):
            vec = struct.unpack_from('<I', data, i)[0]
            if vec != 0xFFFFFFFF and mem.is_mapped(vec):
                tracer.add_entry(vec, f"vector_{i//4}")
                total_entries += 1
                print(f"    Vector {i//4}: {vec:#010x}")
            elif vec != 0xFFFFFFFF:
                print(f"    Vector {i//4}: {vec:#010x} (unmapped)")

    # Also add block2 start
    if 'EPS_code' in loaded_blocks:
        base, data = loaded_blocks['EPS_code']
        tracer.add_entry(base, "block2_start")
        total_entries += 1

    # Phase 1b: Add JARL targets from full binary scan, but validate each
    # target starts with a plausible function prologue pattern
    print("\n  Adding validated JARL targets from binary scan...")
    jarl_scan_count = 0
    for name, (base, data) in loaded_blocks.items():
        jarl_entries = find_entry_points_from_jarls(mem, name, base, data)
        for target in jarl_entries:
            # Validate: check if target looks like a function start
            target_data, target_base, _ = mem.get_block_data(target)
            if target_data is None:
                continue
            toff = target - target_base
            if toff + 4 > len(target_data):
                continue
            hw0 = struct.unpack_from('<H', target_data, toff)[0]
            # Accept if target starts with a PREPARE prologue (strongest signal)
            # or a JARL to another function (trampoline)
            # We're strict here to avoid data-as-code false positives
            opcode6 = (hw0 >> 5) & 0x3F
            is_prepare = (hw0 & 0xFFE0) == 0x0780
            # JR trampoline (tail call)
            is_jr = ((hw0 & 0x07C0) == 0x0780 and (hw0 >> 11) & 0x1F == 0
                     and (hw0 & 0xFFE0) != 0x0780)
            # JARL (call trampoline)
            is_jarl = ((hw0 & 0x07C0) == 0x0780 and (hw0 >> 11) & 0x1F != 0
                       and (hw0 & 0xFFE0) != 0x0780)
            # DI/EI (interrupt handler entry)
            is_di_ei = (hw0 == 0x07E0 or hw0 == 0x87E0)
            # STSR (common in interrupt handlers)
            is_stsr = (opcode6 == 0x3F and toff + 4 <= len(target_data)
                       and (struct.unpack_from('<H', target_data, toff + 2)[0] >> 5) & 0x3F == 0x02)
            if is_prepare or is_jr or is_jarl or is_di_ei or is_stsr:
                tracer.add_entry(target, f"jarl_scan_{name}")
                jarl_scan_count += 1

    print(f"  Validated JARL targets: {jarl_scan_count}")
    total_entries += jarl_scan_count

    print(f"  Phase 1 total seeds: {total_entries}")

    # Run initial trace
    tracer.run()

    # Phase 2: Iterative refinement - find JARL/JR targets within confirmed code
    iteration = 0
    while True:
        iteration += 1
        new_entries = 0

        # Scan confirmed code regions for JARL/JR instructions
        code_regions = tracer.get_code_regions()
        for region_start, region_end in code_regions:
            block_data, block_base, block_name = mem.get_block_data(region_start)
            if block_data is None:
                continue

            # Scan this code region for JARL and JR
            for addr in range(region_start, region_end - 3, 2):
                offset = addr - block_base
                if offset + 4 > len(block_data):
                    break
                hw0 = struct.unpack_from('<H', block_data, offset)[0]

                # 32-bit JARL: (hw0 & 0x07C0) == 0x0780, reg2 != 0, not PREPARE
                if (hw0 & 0x07C0) == 0x0780 and (hw0 & 0xFFE0) != 0x0780:
                    hw1 = struct.unpack_from('<H', block_data, offset + 2)[0]
                    reg2 = (hw0 >> 11) & 0x1F
                    if reg2 != 0 and (hw1 & 1) == 0:
                        raw22 = ((hw0 & 0x3F) << 16) | (hw1 & 0xFFFE)
                        if raw22 & 0x200000:
                            raw22 -= 0x400000
                        target = (addr + raw22) & 0xFFFFFFFF
                        if mem.is_mapped(target) and target not in tracer.explored:
                            tracer.add_entry(target, f"jarl_from_code_iter{iteration}")
                            new_entries += 1

                # 48-bit JARL: (hw0 & 0xFFE0) == 0x02E0, reg1 != 0
                if (hw0 & 0xFFE0) == 0x02E0 and (hw0 & 0x1F) != 0:
                    if offset + 6 <= len(block_data):
                        hw1 = struct.unpack_from('<H', block_data, offset + 2)[0]
                        hw2 = struct.unpack_from('<H', block_data, offset + 4)[0]
                        disp32 = (hw2 << 16) | hw1
                        if disp32 & 0x80000000:
                            disp32 -= 0x100000000
                        target = (addr + disp32) & 0xFFFFFFFF
                        if mem.is_mapped(target) and target not in tracer.explored:
                            tracer.add_entry(target, f"jarl48_from_code_iter{iteration}")
                            new_entries += 1

        if new_entries == 0:
            print(f"\n  Phase 2 converged after {iteration} iterations")
            break

        print(f"\n  Phase 2, iteration {iteration}: {new_entries} new JARL targets from confirmed code")
        tracer.run()

    # Optional: Bcc seeding (disabled by default due to false positives)
    use_bcc_seeds = '--bcc-seeds' in sys.argv
    if use_bcc_seeds:
        bcc_targets_total = 0
        for name, (base_addr, data) in loaded_blocks.items():
            bcc_targets = find_bcc_targets(data, base_addr, mem)
            for t in bcc_targets:
                if t not in tracer.explored:
                    tracer.worklist.append(t)
            bcc_targets_total += len(bcc_targets)
        print(f"\n  Bcc seeding: {bcc_targets_total} branch targets added")
        tracer.run()
    else:
        print("  Bcc seeding: DISABLED (use --bcc-seeds to enable)")

    elapsed = time.time() - t0

    # ---- Report results ----
    print("\n" + "=" * 72)
    print("RESULTS")
    print("=" * 72)

    print(f"\nExecution time: {elapsed:.2f}s")
    print(f"Instructions decoded: {tracer.instruction_count:,}")
    print(f"Code bytes (unique addresses): {len(tracer.code_addrs):,}")
    print(f"Function entry points found: {len(tracer.function_entries):,}")
    print(f"Call targets (JARL): {len(tracer.call_targets):,}")
    print(f"Branch targets (Bcc/JR): {len(tracer.branch_targets):,}")
    print(f"Indirect jumps (unresolvable): {len(tracer.indirect_jumps)}")
    print(f"References to unmapped memory: {len(tracer.unmapped_refs):,}")
    print(f"Decode errors: {len(tracer.errors)}")

    # Code regions
    regions = tracer.get_code_regions()
    print(f"\nCode regions: {len(regions)}")

    # Group by firmware block
    region_by_block = defaultdict(list)
    for start, end in regions:
        block_name = mem.get_region(start) or "unknown"
        region_by_block[block_name].append((start, end))

    for block_name in sorted(region_by_block.keys()):
        block_regions = region_by_block[block_name]
        total_bytes = sum(e - s for s, e in block_regions)
        print(f"\n  [{block_name}] {len(block_regions)} regions, {total_bytes:,} code bytes")
        # Show top regions by size
        by_size = sorted(block_regions, key=lambda r: r[1] - r[0], reverse=True)
        for start, end in by_size[:15]:
            size = end - start
            print(f"    {start:#010x} - {end:#010x}  ({size:>6,} bytes)")
        if len(by_size) > 15:
            print(f"    ... and {len(by_size) - 15} more regions")

    # Indirect jumps (these are switch/vtable dispatch points)
    if tracer.indirect_jumps:
        print(f"\nIndirect jumps (need manual analysis):")
        for addr, info in tracer.indirect_jumps[:30]:
            region = mem.get_region(addr) or "?"
            print(f"  {addr:#010x} ({region}): {info}")
        if len(tracer.indirect_jumps) > 30:
            print(f"  ... and {len(tracer.indirect_jumps) - 30} more")

    # Unmapped references (top by frequency region)
    if tracer.unmapped_refs:
        # Group by high nibble
        ref_groups = defaultdict(int)
        for r in tracer.unmapped_refs:
            ref_groups[r >> 24] += 1
        print(f"\nUnmapped references by address range:")
        for hi, count in sorted(ref_groups.items(), key=lambda x: -x[1])[:10]:
            print(f"  {hi:02X}xxxxxx: {count:,} references")

    # Errors
    if tracer.errors:
        print(f"\nDecode errors (first 20):")
        for addr, reason in tracer.errors[:20]:
            region = mem.get_region(addr) or "?"
            print(f"  {addr:#010x} ({region}): {reason}")

    # ---- Write output files ----
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Code coverage: all executed addresses
    coverage_file = os.path.join(OUTPUT_DIR, 'code_coverage.txt')
    with open(coverage_file, 'w') as f:
        f.write(f"# V850 PSCM Code Coverage Map\n")
        f.write(f"# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Total code bytes: {len(tracer.code_addrs):,}\n")
        f.write(f"# Total instructions: {tracer.instruction_count:,}\n")
        f.write(f"# Total regions: {len(regions)}\n")
        f.write(f"# Function entries: {len(tracer.function_entries):,}\n")
        f.write(f"#\n")
        f.write(f"# Format: start_addr end_addr size_bytes block_name\n\n")

        for start, end in sorted(regions):
            block = mem.get_region(start) or "unknown"
            f.write(f"{start:#010x} {end:#010x} {end - start:>8d} {block}\n")

    print(f"\nWrote code regions to: {coverage_file}")

    # Function entries
    func_file = os.path.join(OUTPUT_DIR, 'function_entries.txt')
    with open(func_file, 'w') as f:
        f.write(f"# Function entry points discovered by control flow analysis\n")
        f.write(f"# Total: {len(tracer.function_entries):,}\n\n")
        for addr in sorted(tracer.function_entries):
            block = mem.get_region(addr) or "unmapped"
            f.write(f"{addr:#010x} {block}\n")
    print(f"Wrote function entries to: {func_file}")

    # Full instruction-level coverage for Ghidra seeding
    insn_file = os.path.join(OUTPUT_DIR, 'code_addresses.txt')
    with open(insn_file, 'w') as f:
        f.write(f"# All code addresses (instruction-level)\n")
        f.write(f"# One address per line, hex format\n")
        f.write(f"# Total: {len(tracer.code_addrs):,}\n\n")
        for addr in sorted(tracer.code_addrs):
            f.write(f"{addr:08X}\n")
    print(f"Wrote instruction addresses to: {insn_file}")

    # Summary stats
    total_fw_bytes = sum(len(d) for _, d in loaded_blocks.values())
    coverage_pct = 100.0 * len(tracer.code_addrs) / total_fw_bytes if total_fw_bytes else 0
    print(f"\nCoverage: {len(tracer.code_addrs):,} / {total_fw_bytes:,} bytes "
          f"({coverage_pct:.1f}% of loaded firmware)")

    return tracer


if __name__ == '__main__':
    main()
