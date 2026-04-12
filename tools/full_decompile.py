"""
Full decompilation of Transit PSCM strategy firmware (transit_strategy_AM.bin).

Linear sweep disassembly across all known code regions, function boundary
detection, CFG construction, IR lifting, constant propagation, and C
pseudocode generation for every function found.

Improvements over v1:
- Known data regions are excluded from disassembly
- Automatic data region detection (ASCII strings, high-.dw density, repeated patterns)
- Better function boundary detection with confidence scoring
- Only high-confidence functions are emitted as pseudocode

Output:
  output/transit_AM_full_decompile.c   -- C pseudocode for all functions
  output/transit_AM_functions.txt      -- Function index with metadata
"""

import os
import sys
import struct
import time
import traceback

# ---- path setup ----
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PROJECT_DIR)

from tools.v850.decoder import V850Decoder
from tools.v850.models import Instruction, REG_NAMES, sign_extend
from tools.v850.cfg import ControlFlowGraph, _is_conditional_branch
from tools.v850.lifter import IRLifter
from tools.v850.propagate import propagate_constants, annotate_address
from tools.v850.structurer import Decompiler, structure_cfg, render_structured

# =============================================================================
# Configuration
# =============================================================================

BIN_PATH = os.path.join(PROJECT_DIR, "bins", "transit_strategy_AM.bin")
BASE_ADDR = 0x01000000  # Strategy firmware base address
OUTPUT_DIR = os.path.join(PROJECT_DIR, "output")

# Known code regions (offsets within the binary file)
CODE_REGIONS = [
    (0x02000, 0x08680),
    (0x08B00, 0x0E280),
    (0x0E500, 0x21680),
    (0x21900, 0x25D80),
    (0x27E00, 0x96A80),
    (0x96D00, 0xC0880),
    (0xC0B00, 0xCB580),
    (0xCB900, 0xEC680),
    (0xECA00, 0xFFF80),
]

# Known data regions within the code regions (file offsets).
# These contain strings, tables, and configuration data that should NOT
# be disassembled.
KNOWN_DATA_REGIONS = [
    (0x02000, 0x05400, "strings/debug_info"),       # NVRAM manager strings, TKP_INFO, paths
    (0x08600, 0x086C0, "config_pointer_table"),      # Address pointer table (CAL/RAM refs)
    (0x08B98, 0x09200, "task_name_strings"),          # AUTOSAR task name strings
    (0x0DB74, 0x0DD00, "DID_table"),                  # Diagnostic ID table
    (0x0DF0C, 0x0DF70, "ascii_charset_table"),        # ASCII character set table
]

# Minimum confidence score for a function to be included in output.
# Scoring:
#   starts with PREPARE: +10
#   ends with return (JMP [lp], DISPOSE+jmp): +10
#   is a JARL/call target: +8
#   high decode rate (>90%): +10 scaled
#   contains CALLT/JARL calls: +5
#   reasonable size (3-5000 insns): +5
#   contains valid MOVHI patterns: +5
MIN_CONFIDENCE = 15

# Address range annotations
ADDR_ANNOTATIONS = [
    (0x00FD0000, 0x00FEFFFF, "CALIBRATION"),
    (0x01000000, 0x010FFFFF, "STRATEGY"),
    (0x010E0000, 0x010EFFFF, "STRATEGY_CFG"),
    (0x40000000, 0x4FFFFFFF, "RAM"),
    (0xFFF80000, 0xFFFFFFFF, "PERIPHERAL"),
]


def classify_addr(addr):
    """Return region name for a resolved address."""
    if addr is None:
        return None
    addr &= 0xFFFFFFFF
    for lo, hi, name in ADDR_ANNOTATIONS:
        if lo <= addr <= hi:
            return name
    return None


# =============================================================================
# Data Region Detection
# =============================================================================

def detect_data_regions(data, known_regions, window_size=128):
    """Auto-detect data regions within the binary.

    Scans for:
    1. ASCII string runs (>= 8 consecutive printable chars)
    2. Regions where >50% of halfwords would decode as .dw
    3. Regions of repeated 2-byte or 4-byte patterns (lookup tables)

    Returns a sorted list of (start_offset, end_offset, reason) tuples,
    merged with the known_regions.
    """
    all_regions = list(known_regions)  # start with known ones

    # --- 1. ASCII string regions ---
    run_start = None
    run_len = 0
    for i in range(len(data)):
        b = data[i]
        if 0x20 <= b <= 0x7E:
            if run_start is None:
                run_start = i
                run_len = 1
            else:
                run_len += 1
        else:
            if run_start is not None and run_len >= 16:
                # Align to 2-byte boundary
                aligned_start = run_start & ~1
                aligned_end = (run_start + run_len + 1) & ~1
                all_regions.append((aligned_start, aligned_end, "ascii_strings"))
            run_start = None
            run_len = 0

    # --- 2. Repeated pattern detection (data tables) ---
    # Scan for regions where the same 4-byte pattern repeats >= 8 times
    for off in range(0, len(data) - 32, 4):
        pattern = data[off:off+4]
        if pattern == b'\x00\x00\x00\x00' or pattern == b'\xFF\xFF\xFF\xFF':
            continue  # skip fill patterns, handled elsewhere
        count = 0
        pos = off
        while pos + 4 <= len(data) and data[pos:pos+4] == pattern:
            count += 1
            pos += 4
        if count >= 8:
            all_regions.append((off, pos, "repeated_pattern"))

    # --- Merge overlapping/adjacent regions ---
    all_regions.sort(key=lambda r: r[0])
    merged = []
    for start, end, reason in all_regions:
        if merged and start <= merged[-1][1] + 4:
            # Extend the previous region
            prev_start, prev_end, prev_reason = merged[-1]
            new_end = max(prev_end, end)
            # Collect unique reasons without exploding the string
            prev_reasons = set(prev_reason.split('+'))
            prev_reasons.add(reason)
            new_reason = '+'.join(sorted(prev_reasons))
            merged[-1] = (prev_start, new_end, new_reason)
        else:
            merged.append((start, end, reason))

    return merged


def offset_in_data_region(offset, data_regions):
    """Check if a file offset falls within any detected data region."""
    for start, end, _ in data_regions:
        if start <= offset < end:
            return True
    return False


def subtract_data_regions(code_regions, data_regions):
    """Remove data regions from code regions, returning clean code-only intervals.

    Returns list of (start, end) tuples representing code-only regions.
    """
    result = []
    for cs, ce in code_regions:
        # Collect data regions that overlap with this code region
        overlaps = [(ds, de) for ds, de, _ in data_regions if ds < ce and de > cs]
        if not overlaps:
            result.append((cs, ce))
            continue

        # Sort overlaps and subtract them
        overlaps.sort()
        cur = cs
        for ds, de in overlaps:
            if ds > cur:
                result.append((cur, ds))
            cur = max(cur, de)
        if cur < ce:
            result.append((cur, ce))

    return result


# =============================================================================
# Step 1: Linear sweep disassembly across clean code regions
# =============================================================================

def disassemble_regions(data, decoder, base_addr, regions):
    """Linear sweep decode across all code regions.
    Returns dict: addr -> Instruction
    """
    all_insns = {}
    total = 0
    for start_off, end_off in regions:
        offset = start_off
        while offset < end_off and offset + 2 <= len(data):
            insn = decoder.decode(data, offset, base_addr)
            if insn is None:
                offset += 2
                continue
            all_insns[insn.addr] = insn
            offset += insn.size
            total += 1
    return all_insns


# =============================================================================
# Step 2: Find function boundaries with confidence scoring
# =============================================================================

def compute_confidence(entry_addr, instructions, call_targets, all_insns_set):
    """Compute a confidence score for a detected function.

    Scoring:
      +10  starts with PREPARE
      +10  ends with return (JMP [lp] or DISPOSE+jmp)
      +8   is a JARL/call target
      +5   contains CALLT or JARL calls (uses the calling convention)
      +5   reasonable size (3-5000 instructions)
      +5   contains valid MOVHI/MOVEA address patterns
      0-10 instruction decode success rate (scaled)

    Returns (score, details_dict)
    """
    if not instructions:
        return 0, {}

    score = 0
    details = {}

    first = instructions[0]
    last = instructions[-1]
    n = len(instructions)

    # --- Start pattern ---
    if first.mnemonic == 'prepare':
        score += 10
        details['starts_prepare'] = True
    else:
        details['starts_prepare'] = False

    # --- End pattern ---
    ends_with_return = (
        last.is_return or
        (last.mnemonic == 'dispose' and last.is_branch) or
        (last.mnemonic == 'jr' and last.is_branch and not _is_conditional_branch(last))
    )
    if ends_with_return:
        score += 10
        details['ends_return'] = True
    else:
        details['ends_return'] = False

    # --- Is a call target ---
    if entry_addr in call_targets:
        score += 8
        details['is_call_target'] = True
    else:
        details['is_call_target'] = False

    # --- Decode success rate ---
    dw_count = sum(1 for i in instructions if i.mnemonic == '.dw')
    decode_rate = (n - dw_count) / n if n > 0 else 0
    decode_score = int(decode_rate * 10)
    score += decode_score
    details['decode_rate'] = decode_rate
    details['dw_count'] = dw_count

    # --- Contains calls (CALLT/JARL) ---
    has_calls = any(i.mnemonic == 'callt' or i.is_call for i in instructions)
    if has_calls:
        score += 5
        details['has_calls'] = True
    else:
        details['has_calls'] = False

    # --- Reasonable size ---
    if 3 <= n <= 5000:
        score += 5
        details['reasonable_size'] = True
    else:
        details['reasonable_size'] = False

    # --- Valid MOVHI patterns (address construction) ---
    has_movhi = any(i.mnemonic == 'movhi' for i in instructions)
    if has_movhi:
        # Check if MOVHI values are plausible (common prefixes: 0x0100, 0x00FD, 0x4000, 0xFFF8)
        valid_movhi = False
        for i in instructions:
            if i.mnemonic == 'movhi':
                parts = i.op_str.split(', ')
                if len(parts) >= 1:
                    try:
                        imm = int(parts[0], 0) & 0xFFFF
                        if imm in (0x0100, 0x0101, 0x00FD, 0x00FE, 0x010E,
                                   0x4000, 0x4001, 0x4002, 0x4003,
                                   0xFFF8, 0xFFFF, 0x0000):
                            valid_movhi = True
                            break
                    except ValueError:
                        pass
        if valid_movhi:
            score += 5
            details['valid_movhi'] = True
        else:
            details['valid_movhi'] = False
    else:
        details['valid_movhi'] = False

    details['score'] = score
    return score, details


def find_functions(all_insns, call_targets_out=None):
    """Detect function boundaries using multiple heuristics with confidence scoring.

    Returns:
        dict: func_entry_addr -> (list[Instruction], confidence_score, details)
    """
    sorted_addrs = sorted(all_insns.keys())
    addr_set = set(sorted_addrs)

    # Collect all branch/call targets
    call_targets = set()
    branch_targets = set()
    for insn in all_insns.values():
        if insn.branch_target is not None:
            if insn.is_call:
                call_targets.add(insn.branch_target)
            else:
                branch_targets.add(insn.branch_target)

    # Export call targets if requested
    if call_targets_out is not None:
        call_targets_out.update(call_targets)

    # ---- Pass 1: Find function entry points ----
    # Heuristic 1: PREPARE instructions
    func_entries = set()
    for addr in sorted_addrs:
        insn = all_insns[addr]
        if insn.mnemonic == 'prepare':
            func_entries.add(addr)

    # Heuristic 2: JARL/CALLT call targets in our decoded range
    for target in call_targets:
        if target in addr_set:
            func_entries.add(target)

    # Heuristic 3: After a return, next instruction starts a new function
    for i, addr in enumerate(sorted_addrs):
        insn = all_insns[addr]
        is_func_end = (
            insn.is_return or
            (insn.mnemonic == 'dispose' and insn.is_branch)
        )
        # Unconditional JR also ends a function
        if (insn.mnemonic == 'jr' and insn.is_branch
                and not _is_conditional_branch(insn)):
            is_func_end = True

        if is_func_end and i + 1 < len(sorted_addrs):
            next_addr = sorted_addrs[i + 1]
            # Only if reasonably close (not a gap between regions)
            if next_addr - (addr + insn.size) < 16:
                func_entries.add(next_addr)

    # ---- Pass 2: Split instructions into functions ----
    sorted_entries = sorted(func_entries & addr_set)

    # Build entry -> index in sorted_addrs for fast lookup
    addr_to_idx = {}
    for idx, addr in enumerate(sorted_addrs):
        addr_to_idx[addr] = idx

    raw_functions = {}
    for i, entry in enumerate(sorted_entries):
        if entry not in addr_to_idx:
            continue
        start_idx = addr_to_idx[entry]

        # End is either the next function entry or end of addresses
        if i + 1 < len(sorted_entries):
            next_entry = sorted_entries[i + 1]
            if next_entry in addr_to_idx:
                end_idx = addr_to_idx[next_entry]
            else:
                end_idx = start_idx + 1
                while end_idx < len(sorted_addrs) and sorted_addrs[end_idx] < next_entry:
                    end_idx += 1
        else:
            end_idx = len(sorted_addrs)

        func_insns = [all_insns[sorted_addrs[j]] for j in range(start_idx, end_idx)]
        if func_insns:
            # Trim function at the first return/end instruction
            # to avoid absorbing trailing data or the next function's code
            trimmed = _trim_function_at_return(func_insns, branch_targets)
            raw_functions[entry] = trimmed

    # ---- Pass 3: Score each function and filter ----
    functions = {}
    removed = {'low_confidence': 0, 'too_long_no_return': 0, 'high_dw_rate': 0}

    for entry, insns in raw_functions.items():
        # Skip functions that are extremely long without a return (likely data)
        if len(insns) > 10000:
            # Check if there's a return anywhere in the first 10000
            has_return = any(
                i.is_return or (i.mnemonic == 'dispose' and i.is_branch)
                for i in insns[:10000]
            )
            if not has_return:
                removed['too_long_no_return'] += 1
                continue

        # Skip functions with very high .dw rate (>50% = almost certainly data)
        dw_count = sum(1 for i in insns if i.mnemonic == '.dw')
        if len(insns) > 5 and dw_count / len(insns) > 0.50:
            removed['high_dw_rate'] += 1
            continue

        score, details = compute_confidence(entry, insns, call_targets, addr_set)

        if score >= MIN_CONFIDENCE:
            functions[entry] = (insns, score, details)
        else:
            removed['low_confidence'] += 1

    return functions, removed


def _trim_function_at_return(instructions, branch_targets):
    """Trim a function's instruction list at the last reachable return.

    If the function has a return instruction and the instructions after it
    are not branch targets within this function, trim them off. This prevents
    absorbing trailing alignment padding or data into the function body.
    """
    if not instructions:
        return instructions

    # Find the addresses within this function that are branch targets
    func_addrs = set(i.addr for i in instructions)
    internal_targets = set()
    for insn in instructions:
        if insn.branch_target is not None and insn.branch_target in func_addrs:
            internal_targets.add(insn.branch_target)

    # Find the last return-like instruction that isn't followed by
    # internally-referenced code
    last_return_idx = None
    for idx, insn in enumerate(instructions):
        if (insn.is_return or
            (insn.mnemonic == 'dispose' and insn.is_branch) or
            (insn.mnemonic == 'jr' and insn.is_branch and not _is_conditional_branch(insn))):
            # Check if anything after this is a branch target
            has_later_target = False
            for j in range(idx + 1, len(instructions)):
                if instructions[j].addr in internal_targets:
                    has_later_target = True
                    break
                if instructions[j].addr in branch_targets:
                    has_later_target = True
                    break
            if not has_later_target:
                last_return_idx = idx
                break  # Take the first "final" return

    if last_return_idx is not None and last_return_idx < len(instructions) - 1:
        return instructions[:last_return_idx + 1]

    return instructions


# =============================================================================
# Step 3: Decompile a single function with full error handling
# =============================================================================

def decompile_function(func_addr, instructions, decompiler):
    """Try full decompilation; fall back to annotated disassembly on error.

    Returns (pseudocode_str, metadata_dict)
    """
    meta = {
        'addr': func_addr,
        'size': len(instructions),
        'num_blocks': 0,
        'has_bsw': False,
        'callt_count': 0,
        'cal_refs': [],
        'ram_refs': [],
        'strategy_refs': [],
        'peripheral_refs': [],
        'error': None,
    }

    # Gather quick metadata
    for insn in instructions:
        if insn.mnemonic == 'bsw':
            meta['has_bsw'] = True
        if insn.mnemonic == 'callt':
            meta['callt_count'] += 1

    # Try full decompilation
    try:
        code = decompiler.decompile_instructions(func_addr, instructions)

        # Count basic blocks from CFG
        try:
            cfg = ControlFlowGraph.from_instructions(instructions)
            meta['num_blocks'] = len(cfg.blocks)
        except Exception:
            meta['num_blocks'] = 1

        # Extract resolved addresses from the code for metadata
        _extract_refs_from_code(code, meta)

        return code, meta

    except Exception as exc:
        meta['error'] = str(exc)

        # Fallback: produce annotated disassembly
        lines = []
        lines.append(f"void func_0x{func_addr:08X}() {{")
        lines.append(f"    // DECOMPILE FAILED: {exc}")
        lines.append(f"    // Showing raw disassembly ({len(instructions)} instructions)")
        lines.append("")

        # Do simple register tracking for address resolution
        regs = {'r0': 0}
        for insn in instructions:
            comment = ""

            # Track MOVHI/MOVEA/ADDI for address resolution
            m = insn.mnemonic
            parts = insn.op_str.split(", ")
            try:
                if m == "movhi" and len(parts) == 3:
                    imm = int(parts[0], 0)
                    r1 = parts[1]
                    r2 = parts[2]
                    base_val = regs.get(r1, 0) if r1 in regs else 0
                    val = ((imm << 16) + base_val) & 0xFFFFFFFF
                    regs[r2] = val
                    ann = classify_addr(val)
                    if ann:
                        comment = f"  // {r2} = 0x{val:08X} ({ann})"
                elif m == "movea" and len(parts) == 3:
                    imm = int(parts[0], 0)
                    r1 = parts[1]
                    r2 = parts[2]
                    if r1 in regs:
                        val = (regs[r1] + imm) & 0xFFFFFFFF
                        regs[r2] = val
                        ann = classify_addr(val)
                        if ann:
                            comment = f"  // {r2} = 0x{val:08X} ({ann})"
                elif m == "addi" and len(parts) == 3:
                    imm = int(parts[0], 0)
                    r1 = parts[1]
                    r2 = parts[2]
                    if r1 in regs:
                        val = (regs[r1] + imm) & 0xFFFFFFFF
                        regs[r2] = val
                elif m == "mov" and len(parts) == 2:
                    src, dst = parts
                    if src.startswith("0x") or src.lstrip('-').isdigit():
                        regs[dst] = int(src, 0) & 0xFFFFFFFF
                    elif src in regs:
                        regs[dst] = regs[src]
                elif m == "callt":
                    imm = int(insn.op_str, 16) if insn.op_str.startswith("0x") else 0
                    comment = f"  // callt_0x{imm:02X}()"
                elif m == "bsw":
                    comment = "  // bswap() BE->LE"
            except (ValueError, IndexError):
                pass

            # Memory access annotation
            if m.startswith("ld.") or m.startswith("st."):
                bracket_s = insn.op_str.find('[')
                bracket_e = insn.op_str.find(']')
                if bracket_s >= 0 and bracket_e >= 0:
                    base_reg = insn.op_str[bracket_s+1:bracket_e]
                    if base_reg in regs:
                        # Extract displacement
                        if m.startswith("ld."):
                            disp_str = insn.op_str[:bracket_s].rstrip()
                        else:
                            # st: "reg, disp[base]"
                            p2 = insn.op_str.split(',')
                            if len(p2) >= 2:
                                disp_str = p2[1].strip().split('[')[0].strip()
                            else:
                                disp_str = "0"
                        try:
                            disp = int(disp_str, 0)
                            data_addr = (regs[base_reg] + disp) & 0xFFFFFFFF
                            ann = classify_addr(data_addr)
                            rw = "read" if m.startswith("ld.") else "write"
                            if ann:
                                comment = f"  // {rw} {ann} @ 0x{data_addr:08X}"
                                if ann == "CALIBRATION":
                                    meta['cal_refs'].append(data_addr)
                                elif ann == "RAM":
                                    meta['ram_refs'].append(data_addr)
                            elif data_addr > 0xFFFF:
                                comment = f"  // {rw} 0x{data_addr:08X}"
                        except ValueError:
                            pass

            # Branch annotation
            if insn.is_branch and insn.branch_target is not None:
                if insn.is_return:
                    comment = "  // return"
                elif insn.is_call:
                    comment = f"  // call func_0x{insn.branch_target:08X}"

            lines.append(f"    // 0x{insn.addr:08X}: {insn.mnemonic:<10s} {insn.op_str}{comment}")

        lines.append("}")
        return "\n".join(lines), meta


def _extract_refs_from_code(code, meta):
    """Extract resolved address references from generated pseudocode."""
    import re
    # Look for hex addresses in comments and code
    for m in re.finditer(r'0x([0-9A-Fa-f]{8})', code):
        addr = int(m.group(1), 16)
        region = classify_addr(addr)
        if region == "CALIBRATION" and addr not in meta['cal_refs']:
            meta['cal_refs'].append(addr)
        elif region == "RAM" and addr not in meta['ram_refs']:
            meta['ram_refs'].append(addr)
        elif region == "STRATEGY" and addr not in meta['strategy_refs']:
            meta['strategy_refs'].append(addr)
        elif region == "PERIPHERAL" and addr not in meta['peripheral_refs']:
            meta['peripheral_refs'].append(addr)


# =============================================================================
# Step 4: Scan for interesting patterns (CAN IDs, etc.)
# =============================================================================

# Known CAN IDs for PSCM
KNOWN_CAN_IDS = {
    0x3B3: "SteeringPinion_Data",
    0x3CC: "Lane_Keep_Assist_Status",  # LaActAvail lives here
    0x3D7: "Steering_Data_FD1",
    0x083: "BodyInfo_3_FD1",
    0x091: "BrakeSnData_4",
    0x167: "Cluster_Info1_FD1",
    0x215: "APIM_Send",
    0x3E6: "EPAS_INFO",
    0x07D: "BCM_Lamp",
    0x076: "VehDyn_Yaw_FD1",
    0x077: "VehDyn_Lat_FD1",
    0x07A: "VehicleOperatingModes",
}


def scan_for_can_ids(instructions, regs_at_addr=None):
    """Check if function instructions contain known CAN ID values."""
    found = {}
    # Simple scan: look for MOV/CMP with known values
    for insn in instructions:
        m = insn.mnemonic
        parts = insn.op_str.split(", ")
        try:
            if m in ("mov", "cmp", "movea", "addi", "ori") and len(parts) >= 2:
                val_str = parts[0]
                val = int(val_str, 0) & 0xFFFFFFFF
                if val in KNOWN_CAN_IDS:
                    found[val] = KNOWN_CAN_IDS[val]
            # Check for MOVHI+MOVEA resolving to CAN ID-range values
            # (unlikely for CAN IDs as they're small, but check movea results)
        except (ValueError, IndexError):
            pass
    return found


# =============================================================================
# Main orchestration
# =============================================================================

def main():
    t0 = time.time()

    # ---- Load binary ----
    if not os.path.exists(BIN_PATH):
        print(f"ERROR: Binary not found: {BIN_PATH}")
        sys.exit(1)

    with open(BIN_PATH, "rb") as f:
        data = f.read()

    print(f"Loaded {len(data):,} bytes from {BIN_PATH}")
    print(f"Base address: 0x{BASE_ADDR:08X}")

    # ---- Create output directory ----
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # ---- Step 0: Detect data regions ----
    print("\n[0/4] Detecting data regions...")
    data_regions = detect_data_regions(data, KNOWN_DATA_REGIONS)
    total_data_bytes = sum(e - s for s, e, _ in data_regions)
    print(f"  Found {len(data_regions)} data regions ({total_data_bytes:,} bytes)")
    for start, end, reason in data_regions[:20]:
        print(f"    0x{start:05X}-0x{end:05X} ({end-start:5d} bytes) [{reason}]")
    if len(data_regions) > 20:
        print(f"    ... and {len(data_regions) - 20} more")

    # Subtract data regions from code regions to get clean code-only intervals
    clean_code_regions = subtract_data_regions(CODE_REGIONS, data_regions)
    print(f"  Code regions after exclusion: {len(clean_code_regions)} intervals")

    # ---- Step 1: Linear sweep disassembly ----
    print("\n[1/4] Linear sweep disassembly across clean code regions...")
    decoder = V850Decoder()
    all_insns = disassemble_regions(data, decoder, BASE_ADDR, clean_code_regions)
    print(f"  Decoded {len(all_insns):,} instructions across {len(clean_code_regions)} regions")

    # ---- Step 2: Find function boundaries with confidence scoring ----
    print("\n[2/4] Finding function boundaries...")
    call_targets = set()
    functions_scored, removed = find_functions(all_insns, call_targets)

    # Unpack for downstream compatibility: functions dict is addr -> insns
    functions = {addr: insns for addr, (insns, score, details) in functions_scored.items()}
    func_scores = {addr: (score, details) for addr, (insns, score, details) in functions_scored.items()}

    print(f"  Found {len(functions):,} functions (confidence >= {MIN_CONFIDENCE})")
    print(f"  Removed: {removed['low_confidence']} low-confidence, "
          f"{removed['high_dw_rate']} high-.dw-rate, "
          f"{removed['too_long_no_return']} too-long-no-return")
    total_removed = sum(removed.values())
    print(f"  Total removed as garbage: {total_removed}")

    # Stats
    total_insns = sum(len(v) for v in functions.values())
    sizes = [len(v) for v in functions.values()]
    if sizes:
        print(f"  Total instructions in functions: {total_insns:,}")
        print(f"  Function sizes: min={min(sizes)}, max={max(sizes)}, "
              f"avg={sum(sizes)/len(sizes):.0f}, median={sorted(sizes)[len(sizes)//2]}")
        scores = [s for s, _ in func_scores.values()]
        print(f"  Confidence scores: min={min(scores)}, max={max(scores)}, "
              f"avg={sum(scores)/len(scores):.1f}")

    # ---- Step 3: Decompile all functions ----
    print("\n[3/4] Decompiling all functions...")
    decompiler = Decompiler(data, BASE_ADDR)

    results = {}       # addr -> pseudocode string
    all_meta = {}      # addr -> metadata dict
    errors = []
    can_id_funcs = {}  # addr -> {can_id: name}

    done = 0
    func_addrs = sorted(functions.keys())
    n_funcs = len(func_addrs)
    last_pct = -1

    for func_addr in func_addrs:
        insns = functions[func_addr]
        code, meta = decompile_function(func_addr, insns, decompiler)
        results[func_addr] = code
        all_meta[func_addr] = meta

        if meta['error']:
            errors.append((func_addr, meta['error']))

        # Scan for CAN IDs
        cids = scan_for_can_ids(insns)
        if cids:
            can_id_funcs[func_addr] = cids

        done += 1
        pct = done * 100 // n_funcs
        if pct != last_pct and pct % 5 == 0:
            elapsed = time.time() - t0
            print(f"  {pct}% ({done}/{n_funcs}) -- {elapsed:.1f}s elapsed")
            last_pct = pct

    t_decomp = time.time() - t0
    print(f"  Decompilation complete in {t_decomp:.1f}s")
    print(f"  Errors: {len(errors)} / {n_funcs}")

    # ---- Step 4: Write output files ----
    print("\n[4/4] Writing output files...")

    # ---- Output 1: Full decompile C file ----
    decomp_path = os.path.join(OUTPUT_DIR, "transit_AM_full_decompile.c")
    total_lines = 0

    with open(decomp_path, 'w', encoding='utf-8') as f:
        # Header
        f.write("/*\n")
        f.write(" * Transit PSCM Strategy Firmware - Full Decompilation\n")
        f.write(f" * Binary: transit_strategy_AM.bin ({len(data):,} bytes)\n")
        f.write(f" * Base address: 0x{BASE_ADDR:08X}\n")
        f.write(f" * Functions: {n_funcs}\n")
        f.write(f" * Decompile errors: {len(errors)}\n")
        f.write(f" * Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(" *\n")
        f.write(" * ThyssenKrupp Presta EPS (AUTOSAR)\n")
        f.write(" * V850E2 architecture, CALLT-based calling convention\n")
        f.write(" *\n")
        f.write(" * Address regions:\n")
        f.write(" *   0x00FD0000-0x00FEFFFF: CALIBRATION (read-only data)\n")
        f.write(" *   0x01000000-0x010FFFFF: STRATEGY (code + const data)\n")
        f.write(" *   0x010E0000-0x010EFFFF: STRATEGY config block\n")
        f.write(" *   0x40000000-0x4FFFFFFF: RAM (variables)\n")
        f.write(" *   0xFFF80000-0xFFFFFFFF: Peripheral registers\n")
        f.write(" */\n\n")

        # CAN ID cross-reference
        if can_id_funcs:
            f.write("/* ================================================================\n")
            f.write(" * CAN ID CROSS-REFERENCE\n")
            f.write(" * ================================================================ */\n")
            for cid in sorted(KNOWN_CAN_IDS.keys()):
                name = KNOWN_CAN_IDS[cid]
                refs = [fa for fa, cids in can_id_funcs.items() if cid in cids]
                if refs:
                    ref_str = ", ".join(f"func_0x{fa:08X}" for fa in refs)
                    f.write(f"// CAN 0x{cid:03X} ({name}): {ref_str}\n")
            f.write("\n\n")

        # All functions
        for func_addr in func_addrs:
            code = results[func_addr]
            meta = all_meta[func_addr]
            score, details = func_scores.get(func_addr, (0, {}))

            # Section header
            f.write(f"/* {'='*68} */\n")
            f.write(f"/* func_0x{func_addr:08X}")
            f.write(f"  ({meta['size']} insns, {meta['num_blocks']} blocks)")
            f.write(f"  [confidence={score}]")
            if details.get('starts_prepare'):
                f.write("  [PREPARE]")
            if details.get('ends_return'):
                f.write("  [RET]")
            if details.get('is_call_target'):
                f.write("  [CALLED]")
            if meta['has_bsw']:
                f.write("  [BSW]")
            if meta['callt_count']:
                f.write(f"  [CALLT x{meta['callt_count']}]")
            if meta.get('cal_refs'):
                f.write(f"  [CAL x{len(meta['cal_refs'])}]")
            if meta.get('ram_refs'):
                f.write(f"  [RAM x{len(meta['ram_refs'])}]")
            if func_addr in can_id_funcs:
                cids = can_id_funcs[func_addr]
                cid_str = ", ".join(f"0x{c:03X}" for c in sorted(cids.keys()))
                f.write(f"  [CAN: {cid_str}]")
            if meta['error']:
                f.write("  [FALLBACK DISASM]")
            f.write(" */\n")

            f.write(code)
            f.write("\n\n")

            total_lines += code.count('\n') + 1

    print(f"  Wrote {decomp_path}")
    print(f"  Total lines of pseudocode: {total_lines:,}")

    # ---- Output 2: Function index ----
    index_path = os.path.join(OUTPUT_DIR, "transit_AM_functions.txt")

    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(f"Transit PSCM Strategy - Function Index\n")
        f.write(f"{'='*100}\n")
        f.write(f"{'Address':<14s} {'Size':>5s} {'Blocks':>6s} {'Conf':>5s} {'BSW':>4s} "
                f"{'CALLT':>6s} {'CAL':>4s} {'RAM':>4s} {'Flags':<16s} {'CAN IDs':<20s} {'Status':<10s}\n")
        f.write(f"{'-'*14} {'-'*5} {'-'*6} {'-'*5} {'-'*4} {'-'*6} {'-'*4} {'-'*4} "
                f"{'-'*16} {'-'*20} {'-'*10}\n")

        for func_addr in func_addrs:
            meta = all_meta[func_addr]
            score, details = func_scores.get(func_addr, (0, {}))
            bsw = "Y" if meta['has_bsw'] else ""
            callt = str(meta['callt_count']) if meta['callt_count'] else ""
            cal = str(len(meta['cal_refs'])) if meta.get('cal_refs') else ""
            ram = str(len(meta['ram_refs'])) if meta.get('ram_refs') else ""

            # Build flags string
            flags = []
            if details.get('starts_prepare'):
                flags.append('P')
            if details.get('ends_return'):
                flags.append('R')
            if details.get('is_call_target'):
                flags.append('C')
            if details.get('has_calls'):
                flags.append('J')
            flags_str = ''.join(flags)

            cids = ""
            if func_addr in can_id_funcs:
                cids = ", ".join(f"0x{c:03X}" for c in sorted(can_id_funcs[func_addr].keys()))

            status = "ERROR" if meta['error'] else "OK"

            f.write(f"0x{func_addr:08X}   {meta['size']:>5d} {meta['num_blocks']:>6d} "
                    f"{score:>5d} {bsw:>4s} {callt:>6s} {cal:>4s} {ram:>4s} "
                    f"{flags_str:<16s} {cids:<20s} {status:<10s}\n")

        # Summary
        f.write(f"\n{'='*90}\n")
        f.write(f"Total functions: {n_funcs}\n")
        f.write(f"Functions with BSW: {sum(1 for m in all_meta.values() if m['has_bsw'])}\n")
        f.write(f"Functions with CALLT: {sum(1 for m in all_meta.values() if m['callt_count'] > 0)}\n")
        f.write(f"Functions with CAL refs: {sum(1 for m in all_meta.values() if m.get('cal_refs'))}\n")
        f.write(f"Functions with RAM refs: {sum(1 for m in all_meta.values() if m.get('ram_refs'))}\n")
        f.write(f"Functions with CAN IDs: {len(can_id_funcs)}\n")
        f.write(f"Decompile errors: {len(errors)}\n")
        f.write(f"Garbage removed: {total_removed}\n")
        f.write(f"  low confidence: {removed['low_confidence']}\n")
        f.write(f"  high .dw rate: {removed['high_dw_rate']}\n")
        f.write(f"  too long no return: {removed['too_long_no_return']}\n")
        f.write(f"\nFlags: P=starts with PREPARE, R=ends with return, C=is call target, J=contains calls\n")

        # Confidence distribution
        f.write(f"\n--- Confidence Score Distribution ---\n")
        score_buckets = {}
        for addr in func_addrs:
            s, _ = func_scores.get(addr, (0, {}))
            bucket = (s // 10) * 10
            score_buckets[bucket] = score_buckets.get(bucket, 0) + 1
        for bucket in sorted(score_buckets.keys()):
            f.write(f"  {bucket:3d}-{bucket+9:3d}: {score_buckets[bucket]:4d} functions\n")

        if can_id_funcs:
            f.write(f"\n--- CAN ID References ---\n")
            for cid in sorted(KNOWN_CAN_IDS.keys()):
                name = KNOWN_CAN_IDS[cid]
                refs = [fa for fa, cids in can_id_funcs.items() if cid in cids]
                if refs:
                    f.write(f"  0x{cid:03X} ({name}):\n")
                    for fa in refs:
                        f.write(f"    func_0x{fa:08X} ({all_meta[fa]['size']} insns)\n")

    print(f"  Wrote {index_path}")

    # ---- Final summary ----
    elapsed = time.time() - t0
    print(f"\n{'='*70}")
    print(f"COMPLETE in {elapsed:.1f}s")
    print(f"{'='*70}")
    print(f"  Data regions excluded: {len(data_regions)} ({total_data_bytes:,} bytes)")
    print(f"  Functions found (after filtering): {n_funcs}")
    print(f"  Functions removed as garbage: {total_removed}")
    print(f"    - low confidence (<{MIN_CONFIDENCE}): {removed['low_confidence']}")
    print(f"    - high .dw rate (>50%): {removed['high_dw_rate']}")
    print(f"    - too long without return: {removed['too_long_no_return']}")
    print(f"  Total pseudocode lines: {total_lines:,}")
    print(f"  Decompile successes: {n_funcs - len(errors)}")
    print(f"  Decompile errors (fallback to disasm): {len(errors)}")
    print(f"  Functions with CAN ID references: {len(can_id_funcs)}")

    if can_id_funcs:
        print(f"\n  CAN ID 0x3CC (Lane_Keep_Assist_Status) references:")
        refs_3cc = [fa for fa, cids in can_id_funcs.items() if 0x3CC in cids]
        if refs_3cc:
            for fa in refs_3cc:
                print(f"    func_0x{fa:08X} ({all_meta[fa]['size']} insns)")
        else:
            print(f"    (none found -- may be loaded indirectly)")

    if errors:
        print(f"\n  First 10 errors:")
        for fa, err in errors[:10]:
            print(f"    0x{fa:08X}: {err[:80]}")

    # Print sample output from a CAN-ID-related function
    if can_id_funcs:
        print(f"\n{'='*70}")
        print("SAMPLE OUTPUT - First function with CAN ID references:")
        print(f"{'='*70}")
        sample_addr = sorted(can_id_funcs.keys())[0]
        sample_code = results[sample_addr]
        # Print first 60 lines
        sample_lines = sample_code.split('\n')
        for line in sample_lines[:60]:
            print(line)
        if len(sample_lines) > 60:
            print(f"  ... ({len(sample_lines) - 60} more lines)")

    # Print sample of a 0x3CC function if found
    refs_3cc = [fa for fa, cids in can_id_funcs.items() if 0x3CC in cids]
    if refs_3cc:
        print(f"\n{'='*70}")
        print(f"SAMPLE OUTPUT - CAN 0x3CC (Lane_Keep_Assist) function:")
        print(f"{'='*70}")
        fa = refs_3cc[0]
        code = results[fa]
        code_lines = code.split('\n')
        for line in code_lines[:80]:
            print(line)
        if len(code_lines) > 80:
            print(f"  ... ({len(code_lines) - 80} more lines)")


if __name__ == "__main__":
    main()
