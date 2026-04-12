# F-150 Test Patches — LKA Lockout + Min-Speed

**Target:** 2021 F-150 Lariat 502A BlueCruise (cal `ML34-14D007-EDL`)

## The right framing

- **LKA** (Lane Keep Assist — the tug-back) has a **10-second lockout** on every Ford, including this F-150. That's what we're removing.
- **LCA** (Lane Centering, BlueCruise) is **continuous** — no lockout — so we don't touch it.
- The friend's report of "no 10-sec lockout" was probably describing **LCA/BlueCruise continuous steering**, not LKA behavior.

## ⚠️ Signature enforcement unknown

F-150 cal VBF has a 256-byte RSA-2048 signature + 32-byte SHA trailer. These patches **do not re-sign**. The PSCM's SBL may reject the flash at `0x31 RoutineControl` checksum. Try on a donor/bench module first if available.

## Patch candidates

### `LKA_LOCKOUT_ONLY.VBF` — recommended first try
Two bytes changed:
```
cal+0x07ADC:  10 27  →  00 00   (10000 → 0) — LKA arm timer (10 s → 0)
cal+0x07ADE:  10 27  →  00 00   (10000 → 0) — LKA re-arm timer (10 s → 0)
```
**Rationale:** Two adjacent u16 values both = 10000. At 1 ms/tick this is **exactly 10 s** — the canonical Ford LKA lockout pair (arm + re-arm). Surrounding values look like related control parameters (1500, 300, 257, 3). This pair was **unchanged between BDL and EDL revisions**, consistent with "Ford never relaxes the lockout."

Expected effect: LKA stays active continuously instead of dropping for 10 s after each tug. Min-speed gate (23 mph) remains enforced — test this first to confirm the lockout theory before going broader.

### `LKA_FULL_UNLOCK.VBF` — next step if lockout-only works
Same as above, plus:
```
cal+0x0114:  00 00 20 41  →  00 00 00 00   (10.0 m/s → 0) — LKA engage min-speed
```
**Rationale:** The 10.0 m/s value at `cal+0x0114` is in a structured `[max=200, MIN=10, gain=1, ...]` feature-config block. 10.0 m/s = 22.37 mph ≈ the user-reported "23 mph" LKA min-speed gate.

**Note:** There's a second 10.0 at `cal+0x0120` intentionally left unchanged — suspected LCA engage min-speed, and we don't want to disturb LCA.

### `LKA_AGGRESSIVE.VBF` — if above don't fully unlock
```
cal+0x07ADC:  10 27  →  00 00   (LKA arm timer)
cal+0x07ADE:  10 27  →  00 00   (LKA re-arm timer)
cal+0x07E64:  10 27  →  00 00   (third 10000 in nearby cluster — possibly ESA / TJA / confirmation timer)
cal+0x0114:   00 00 20 41 → 00 00 00 00   (LKA min-speed)
```

## Test plan

1. **Pre-flash:** dump cal PN via UDS `0x22 F10A` — confirm it reads as `ML34-14D007-EDL`.
2. **Flash `LKA_LOCKOUT_ONLY.VBF`** first. Narrowest change. If this gets rejected (signature), stop — the other variants have the same problem.
3. **Drive test:** engage LKA, drift out of lane, feel the tug, then drift again within 10 s. Pre-patch: no response during the lockout. Post-patch: should tug again immediately.
4. If lockout removal works but min-speed gate still blocks you, flash `LKA_FULL_UNLOCK.VBF` and retest below 23 mph.
5. If still gated below 23 mph after the full unlock, the IPMA (camera) is likely refusing to command LKA below threshold — PSCM cal patch alone won't help. That would require IPMA cal mod too (different module, different RE effort).

## Recovery

Keep `firmware/F150_2021_Lariat_BlueCruise/ML34-14D007-EDL.VBF` as the restore file. Flash it back to return to stock.

## Openpilot alternative

If the signature blocks every patch attempt, the cleanest path for openpilot on this truck is:
1. Leave PSCM firmware stock.
2. Filter out the IPMA's `0x213 DesTorq` on CAN at your Panda.
3. Send your own `0x213 DesTorq` + matching `0x3CA LKA active` from openpilot.
4. The PSCM will apply torque as long as its internal LKA state machine accepts the `0x3CA` — you may still hit the 10-s lockout, in which case you need these firmware patches, OR you need to find a way to keep the lockout timer from decrementing via CAN trickery.

Report results at https://github.com/ghostdev137/ford-pscm-re/issues.
