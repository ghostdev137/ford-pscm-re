# 6G Bronco PSCM (NB3C-*)

Initial analysis of three VBFs pulled from a 6G Bronco. Vehicle topology is
unusual: legacy CAN IPMA + CAN-FD PSCM. Question on the table was whether the
PSCM is LKA-only or whether LCA (BlueCruise / openpilot-style continuous
lateral) is in there too.

**Answer: it has LCA. Not LKA-only.**

## Files

All three VBFs are uncompressed (`data_format_identifier = 0x00`), so the
raw block bytes are immediately RE-ready under `decompressed/`.

| VBF                     | sw_part_type | Erase range              | Size     | Role            |
|-------------------------|--------------|--------------------------|----------|-----------------|
| `NB3C-14D003-AB.VBF`    | DATA         | `0x10040000 + 0x180000`  | 1.50 MB  | Strategy        |
| `NB3C-14D004-AD.VBF`    | DATA         | `0x101C0000 + 0x10000`   | 64 KB    | SBL? (small)    |
| `NB3C-14D007-AAB.VBF`   | DATA         | `0x101D0000 + 0x30000`   | 192 KB   | Calibration     |

ECU address `0x730`, frame format `CAN_STANDARD` for diagnostics (vehicle
bus is CAN-FD; this is just the UDS flash transport). Each VBF also carries
a 300-byte verification structure block at `*F400`.

VBF block CRC16 passes. The header `file_checksum` disagrees with
`vbf_decompress.py`'s zlib CRC32 — same false-mismatch we see on every
Ford PSCM VBF; the header CRC algorithm is different from what the tool
computes.

## LCA-vs-LKA evidence

LE32 CAN-ID literal hit count in the strategy block (the firmware loads
the ID as a 32-bit immediate when subscribing / dispatching):

| ID    | Name                              | Bronco | F-150 '21 ELF | F-150 '22 | Transit '25 |
|-------|-----------------------------------|--------|---------------|-----------|-------------|
| 0x3CA | Lane_Assist_Data1 (IPMA LKA)      | 2      | 0             | 0         | 0           |
| 0x3D6 | **LateralMotionControl2 (LCA)**   | **2**  | 0             | 0         | 0           |
| 0x3D3 | LMC1 (legacy LCA)                 | 0      | 12            | 0         | 0           |
| 0x230 | AdvTrJamAsst (BC lat support)     | 2      | 1             | 1         | 0           |
| 0x131 | Steering_Data_FD1                 | 1      | 0             | 0         | 0           |
| 0x3F1 | ParkAid_Data (APA)                | 17     | 15            | 15        | 0           |

Bronco subscribes to **both** the legacy IPMA LKA path (`Lane_Assist_Data1`)
**and** the LMC2 BlueCruise / openpilot path. F-150 '21 used the older LMC1
form; Bronco moved to LMC2 like newer F-150 builds.

(The F-150 '22 and Transit zeros for some rows are partly artifacts of how
those strategy blocks are split / encoded — the Bronco vs F-150-'21 ELF
comparison is the cleanest cross-platform check.)

## Family fingerprint

The cal block looks like a sibling of the F-150 BlueCruise cal, not Transit:

| Metric                                  | Bronco cal | F-150 '22 cal |
|-----------------------------------------|------------|----------------|
| Size                                    | 193,536 B  | 195,584 B      |
| Printable byte density                  | 3.7%       | 3.5%           |
| f0.5 (BE `3F 00 00 00`) hits            | 40         | 37             |
| u16 BE `0x2800` hits                    | 66         | 62             |
| u16 BE `0x5000` hits                    | 126        | 128            |

And in the strategy itself, the F-150 LCA angle scaler — float `1024.0`
loaded LE as `00 00 80 44` (the `movhi 0x4480` constant) — appears once
in the Bronco strategy, once in F-150 '21 ELF, once in F-150 '22 strategy,
and **zero times** in the LKA-only Transit AM strategy (which uses a
`mulhi 0x67c2` form instead). Same scaler family as F-150 BlueCruise.

## Topology note

CAN-IPMA + CAN-FD-PSCM is consistent with what we see here. Legacy IPMA
ships `Lane_Assist_Data1` over HS CAN, gateway forwards it; LMC2 lives
natively on the CAN-FD chassis bus. The PSCM listens on both buses /
both message families.

## Caveat

LE32 hit counts prove the IDs are loaded as 32-bit constants in code. They
don't by themselves prove every code path is enabled by this trim's cal.
But cal+strategy parity with F-150 BlueCruise + LMC2 references + the
1024.0 angle scaler ≈ "this is a BlueCruise-family PSCM."

## Next steps

- Lift `decompressed/NB3C-14D003-AB_block0_0x10040000.bin` in Ghidra
  (RH850 v850e3 LE) using the same `SeedFromPointerTables` /
  `SeedFromJarls` flow proven on F-150 / Transit.
- Inspect the 64 KB `NB3C-14D004-AD` region — too small to be a strategy
  delta; likely SBL or a small CAN map shim.
- Map cal + 0x1610 / cal + 0x1630 (F-150 LCA speed-keyed authority
  envelopes) to confirm offset parity in this cal.
