# F-150 strategy — shared angle reader scaling

A ~2-byte patch in the F-150 PSCM strategy that multiplies the decoded steering-angle command by an arbitrary float, applied uniformly to all six steering modes (LKA, LDW, LCA, TJA, APA, BlueCruise). How we found it, how to replicate it, and why the same approach doesn't drop into Ghidra for Transit.

---

## Why F-150 was easy and Transit is hard

**F-150 PSCM runs baseline Renesas V850.** Confirmed from the AUTOSAR hardware-abstraction string `AH850S54GxxxxxV101` in `ML34-14D005-AB.VBF` (2021 Lariat BlueCruise SBL).

**Transit PSCM runs RH850-extended** (same family, newer generation, adds saturating arithmetic, bit-string ops, SHA2 peripheral helpers, and a handful of other extension opcodes).

Ghidra 12 ships with a working V850 processor spec **for baseline V850 only**. When it hits a file full of baseline V850 instructions, auto-analysis lifts every function cleanly — `FUN_xxxxxxxx` labels, full decompilation, complete cross-reference graph, "100% lift". When it hits an RH850 extension opcode, it fails to decode that instruction, breaks the containing function's analysis, and the decompilation of the surrounding code falls apart — then downstream functions that reference the broken one also fail to lift.

That's the single reason F-150 RE was a one-afternoon job and Transit has been a multi-day guess-and-check exercise against our own driving data.

### Consequences for the workflow

- **F-150 path** → Ghidra 12 stock → auto-analyze → browse the function list, look at xrefs, patch.
- **Transit path** → either (a) author a Ghidra V850E2M/RH850 SLEIGH spec covering the extension opcodes, (b) use an alternate disassembler that knows RH850 (IDA Pro + RH850 plugin, or `rh850-elf-objdump` from the GNU toolchain), or (c) continue the cal-byte bisect approach with drive-data validation.

---

## The finding

F-150 strategy contains a single small function that reads the wire-domain steering-angle command, clamps it, and converts it to the integer domain used by every downstream steering controller. The last five instructions of that function are:

```
0x1009690e   40 5e 80 44     movhi   0x4480, r0, r11   ; r11 = 0x44800000 = float 1024.0
0x10096912   08 8f 64 64     mulf.s  r11, r17, r12     ; r12 = clamped_value * 1024.0
0x10096916   e1 67 40 54     trncf.sw r12, r10         ; r10 = (int)r12
0x1009691a   ea 00           sxh     r10               ; sign-extend low halfword
0x1009691c   7f 80           jmp     [lp]              ; return
```

The scale factor `1024.0` is encoded in a single `movhi` because IEEE-754 float32 for 1024.0 has zero low 16 bits (`0x44800000`), so the compiler emits the constant in one instruction with no literal-pool entry. Changing the halfword `0x4480` to another float32 high-half directly changes the scale factor.

### How we found it — the xref trick

With Ghidra's complete function list + call graph:

1. Locate the CAN RX handlers for the three steering message IDs openpilot and Ford both use: `0x3CA` (LKA), `0x3D3` (LCA/TJA/LateralMotionControl), `0x3A8` (APA).
2. For each, follow the call chain from "frame byte decode" → "physical-units conversion" → "controller input."
3. Find the function that **appears in all three call chains.** That's the shared angle reader.
4. Read the last basic block — it's the unit conversion `float angle × SCALE → int`, and `SCALE` is a literal constant.

On F-150 this took minutes because Ghidra's decompiler renders every step as pseudo-C with the float constant inlined. The xref panel does the "all three chains share this" match for free.

---

## The patch

**File offset:** `0x569D0..0x569D1` (2 bytes) in the decompressed F-150 strategy.
**What changes:** the 16-bit MOVHI immediate that sets the scale factor.

| Multiplier | New halfword | New float | File bytes @ `0x569D0..0x569D1` |
|---|---|---|---|
| 1.0× (stock) | `0x4480` | 1024.0 | `80 44` |
| **1.5×** | `0x44C0` | 1536.0 | `C0 44` |
| **2.0×** | `0x4500` | 2048.0 | `00 45` |
| **3.0×** | `0x4540` | 3072.0 | `40 45` |
| **4.0×** | `0x4580` | 4096.0 | `80 45` |

The bytes are stored little-endian in the strategy binary because the instruction stream is LE. The immediate value is byte-swapped relative to how you write the constant in documentation.

### Effect

The function is the common input path for every controller that receives a steering-angle command from the camera / parking module / adaptive-cruise module. Patching the scale factor multiplies what the downstream controllers see — so a 3× patch makes every steering-mode-requested angle arrive 3× larger at the motor loop.

This is blunt: LKA, LDW, LCA, TJA, APA, and BlueCruise all see the multiplied value, not just the one you wanted to boost. APA at low speed could over-correct dangerously at 3×. Start at 1.5×.

---

## Caveats

1. **Downstream saturation.** If `_DAT_fef21a6e` (the RAM slot the result lands in) is a 16-bit signed field, 3× saturates at the wire-level range and clips. Symptom: command flattens at the clip regardless of requested value. Drop to 1.5× or 2× and measure.
2. **Uniform scaling across every steering mode.** Safe-area parking-lot testing only, especially for the first drive after flashing.
3. **Authority clamp at `FUN_101a4d56` is now in scope.** Stock code reaches this clamp only at large commanded angles; at 3× it's hit routinely. If over-aggressive clipping appears, that clamp's ±10240 bound can be widened (4 instructions, different patch — `FUN_101a4d56`'s `cmp` immediates against `±0x2800`, candidates `±0x7800` for a 3× headroom expansion).
4. **Recompute strategy CRC32 after patching.** The SBL checksum gate enforces the header's `file_checksum` over the whole binary region. Our `tools/vbf_patch_f150.py` already handles this for cal VBFs — strategy VBFs need the same treatment. The SBL itself (RH850 HW SHA2) verifies its own integrity but not the strategy content it flashes.

---

## Replicating for Transit

The same kind of shared-angle-scale constant almost certainly exists in Transit. What's missing is the ability to find it:

- **Baseline attempt:** load `analysis/transit/AM_block0_0x01000000.bin` into Ghidra 12 with stock V850 processor. Auto-analysis will fail at some fraction of functions.
- **What to check:** percentage of functions successfully decompiled (Ghidra's "Function Analyzer" progress). If it's <70%, the extension opcodes are widespread enough that cross-reference searches can't be trusted.
- **Workarounds** (unexplored):
  - IDA Pro + [Hex-Rays RH850 processor module](https://hex-rays.com/products/processors/) (paid, commercial).
  - `rh850-elf-objdump` from the Renesas GNU-RH850 toolchain — gives disassembly without decompilation or xrefs, but at least decodes every instruction.
  - Extend Ghidra's `V850.sinc` SLEIGH file with the RH850 extension opcodes (likely a few days of work).

Until one of those lands, Transit stays on the drive-evidence-driven bisect approach:
- Known: `cal+0x0690 = 3.0` (our "low-speed floor" scalar) is drive-safe
- Unknown: whether the Transit strategy has an analogous angle-scale scalar (probably yes — it's a standard EPS design pattern) and where it lives.

---

## What this doc does **not** establish

- Whether the F-150 patch has been test-driven. (README for `LKA_FULL_AUTHORITY.VBF` notes **not yet test-flashed**.)
- Whether the Transit strategy's equivalent function lives at an analogous offset (probably doesn't — Transit and F-150 are different platform vendors with different firmware teams).
- Whether `_DAT_fef21a6e` is 16-bit or 32-bit downstream — needs a decompile of the callee.

## See also

- `docs/vehicles/f150-2022.md` — Ghidra 12 V850 decodes F-150 cleanly
- `analysis/f150/strategy_findings.md` — broader F-150 strategy RE
- `analysis/f150/verdict.md` — pre-flash signoff for F-150 patches
- `firmware/patched/F150_Lariat_BlueCruise/` — working F-150 patch set (cal-only)
