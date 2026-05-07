# 6G Bronco PSCM (NB3C-*)

Initial analysis of three VBFs pulled from a 6G Bronco. Vehicle topology
is unusual: legacy CAN IPMA + CAN-FD PSCM. Question on the table was
whether the PSCM is LKA-only or whether LCA (BlueCruise /
openpilot-style continuous lateral) is in there too.

**Answer: it has LCA. The PSCM directly subscribes to
`LateralMotionControl2` (0x3D6) — the same message openpilot ships
on Ford.** It is *not* LKA-only.

## Files

All three VBFs are uncompressed (`data_format_identifier = 0x00`), so
the raw block bytes are immediately RE-ready under `decompressed/`.

| VBF                     | sw_part_type | Erase range              | Size     | Role          |
|-------------------------|--------------|--------------------------|----------|---------------|
| `NB3C-14D003-AB.VBF`    | DATA         | `0x10040000 + 0x180000`  | 1.50 MB  | Strategy      |
| `NB3C-14D004-AD.VBF`    | DATA         | `0x101C0000 + 0x10000`   | 64 KB    | SBL? (small)  |
| `NB3C-14D007-AAB.VBF`   | DATA         | `0x101D0000 + 0x30000`   | 192 KB   | Calibration   |

ECU address `0x730`, frame format `CAN_STANDARD` for diagnostics
(vehicle bus is CAN-FD; this is just the UDS flash transport). Each
VBF also carries a 300-byte verification structure block at `*F400`.

VBF block CRC16 passes. The header `file_checksum` disagrees with
`vbf_decompress.py`'s zlib CRC32 — same false-mismatch we see on every
Ford PSCM VBF; the header CRC algorithm is different from what the
tool computes.

## CAN rx dispatch table (the strong evidence)

The strategy contains two identical-format `(handler_id, can_id, sentinel)`
dispatch tables, 12 bytes per record, sentinel `0x400007FF`. Two copies
suggests two CAN controllers (likely HSCAN + CAN-FD).

* **Table A** at VA `0x100412A8 .. 0x100414DC` — 47 entries
* **Table B** at VA `0x10041590 .. 0x100417C4` — 47 entries

The two tables are identical except for three slots that differ between
buses: ISO-TP responder ID (`0x7CB` vs `0x7CA`), `0x712` vs `0x713`,
and `0x61F` vs `0x660`.

Lateral / ADAS-relevant entries (offsets within each table):

| Tbl off | handler_id   | CAN ID  | Name                              |
|---------|--------------|---------|-----------------------------------|
| `0x108` | `0x00030814` | `0x3F1` | `ParkAid_Data` (APA)              |
| `0x114` | `0x00030801` | `0x3D7` | LMC2 counter (presumed)           |
| `0x120` | `0x0003081E` | `0x3D6` | **LateralMotionControl2 (LCA)**   |
| `0x12C` | `0x00030817` | `0x3CA` | **Lane_Assist_Data1 (IPMA LKA)**  |
| `0x138` | `0x00030816` | `0x3B3` | `AccCmd`                          |
| `0x150` | `0x00030819` | `0x3A8` | ACC-related                       |
| `0x174` | `0x00030805` | `0x230` | **AdvTrJamAsst (BC lat support)** |
| `0x180` | `0x00030827` | `0x217` | `AccelerationData`                |
| `0x1C8` | `0x00030810` | `0x176` | `Steering_Pinion_Data`            |
| `0x1D4` | `0x0003081D` | `0x167` | `Yaw_Data_FD1`                    |

This is direct subscription evidence — these aren't loose constants in
code, they're entries in the CAN rx filter / dispatch table that the
driver uses to route each frame to its handler. If `0x3D6` weren't
serviced, it wouldn't be in this table.

The handler IDs follow `0x0003 08xx`, with `xx` ranging `0x00..0x2B` —
likely AUTOSAR Com / PduR PDU handles, not raw code addresses. Resolving
them to functions needs the AUTOSAR-side Rte tables (typical workflow:
follow the PduR config struct → callback array).

## What I previously claimed that needs correcting

In the first pass I cited two cross-platform fingerprints that don't
hold up under closer inspection:

* **The `(hdlr, can_id, 0x400007FF)` rx dispatch format is *not* shared
  with F-150 PSCM.** F-150 '21 ELF and F-150 '22 strategy contain
  zero such tables. So while Bronco supports the same lateral feature
  set, its CAN-stack / AUTOSAR generation differs from F-150 BlueCruise.
  Don't expect to lift F-150 dispatcher maps onto Bronco verbatim.

* **The float `1024.0` LE byte pattern is in both Bronco and F-150
  strategies, but in a *data* table (Rte init / parameter blob), not as
  the operand of a `movhi 0x4480` instruction.** The F-150 LCA angle
  scaler note (`f150_lca_override_cal_mapping`) is about the *instruction*
  encoding; the raw-byte hit doesn't transplant to Bronco. Bronco may
  still have a 1024.0-scaled parameter somewhere, but presence of those
  four bytes alone doesn't prove it's the LCA scaler.

What still holds:

* Cal block size and structural fingerprint are very close to F-150
  BlueCruise (193,536 B vs 195,584 B; 3.7% vs 3.5% printable; BE-tuning
  histograms `f0.5_BE = 40 / 37`, `u2800_BE = 66 / 62`, `u5000_BE = 126
  / 128`). Same calibration template family, even if the specific offsets
  for individual params differ.
* `cal + 0x1610` and `cal + 0x1630` (the F-150 LCA speed-keyed envelope
  offsets) do **not** contain the F-150 envelope shape in Bronco — values
  there are different magnitudes (peaks ~4900, not ~124). Bronco has its
  own LCA tuning offsets that need to be located independently.
* Bronco cal does contain a recurring 16-entry `[96, 96, 93, 81, 57, 31,
  0…]` envelope at uniform stride `0xF54` (cal+0x13A2, +0x22F6, +0x324A,
  +0x419E, +0x50F2, +0x6046) — six copies. Looks like a per-mode or
  per-axis authority profile; consumer is TBD.

## Will openpilot work?

The PSCM side is *necessary but not sufficient*.

What this analysis settles:

* The actuator endpoint openpilot targets (`LateralMotionControl2` =
  0x3D6) is wired into the PSCM's rx dispatch on both filter banks.
  This is the strongest possible static evidence short of running it.
* `Lane_Assist_Data1` (legacy IPMA LKA) is also subscribed — so the
  PSCM is *able* to take lateral commands from either source. With
  IPMA on legacy CAN and PSCM on CAN-FD, the realistic openpilot
  topology is panda-on-CAN-FD spoofing IPMA_ADAS's `LMC2`.

What this analysis does **not** settle:

1. **Angle-clamp envelope inside this strategy.** Bronco's clamp constants
   and speed-keyed authority limits are not at the F-150 cal offsets.
   A real Ghidra lift of the LMC2 handler (entered from PduR via
   `handler_id = 0x0003081E`) is required to find them.
2. **Arbitration gates.** Whether the PSCM honors LMC2 unconditionally
   or only when some "BC active" / "TJA active" / hands-on-wheel flag
   is set elsewhere — not yet traced. Soft-gating like this is normal
   in Ford BC code.
3. **CAN-FD harness wiring on the actual car.** PSCM-FD ↔ rest-of-bus
   topology and where panda has to interpose is a per-vehicle wiring
   question.
4. **Vehicle fingerprint in stock openpilot.** Whether 6G Bronco is in
   `selfdrive/car/ford/values.py` (or sunnypilot/bluepilot) is a port
   question, separate from PSCM willingness.
5. **Longitudinal / ACC.** This analysis is steering-only; the ACM has
   its own story.

So: **the firmware does not disqualify openpilot use.** Net read is that
the Bronco PSCM is a BlueCruise-feature-set ECU that listens for the
right command. But "open-pilot ready" still requires a Ghidra lift of
the LMC2 handler chain (clamps + gates), an on-car CAN-FD harness check,
and vehicle-side openpilot port work.

## Next steps

1. Lift `decompressed/NB3C-14D003-AB_block0_0x10040000.bin` in Ghidra
   (RH850 v850e3 LE). Resolve PduR `handler_id = 0x0003081E` to the
   LMC2 entry function. Trace to:
   * Signal extraction (`LatCtlPath_No_*`, `LatCtl0_*`, etc.)
   * i16/float clamp chain analogous to F-150's ±0x2800/±0x5000
   * Gate predicates (TJA active, BC active, fault state)
2. Locate the actual LCA speed-keyed envelope tables in this cal —
   probably accessible from the LMC2 chain via gp/RAM-relative reads,
   not at the F-150 offsets.
3. Inspect the 64 KB `NB3C-14D004-AD` region — too small to be a
   strategy delta, likely SBL or a small CAN-map shim.
4. On a real Bronco: panda-only CAN-FD bench replay of synthesized
   LMC2 (counter + CRC valid), watch `Steering_Pinion_Data` and
   `Steering_Data_FD1` to confirm the wheel actually moves.
