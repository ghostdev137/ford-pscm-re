# F-150 PSCM Cal RE — Findings (2021 Lariat 502A BlueCruise)

**Source:** `firmware/F150_2021_Lariat_BlueCruise/ML34-14D007-EDL.VBF`
**Compared against:** `firmware/F150_2022/ML34-14D007-BDL` (older revision)
**Cal data:** 195,584 bytes, flashes to `0x101D0000`
**Endianness:** **little-endian** (u16 and float32) — different from Transit/Escape which are big-endian

---

## ⚠️ CRITICAL: F-150 VBF is RSA-signed

Unlike the Transit/Escape PSCM (CRC-only checks), the F-150 VBF has a **256-byte RSA-2048 signature + 32-byte hash trailer** after the block data. `file_checksum` in the header is not a CRC32 of the data.

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

## Finding 2: BDL→EDL changes reveal Ford's tuning philosophy

Diffing the newer `EDL` against older `BDL` cal (both 195,584 bytes):
- **2,782 byte-level diffs** organized into **67 regions**
- Most changes appear in **4 identical copies** spaced ~0xF00 apart — Ford uses four variant calibrations (trim-dependent or profile-dependent)

### Key diff: `cal+0x1402..0x1416` — EDL **zeroed** a timer table
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
