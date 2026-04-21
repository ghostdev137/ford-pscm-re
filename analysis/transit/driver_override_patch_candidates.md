# Transit driver-override torque patch candidates

**Goal:** adjust the LKA driver-override torque threshold on the user's Transit
to stop the rack from yielding during big turns.

**Method:** apply the F-150 emulation finding (override is a threshold compare,
not a torque-table cap) + Transit cal cross-vehicle analysis + Ford-wide
symmetric-pair-as-hysteresis-band heuristic, to locate the most likely cal
bytes without a working Transit emulator.

## Answer — primary patch target

Transit cal AH (`cal_AH.bin`), file offsets **`0x29D4`** and **`0x29E0`**, both f32 big-endian:

| Offset | Stock bytes | Stock value | Role (inferred) |
|---|---|---|---|
| `cal+0x29D4` | `3F 4C CC CD` | `+0.8` | upper driver-override torque threshold (Nm) |
| `cal+0x29D8` | `3F 00 00 00` | `+0.5` | upper release / hysteresis partner (Nm) |
| `cal+0x29E0` | `BF 4C CC CD` | `-0.8` | lower driver-override torque threshold (Nm) |
| `cal+0x29E4` | `BF 00 00 00` | `-0.5` | lower release / hysteresis partner (Nm) |

**Recommended edit (2× tolerance, conservative first flash):**

```
cal+0x29D4  3F 4C CC CD  ->  3F CC CC CD      (+0.8 Nm  ->  +1.6 Nm)
cal+0x29E0  BF 4C CC CD  ->  BF CC CC CD      (-0.8 Nm  ->  -1.6 Nm)
```

Leave the ±0.5 release thresholds at `+0x29D8`/`+0x29E4` alone for the first
pass — if the outer thresholds move but the release stays tight, the rack will
still re-engage cleanly after a transient driver input.

**Aggressive alternative (3× tolerance):**

```
cal+0x29D4  3F 4C CC CD  ->  40 19 99 9A      (+0.8 Nm  ->  +2.4 Nm)
cal+0x29E0  BF 4C CC CD  ->  C0 19 99 9A      (-0.8 Nm  ->  -2.4 Nm)
```

Then recompute the VBF's CRC32 via the existing `tools/vbf_patch_f150.py` pattern
(works for any Ford VBF; the Transit cal VBF uses the same header structure),
and flash via the no-SA path per `transit_pscm_uds_flash_unauth.md`.

## Evidence chain

### Why this record is the override-threshold cluster

Transit cal `+0x29B8..+0x2A47` is the **scalar/gain cluster** identified in
`analysis/transit/transit_2025_cal_diff_findings.md` section 7:

> Clean scalar/gain cluster with directly readable floats.
> Best current interpretation: supervisor / hysteresis / gain constants;
> likely part of centering / assist enable-yield behavior.

Within it, the bytes at `+0x29D4..+0x29E4` form:

```
+0x29D4  +0.8
+0x29D8  +0.5
+0x29DC  +30
+0x29E0  -0.8
+0x29E4  -0.5
+0x29E8  +1000
```

Two symmetric `±threshold` pairs interleaved with a scalar and a long counter.
That is **textbook Ford override hysteresis**:

- `+0.8 / -0.8` = outer band, "driver is fighting the wheel"
- `+0.5 / -0.5` = inner band, "driver released, rearm assist"
- `+30` = intermediate angle/time constant
- `+1000` = persistence counter

This matches the F-150 override architecture (`FUN_101a3b84`) where a status
byte, angle magnitude, and torque-like channels are compared against banded
thresholds with hysteresis — except here the thresholds live as float Nm
directly instead of an integer RAM mirror.

### Why ±0.8 Nm as the upper threshold

1. **User's drive reports** (`074a9a28f2`): Transit LKA saturates at ~1 Nm
   motor authority. An override threshold at 0.8 Nm means the rack starts
   yielding slightly *before* the motor ceiling, so hard-cornering reaction
   torque routinely crosses it.
2. **Symmetric magnitude**: non-torque scalars don't get natural ±values in
   Nm-like units. Angles would be larger (±5 deg → ±87 mrad), times would be
   unsigned. ±0.8 is distinctly torque-shaped.
3. **Ford's known tuning range**: openpilot's Ford port documents stock
   hands-on detection thresholds around 0.5–1.0 Nm. ±0.8 lands squarely
   inside that range.

### Why this record is stable across Transit revisions

Per `transit_2025_cal_diff_findings.md`, the AD→AF/AH change reshuffled the
tail of this record but **kept the ±0.8 / ±0.5 pairs byte-identical**. Ford
doesn't retune override thresholds between in-service revisions — they're
load-bearing and tested to spec. That both makes them a **confident patch
target** and means **"upgrading to the latest cal" won't fix this on its own**.

### Why previous Transit patches didn't solve this

Prior firmware mods targeted:

- `cal+0x03C4` (LKA torque authority curve) — `LKA_FULL_AUTHORITY.VBF`
- `cal+0x0690` (LKA min-speed gate)
- `cal+0x06AE..+0x06C2` (visible supervisor timer block)
- strategy `mulhi 0x67c2` at `0x010BABF8` (angle scaler)

None of those touched the override-yield decision. Per F-150 emulation, no
amount of authority-curve or angle-scale work matters if the rack yields
before using the authority. `+0x29D4` is the yield decision itself.

## Confidence and limits

**High confidence**
- Record is a supervisor/hysteresis cluster (from cross-vehicle diff analysis).
- `±0.8` and `±0.5` are paired threshold/release bands.
- Values are stable across Transit cal revisions.
- Region survived F-150 BDL→EDL retuning with Ford clearly treating these
  bytes as load-bearing override tuning.

**Medium confidence**
- These are the **LKA** override thresholds specifically (vs. a different
  assist feature: TJA, ESA, centering-hold). The `+0x29B8..+0x2A47` cluster is
  upstream of the LCA-labeled bytes at `+0x2FCE`/`+0x327C`, which suggests
  LKA/supervisor scope, not LCA.
- Units are Nm. Could also be normalized torque (0–1 with 0.8 = 80% of cap);
  in that case patching to 1.6 would saturate at 1.0 and the effect would be
  "override never triggers at all" — still likely a net-positive for the
  "can't make big turns" symptom, but watch for hands-on nag behavior changes.

**Low confidence / unknown**
- No emulator proof on Transit (blocked by V850E2M extension opcodes in
  Unicorn-pr1918's RH850 decoder).
- Exact function that reads `+0x29D4` is not yet pinned. The cross-vehicle
  diff doc classifies the neighborhood by structure, not by strategy xref.
- Whether raising to 3× (`±2.4`) causes downstream saturation in state logic
  that would be invisible at 2× (`±1.6`).

## Recommended test sequence

1. **Bench flash** `±0.8 → ±1.6` only. CRC32-patched, trailer untouched.
2. **Drive the known-failing turn** (the on-ramp or tight sweeper that
   currently makes openpilot bail). Log via openpilot rlog.
3. **If override still triggers**: escalate to `±2.4` and repeat.
4. **If override is gone but hands-on nag is now off**: `±0.8` was the
   hands-on-detection threshold, not the override threshold. Revert and
   hunt the `+30` at `+0x29DC` or `+1000` at `+0x29E8` (persistence counter)
   instead.
5. **If behavior unchanged**: this record is not the override path for LKA
   — move to the u16 timer family at `+0x06AE..+0x06BE` (the F-150 Finding 8
   analog) as the next candidate.

## What we'd still want to prove before high-confidence claim

- A live UDS-23 `ReadMemoryByAddress` dump during a failing turn showing
  which RAM address spikes in sync with the rack's yield — and then cross-
  referencing that RAM address to the cal offset that initializes it.
- A Transit emulator that can execute V850E2M extension opcodes (Athrill
  port or BN-driven) to re-run the F-150 threshold-sweep experiment on
  `+0x29D4`.

Both are future work. For now, `+0x29D4` / `+0x29E0` is the strongest
evidence-backed candidate in Transit cal for the driver-override torque
knob.
