# F-150 PSCM Cal RE — Findings (2021 Lariat 502A BlueCruise)

**Source:** `firmware/F150_2021_Lariat_BlueCruise/ML34-14D007-EDL.VBF`
**Compared against:** `firmware/F150_2022/ML34-14D007-BDL` (older revision)
**Cal data:** 195,584 bytes, flashes to `0x101D0000`
**Endianness:** **little-endian** (u16 and float32) — different from Transit/Escape which are big-endian

Quick entry point:

- [cal_plain_language_map.md](/Users/rossfisher/ford-pscm-re/analysis/f150/cal_plain_language_map.md) — plain-language catalog of what each major cal block does in EPS terms
- [eps_mode_separation_ghidra_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/eps_mode_separation_ghidra_trace.md) — which cal/workspace families belong to `LKA`, `LCA/BlueCruise`, `APA`, or shared EPS logic

---

## ⚠️ F-150 VBF verification structure (updated)

Unlike my first guess, the `file_checksum` in the header **IS a standard zlib CRC32** of everything after the ASCII header (covers block header + name tag + data + trailer). It's recomputable.

However, the file also has a **296-byte trailer** after the block data containing:
- ~256 bytes of high-entropy data (likely RSA-2048 signature)
- 12 bytes of block-count + block-header repeat
- 32 bytes of hash (algorithm not yet identified — not a straight SHA-256 of any obvious region)

**All four F-150 VBF types** (cal `DATA`, supplementary `DATA`, strategy `EXE`, bootloader `SBL`) have this trailer structure. So the signature layer is present on every file type, not just cal.

The CRC32 is definitely enforced by the SBL during flashing. The trailer hash/signature MAY be enforced by the SBL or MAY only be checked at boot by the PSCM's mask ROM — unknown without testing. Our patches recompute CRC32 correctly; they cannot update the RSA layer without Ford's signing key.

```
File layout (ML34-14D007-EDL.VBF):
  bytes 0–1500      ASCII header (`};` terminator at 1499)
  bytes 1505–1512   u32 BE addr=0x101D0000, u32 BE len=0x0002FC00
  bytes 1513–1528   16-byte part-name tag "ML34-14D007-EDL\0"
  bytes 1529–197112 195,584 bytes of cal data
  bytes 197113+     256-byte RSA signature + repeated block header + 32-byte hash
```

**Implication:** A patched cal with valid CRCs but invalid signature **will likely be rejected** by the PSCM's SBL. Patching may require:
- Signature-bypass SBL (unknown if available)
- A signing oracle (unlikely)
- Runtime manipulation instead (openpilot-style `0x213 DesTorq` CAN spoofing with stock firmware)

Flash attempts should **start with a full backup** and a plan for module replacement/recovery.

---

## Endianness

All values below are **LITTLE-ENDIAN**. Confirmed by:
- Float32 values like `00 00 20 41` → 10.0 (valid only as LE IEEE-754)
- Monotonic u16 curves read sensibly LE (`17 00 25 00 42 00 ...` → 23, 37, 66, ...)

---

## Finding 1: `10.0 m/s` ≈ 22.37 mph LKA minimum-speed candidate (HIGH confidence)

The user's friend reports LKA has a **~23 mph minimum-speed gate**. The value `10.0 m/s` (= 22.37 mph) appears as float32 LE **27 times** in the cal, most in structured feature-config records. Three highest-confidence candidates:

### cal+0x00C4 — feature config block A
```
+0x00B8  0.800     \
+0x00BC  0.500      |
+0x00C0  200.000    |-- [gain, gain, MAX_SPEED, MIN_SPEED, ...]
+0x00C4  10.000    /   ←  LKA min-speed candidate
+0x00C8  3.500
+0x00CC  0.055
+0x00D0  55.000
+0x00D4  3.600
```

### cal+0x0114 / cal+0x0120 — feature config block B (TWO adjacent min-speed values!)
```
+0x0108  250.000    \
+0x010C  40.000      |
+0x0110  40.000      |
+0x0114  10.000     /   ←  min-speed candidate #1 (LKA?)
+0x0118  1.000
+0x011C  200.000       ←  max-speed
+0x0120  10.000         ←  min-speed candidate #2 (LCA?)
+0x0124  1.000
+0x0128  66.000
+0x012C  50.000
```

This block's structure `[MAX, MIN, gain, MAX, MIN, gain, ...]` is the signature of **two related speed gates** — likely LKA min-speed at 0x0114 and LCA min-speed at 0x0120 (or vice-versa).

### Candidate patch (if signature bypass works)
```
cal+0x0114: 00 00 20 41  →  00 00 00 00   (10.0 m/s → 0.0 m/s)
cal+0x0120: 00 00 20 41  →  00 00 00 00   (10.0 m/s → 0.0 m/s)
cal+0x00C4: 00 00 20 41  →  00 00 00 00   (conservative: also zero for safety)
```

Safer alternative — lower to 0.5 m/s (~1 mph) to avoid divide-by-zero in any PID loops:
```
cal+0x0114: 00 00 20 41  →  00 00 00 3F   (10.0 → 0.5)
cal+0x0120: 00 00 20 41  →  00 00 00 3F
```

---

## Finding 1b: mixed EPS supervisor record at `cal+0x07ADC` (HIGH confidence for neighborhood, medium for exact field roles)

**Correction to the old shorthand:** this is not just "two naked LKA timer words." Ghidra now shows that the F-150 lateral/EPS supervisor uses multiple config records:

- a mixed float/int record that best fits this `0x07ADC` neighborhood
- a separate packed debounce/persistence record
- a curve/lookup record

What remains true is that `cal+0x07ADC` contains a very important timer/supervisor neighborhood:

```
cal+0x07ADC:  10 27   (u16 LE = 10000)   arm timer
cal+0x07ADE:  10 27   (u16 LE = 10000)   re-arm timer
cal+0x07AE0:  1500, 300, 257, 3, 256, 257, 0, 1   (related debounce/state params)
```

Two adjacent u16 = 10000 in a mixed float/int struct region. This pair is **identical between BDL and EDL**.

What Ghidra adds:

- the live 4-state helper described in [lka_timer_ghidra_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/lka_timer_ghidra_trace.md) uses:
  - one fixed `10001 ms` window
  - two byte-scaled `*10000 ms` timers
- the broader EPS supervisor split is documented in [eps_supervisor_ghidra_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/eps_supervisor_ghidra_trace.md)

Best current read:

- `0x07ADC/0x07ADE` still belong to the same lateral/EPS supervisor neighborhood
- the adjacent `0x01/0x01` byte pair at `0x07AE4/0x07AE5` is now a better match for the directly proven per-substate `*10000 ms` timer fields
- the `10000/10000` pair may be a higher-level arm/re-arm pair in the same record rather than the only live timing fields

A third `10000` at `cal+0x07E64` has neighbors `300, 1500` and still looks like a sibling subsystem supervisor timer (ESA / TJA / confirmation style behavior), not a duplicate of the same helper.

### Revised LKA-unlock patch
```
cal+0x07ADC: 10 27 → 00 00  (arm timer: 10 s → 0)
cal+0x07ADE: 10 27 → 00 00  (re-arm timer: 10 s → 0)
cal+0x0114:  00 00 20 41 → 00 00 00 00  (engage min-speed: 10 m/s → 0)
```

**Leave `cal+0x0120` alone** — almost certainly the LCA engage min-speed, and LCA is already continuous (no patch needed).

## Finding 2: BDL→EDL changes reveal Ford's tuning philosophy

Diffing the newer `EDL` against older `BDL` cal (both 195,584 bytes):
- **2,782 byte-level diffs** organized into **67 regions**
- Most changes appear in **4 identical copies** spaced ~0xF00 apart — Ford uses four variant calibrations (trim-dependent or profile-dependent)

### Key diff: `cal+0x1402..0x1416` — EDL **zeroed** a timer-like table
*(Not the LKA lockout — see Finding 1b. All Fords keep LKA locked. Most likely this is a re-located or deprecated table — Ford reworked it rather than removing a safety feature.)*

```
BDL: [..., 0, 655, 655, 655, 655, 655, 655, 655, 655, 655, 655, 0]
EDL: [..., 0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0, 0]
```
655 × 10 ms = **6.55 s**. Ford **removed** a 6.55-second timer. Four copies zeroed (at 0x13F0, 0x23xx, 0x32xx, 0x41xx).

**Interpretation:** This may be a lockout-style timer that Ford disabled in the firmware revision. If it's LKA-related, it's already gone in EDL — no patch needed there.

### Key diff: `cal+0x185E` — timer reduced 12.8 s → 8.96 s
```
BDL @ 0x185E: 1280 (= 12.8 s)
EDL @ 0x185E:  896 (= 8.96 s)
```

### Key diff: `cal+0x1520..0x153C` — breakpoints exactly halved
```
BDL: 32, 64, 96, 128, 192, 256, 320, 512, 768, 960, 1344, 1920
EDL: 16, 32, 48,  64,  96, 128, 160, 256, 384, 480,  672,  960
```
Every value halved. Likely a torque ramp-up or rate-limit table.

### Key diff: `cal+0x7280..0x7420` — BlueCruise tuning
A large region of float32 scalars and flag bytes changed. This is almost certainly **BlueCruise-specific tuning** (LCA gains, hand-off thresholds) that was updated between revisions.

---

## Finding 3: Monotonic-curve torque/speed breakpoints (repeats 4×)

Starting at `cal+0x0DAA`, `0x1CFA`, `0x2C4A`, `0x3B9E` — same 18-entry curve in all 4 variants:
```
LE u16: 23, 37, 66, 111, 170, 244, 332, 436, 553, 686, 850, 1026, 1219, 1423, 1645, 1882, 2132, 2398
```
Geometric/exponential growth. Likely a **torque-authority-vs-something breakpoint table**, not a speed gate. The leading `23` is probably not the LKA min-speed (it's the first entry of a curve, not a scalar gate).

A secondary similar curve follows, starting with `31`.

---

## Finding 4: Bell-curve torque authority profile

At `cal+0x1660` and `cal+0x350C` (and 2 more copies):
```
EDL: [10, 19, 23, 29, 31, 32, 31, 23, 16, 10, 6, 0, ...]  (symmetric-ish)
BDL: [14, 25, 32, 40, 43, 44, 42, 33, 23, 14, 9, 0, ...]  (~40% higher peak)
```
**EDL reduced the peak authority from 44 → 32**. Consistent with a more conservative LKA/LCA tuning (less aggressive steering).

---

## Finding 5: APA-related float tables

Multiple 10.0-containing records appear in the `cal+0x6000–0x8100` range:
```
cal+0x6AB4: [10.0, 20.0, 30.0, 40.0, 50.0]     (speed breakpoints)
cal+0x77D0: [10.0, 20.0, 30.0, 40.0, 50.0]
cal+0x780C: [13.9, 0.0, 5.0, 10.0, 20.0, 50.0, 0.0, 10.0]
cal+0x781C: [..., 10.0, 20.0, 30.0, 40.0, 50.0]
cal+0x7934: [500.0, 1000.0, 3000.0, 20.0, 40.0, 40.0, 10.0]
cal+0x79C8: [..., 20.0, 30.0, 80.0, 10.0, 150.0, 20.0, 30.0, 80.0]
```
These look like APA / LKA / LCA lookup-table breakpoints where speed in m/s (or kph) is the X-axis. 10.0 as the first entry means "table starts at 10 m/s" — which is consistent with "gate at 10 m/s."

---

## Finding 6: Timer-adjacent float supervisor block at `cal+0x7D68..0x7E3F`

Immediately upstream of the known F-150 timer neighborhoods (`0x07ADC` and `0x07E64`) is a dense set of short float tables:

```text
cal+0x07D68: [1.0, 1.0, 0.7, 0.6, 0.5, 0.4, 0.2]
cal+0x07D88: [3.0, 1.5789, 1.2857, 1.1114, 1.0227, 0.8871, 0.8]
cal+0x07DAC: [0.6667, 0.9333, 0.8333, 0.8333, 0.8333, 0.8, 0.4167]
cal+0x07DCC: [-1.4, -0.98, -0.665, -0.56, -0.56, -0.525, -0.28]
cal+0x07DF0: [0.06, 0.06, 0.036, 0.036, 0.036, 0.032, 0.018]
cal+0x07E14: [-0.469, -0.469, -0.402, -0.335, -0.335, -0.335, -0.1675]
cal+0x07E38: [-0.098, -0.098, -0.084, -0.07, -0.07, -0.07, -0.035]
```

Observed facts:

- the whole block is **unchanged** between `BDL` and `EDL`
- it sits directly beside the known LKA/ESA timer cluster
- the values are highly structured and monotonic, not random packed scalars

Best current interpretation:

- a **supervisor/gain/hysteresis block** for the same feature family as the timer region
- likely helper slopes, weights, decay constants, or signed correction factors rather than user-visible gates

New code-backed refinement from Ghidra:

- `context + 0x68` is now proven to be a **mixed continuous-control block**
- reads from `cfg68 + 0x34`, `+0x48`, `+0x4c`, and `+0x5c` are used as fallback gains/limits and filter constants
- the best current fit is that this `0x07D68..0x07E3F` neighborhood, extending through the mixed record at `0x07ADC`, backs that pointer family

Best-fit raw values from the `0x07ADC` neighborhood now tighten that interpretation:

- `base + 0x14 = 0.08726646` (`5 deg` in radians)
- `base + 0x18 = 0.17453292` (`10 deg` in radians)
- `base + 0x34 = 0.7`
- `base + 0x44 = 0.008`
- `base + 0x48 = 36.1111`
- `base + 0x4c = 5.5556`
- `base + 0x54 = 90.0`
- `base + 0x5c = 1.2`
- `base + 0x60 = 5.0`

That is strong enough to describe this family more plainly as:

- a **continuous-control supervisor record**
- with angle-like thresholds, fallback magnitudes, filter poles, and small numerical tuning coefficients

Still unresolved:

- the exact low end of the flash record, because `base + 0x10` is still `0x00010000` rather than a clean float
- the larger byte-table portion of the same runtime record, which is consumed at offsets like `+0x3b7`, `+0x3f0`, `+0x40e`, `+0x822`, and `+0x852`

This is still not fully pinned field-by-field, but it is no longer just a shape guess. See [eps_supervisor_ghidra_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/eps_supervisor_ghidra_trace.md).

---

## Finding 7: Repeated 4x u16 breakpoint-curve family was retuned in EDL

The monotonic u16 curve family appears in multiple variant copies:

```text
BDL:
0x0DA8, 0x2C50, 0x3BA4, 0x4AF8
[0, 51, 66, 78, 100, 135, 182, 240, 307, 387, 479, 582, 735, 897, 1067, 1245, 1434, 1628, 1831]

BDL outlier copy:
0x1CFC
[0, 53, 61, 72, 92, 121, 162, 215, 276, 348, 430, 524, 666, 817, 975, 1145, 1321, 1507, 1704]

EDL:
all copies normalized to
[0, 23, 37, 66, 111, 170, 244, 332, 436, 553, 686, 850, 1026, 1219, 1423, 1645, ...]
```

Observed facts:

- the table is present in **four or five variant copies**
- `EDL` retuned it substantially rather than leaving it alone
- the curve shape is clearly deliberate and non-linear

Best current interpretation:

- this is a **real breakpoint axis** used by active steering logic
- likely tied to authority/rate/assist scheduling rather than a simple on/off threshold

New code-backed refinement:

- `FUN_10055494` is now the concrete context initializer for the surrounding interpolation records
- `FUN_100b8078`, `FUN_100b7918`, `FUN_100b7e96`, and `FUN_100b87ae` prove that neighboring runtime records are used as interpolation-backed limiter, filter, and state-selection schedules

So this family is now stronger than “some monotonic axis”:

- it belongs to the **authority / limiter / filter scheduling side** of the rack, not the feature-arm timer side
- it is exactly the kind of data Ford would retune to soften steering behavior between `BDL` and `EDL`

See [eps_curve_family_ghidra_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/eps_curve_family_ghidra_trace.md).

## Finding 8: separate packed debounce/persistence record feeds the watchdog state machines

Ghidra now proves that a different config pointer, `context + 0x6c`, is consumed as a packed `u16 * 10 ms` timer bundle by:

- `FUN_1005dbc8`
- `FUN_1005ea9c`

That record is **not** the same thing as the mixed `0x07ADC` float/int neighborhood.

Proven behavior:

- low offsets are repeatedly multiplied by `10` and compared against elapsed milliseconds
- the consumers are latch/set/clear state machines, not curve interpolation or continuous control
- the fields control assertion delays, hold windows, retain-last-value windows, and clear timers for multiple supervisor outputs

The most solid per-offset roles are:

- `+0x3a`, `+0x4a`: assert delays for two supervisor event paths
- `+0x3c`: preserve-old-state window after reset
- `+0x46`: delay before another event path is reported
- `+0x4c`: top-level qualify dwell before downstream booleans are allowed to go active
- `+0x50`, `+0x56`, `+0x5c` and two nearby opaque halfword reads: clear/retain timers for four output latches
- `+0x52`, `+0x58` and a sibling opaque halfword read: keep-last-state windows after supervisor reset

This is the clearest proof so far that the rack firmware separates:

1. float/gain/filter supervision
2. debounce/persistence timing
3. lookup-curve scheduling

See [eps_supervisor_ghidra_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/eps_supervisor_ghidra_trace.md) for the code path and function list.

---

## Finding 9: Stable step-threshold family at `cal+0x080C..0x0878`

There is a compact family of small u16 tables:

```text
0x080C: [10, 20, 30, 80, 100, 100, 100, 100]
0x081E: [10, 20, 30, 80, 100, 100, 100, 100]
0x0830: [10, 20, 30, 80, 100, 100, 100, 100]
0x0854: [5, 10, 15, 60, 80, 80, 80, 80]
0x0866: [0, 5, 10, 30, 40, 40, 40, 40]
0x0878: [0, 5, 10, 20, 30, 30, 30, 30]
```

Observed facts:

- tightly grouped
- clearly table-shaped
- **unchanged** between `BDL` and `EDL`

Best current interpretation:

- low-level threshold / gain-step schedules
- possibly used as sibling threshold tables for related modes or trims

Refinement from the latest Ghidra pass:

- the same-offset `fef208xx` path is **not** a clean proof path for these tables
- the live `fef208xx` page is an actively written runtime workspace, not a passive cal mirror
- so the flash tables still look real, but they are probably copied or normalized into another
  gp/context-backed record before use

See [eps_envelope_threshold_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/eps_envelope_threshold_trace.md).

---

## Finding 10: Dense feature-envelope block at `cal+0x0100..0x015C`

This dense float block remains one of the highest-value non-curve cal neighborhoods:

```text
0x0100: 40.0
0x0104: 40.0
0x0108: 250.0
0x010C: 40.0
0x0110: 40.0
0x0114: 10.0
0x0118: 1.0
0x011C: 200.0
0x0120: 10.0
0x0124: 1.0
0x0128: 66.0
0x012C: 50.0
0x0130: 0.004
0x0134: 1.0
0x0138: 1.0
0x013C: 0.3
0x0140: 0.5
0x0144: 8.0
0x0148: 0.05
0x014C: 20.0
0x0150: 20.0
0x0154: 40.0
0x0158: 100.0
0x015C: 85.0
```

Observed facts:

- unchanged between `BDL` and `EDL`
- contains the already-proven engage-speed anchors:
  - `0x0114 = 10.0`
  - `0x0120 = 10.0`
  - `0x0140 = 0.5`
  - `0x0144 = 8.0`
- shaped like a **feature-envelope record**, not a curve family

Best current EPS read:

- `0x0114/0x0120` are still the strongest LKA/LCA minimum-speed gates
- `0x0140/0x0144` still look like APA min/max speed gates
- the adjacent `40/40/250/200/66/50/20/20/40/100/85` values are likely envelope caps, authority limits, or activation/deactivation bounds for sibling steering features
- the small `0.004 / 0.3 / 0.05 / 1.0 / 1.0` values look like gains or hysteresis terms inside the same envelope record

Refinement from the latest Ghidra pass:

- direct same-offset mirror checks for `fef20100..fef2015c` produced **no direct readers**
- the anchor fields `fef20114`, `fef20140`, `fef20144`, and `fef200c4` also have no direct
  readers in the current analyzed image
- so the block still looks like a real EPS feature-envelope neighborhood, but its access path is
  likely indirect through gp/context-backed records rather than plain `fef201xx` globals

See [eps_envelope_threshold_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/eps_envelope_threshold_trace.md).

---

## Finding 11: Direct same-offset `fef2xxxx` mirrors are unreliable for the remaining open blocks

The latest headless pass adds one important structural result:

- `cal+0x0100..0x015C`
- `cal+0x06BA`
- `cal+0x080C..0x0878`

do **not** currently resolve cleanly through a naive same-offset `fef20000 + cal_offset` model.

Observed facts:

- `fef20100..fef2015c`: no direct readers/writers found
- `fef206ba`: no direct readers/writers found
- the `fef208xx` page is heavily used, but as a mutable runtime state/control record rather than a
  passive calibration mirror

Best current EPS read:

- these flash blocks are still probably real calibration
- but they are most likely copied into other gp-backed or context-backed records before use
- future proof work should target the initializer / context path, not more direct same-offset xref hunting

See:

- [eps_envelope_threshold_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/eps_envelope_threshold_trace.md)
- [eps_supervisor_ghidra_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/eps_supervisor_ghidra_trace.md)
- [eps_curve_family_ghidra_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/eps_curve_family_ghidra_trace.md)

---

## Patch strategy for test-today (if signature can be bypassed)

### Aggressive: zero-out all 3 config-block min-speeds
```
cal+0x00C4: 00 00 20 41 → 00 00 00 00
cal+0x0114: 00 00 20 41 → 00 00 00 00
cal+0x0120: 00 00 20 41 → 00 00 00 00
```
Expected effect: LKA (and LCA if 0x0120 is LCA) active at any speed above 0.

### Conservative: reduce to 0.5 m/s (~1 mph)
```
cal+0x00C4: 00 00 20 41 → 00 00 00 3F
cal+0x0114: 00 00 20 41 → 00 00 00 3F
cal+0x0120: 00 00 20 41 → 00 00 00 3F
```
Avoids potential zero-speed divide issues.

### APA speed raise — unclear necessity
User says APA works stock on this truck. No changes needed unless raising the APA ceiling is desired. Candidates to investigate:
- `cal+0x7934` region contains 10.0 alongside 20.0, 40.0 — if one of these is the APA max cap, change it to a higher value.

---

## Confidence summary

| Finding | Confidence | Actionable today? |
|---|---|---|
| F-150 cal is LE (not BE) | HIGH | Yes — this changes every offset interpretation |
| VBF is RSA-signed | HIGH | **Yes — may block all flash patches** |
| 10.0 m/s = LKA min-speed gate | HIGH (pattern + user's 23 mph claim) | Yes if signature OK |
| cal+0x0114 / 0x0120 are the gates | MEDIUM-HIGH (structural pattern) | Test first |
| cal+0x00C4 is a related gate | MEDIUM | Test in combination |
| BDL→EDL timer removals are LKA-related | MEDIUM | EDL already has them zeroed |
| 23-starting curve is a torque breakpoint | HIGH | No patch — not a gate |
| APA speed caps | LOW (not found with certainty) | Investigate more |

---

## Next steps for deeper RE

1. **Verify signature enforcement.** Flash a CRC-only-patched cal and observe SBL response. If it fails at `0x31 RoutineControl` checksum, signature is enforced. If it flashes, proceed with confidence.
2. **Disassemble `ML3V-14D003-BD.VBF` strategy.** Cross-reference which code paths read `0x101D00C4`, `0x101D0114`, `0x101D0120` to confirm they are LKA / LCA / APA gates.
3. **Identify CAN RX handler for `0x3CA` (LKA)** in strategy — the surrounding code will call into a gate-check that reads one of these cal floats.
4. **Check if AS-built configuration has a higher-level enable** that overrides the cal speed gate.
