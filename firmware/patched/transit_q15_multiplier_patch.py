#!/usr/bin/env python3
"""Transit PSCM strategy patch: scale up the Q15 multiplier in the torque
angle reader, which sets the per-tick gain from commanded angle (arg1 of
torque_angle_reader_Q15, fed by the APA/LKA path) to motor torque output.

TARGET
------
Virtual address:   0x010BABF8    (inside function torque_angle_reader_Q15 @ 0x10BABF2)
Raw-binary offset: 0xBABF8       (base = 0x01000000, so vaddr - 0x01000000)

INSTRUCTION
-----------
  mulhi 0x67C3, r6, r6      (V850 Format VI)
  Bytes (LE): e6 36 c3 67
  imm16 is signed Q15, range -1.0 .. +0.99997
  Current coefficient 0x67C3 = 26563 ≈ Q15 +0.8106
  The 2 bytes that carry the immediate are at file offsets 0xBABFA-0xBABFB (c3 67).

Downstream: output feeds through arbiter state machines and eventually the
motor PWM at 0xFFE34040 (TAUB0_TDR).

SCALING LIMITS
--------------
Because mulhi's imm is signed Q15, max patch value is 0x7FFF (+0.99997).
That's 0x7FFF / 0x67C3 = 1.234x of current gain — not the 3x patch
available on F150 (which used float mulf.s, different format).

If 1.23x is insufficient, there are 8 other mulhi instructions in the same
function (see SECONDARY_PATCHES below) that participate in different
control paths. Patching additional ones compounds the gain, but each
change risks breaking a filter or compensator. Experiment with one at a
time.

USAGE
-----
  $ python3 transit_q15_multiplier_patch.py <input_blk0.bin> <output_blk0.bin>
  $ python3 transit_q15_multiplier_patch.py --scale 1.23 ...
  $ python3 transit_q15_multiplier_patch.py --raw-imm 0x7FFF ...

DEFAULTS
--------
--scale 1.23  (max achievable by single-multiplier patch given Q15 limits)

NEXT STEPS AFTER RUNNING
------------------------
1. The output file is the patched *decompressed* strategy blob.
2. To build a flashable VBF, re-compress with the LZSS encoder at
   ~/ford-pscm-re/tools/vbf_lzss_encode.py and recompute the strategy CRC.
3. Flash via ForScan / UDS RequestDownload. Prior-session notes say
   Transit PSCM accepts RequestDownload without SA key (seed/key bypass).
"""

import argparse
import os
import shutil
import struct
import sys


# File offset of the mulhi imm16 (Q15 coefficient) for the primary gain.
# These 2 bytes are the payload of the patch.
OFFSET_IMM_LO = 0xBABFA
OFFSET_IMM_HI = 0xBABFB

# Known-good original bytes (sanity check)
ORIGINAL_BYTES = bytes([0xC3, 0x67])   # 0x67C3 LE
ORIGINAL_IMM = 0x67C3

# Maximum safe signed Q15 value for the mulhi imm16 field.
Q15_MAX_SIGNED = 0x7FFF

# Secondary mulhi sites in the same function. Patch ONLY if the primary
# doesn't move the needle — compounding changes multiple gains can
# destabilize filters.
SECONDARY_PATCHES = [
    # (file_offset, va, original_imm, meaning)
    (0xBAC0A, 0x010BAC08, 0x66C1, "mulhi 0x66C1, r8, r5  (Q15 +0.80)  — sibling forward gain"),
    (0xBACE4, 0x010BACE2, 0x3D51, "mulhi 0x3D51, r6, r7  (Q15 +0.48)  — intermediate"),
    (0xBAC8A, 0x010BAC88, 0xBE50, "mulhi 0xBE50, r2, r3  (Q15 -0.51)  — compensator (negative)"),
]


def patch(in_path: str, out_path: str, new_imm: int, force: bool = False) -> None:
    if not (0 <= new_imm <= 0xFFFF):
        sys.exit(f"imm must fit in 16 bits, got 0x{new_imm:X}")
    if new_imm > Q15_MAX_SIGNED and not force:
        sys.exit(
            f"imm 0x{new_imm:X} exceeds Q15 signed max 0x{Q15_MAX_SIGNED:X}. "
            f"Values above 0x7FFF are interpreted as NEGATIVE by mulhi's "
            f"sign-extension — this will REVERSE the gain and almost "
            f"certainly drive the steering in the wrong direction. "
            f"Use --force if you actually want that."
        )

    shutil.copyfile(in_path, out_path)

    with open(out_path, "r+b") as f:
        f.seek(OFFSET_IMM_LO)
        existing = f.read(2)
        if existing != ORIGINAL_BYTES:
            sys.exit(
                f"Sanity check failed: bytes at 0x{OFFSET_IMM_LO:X} are "
                f"{existing.hex(' ')}, expected {ORIGINAL_BYTES.hex(' ')}. "
                f"Either wrong input file or the function has shifted."
            )
        f.seek(OFFSET_IMM_LO)
        f.write(struct.pack("<H", new_imm))

    ratio = new_imm / ORIGINAL_IMM
    print(f"Patched {in_path} → {out_path}")
    print(f"  file offset 0x{OFFSET_IMM_LO:X}-0x{OFFSET_IMM_HI:X}")
    print(f"  bytes: {ORIGINAL_BYTES.hex(' ')} → "
          f"{struct.pack('<H', new_imm).hex(' ')}")
    print(f"  imm:   0x{ORIGINAL_IMM:04X} → 0x{new_imm:04X}")
    print(f"  scale: ×{ratio:.3f} of original gain")
    print()
    print("Secondary patch sites (only touch if needed):")
    for fo, va, imm, desc in SECONDARY_PATCHES:
        print(f"  file 0x{fo:X} / va 0x{va:08X}  imm 0x{imm:04X}  — {desc}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input_bin",
                    help="Input decompressed strategy blob (blk0, base 0x01000000)")
    ap.add_argument("output_bin",
                    help="Output patched blob")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--scale", type=float, default=None,
                   help="Scale factor (e.g. 1.23). Computes new imm from original.")
    g.add_argument("--raw-imm", type=lambda x: int(x, 0), default=None,
                   help="Set imm directly (hex or dec). E.g. 0x7FFF for max +Q15.")
    ap.add_argument("--force", action="store_true",
                    help="Allow unsigned imm > 0x7FFF (reverses sign — probably bad)")
    args = ap.parse_args()

    if args.raw_imm is not None:
        new_imm = args.raw_imm
    elif args.scale is not None:
        new_imm = min(int(ORIGINAL_IMM * args.scale), 0xFFFF)
    else:
        # Default: maximum safe signed Q15.
        new_imm = Q15_MAX_SIGNED

    patch(args.input_bin, args.output_bin, new_imm, force=args.force)


if __name__ == "__main__":
    main()
