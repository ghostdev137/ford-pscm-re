# F-150 Test Patches — LKA Min-Speed Gate

**Target vehicle:** 2021 F-150 Lariat 502A BlueCruise
**Base file:** `ML34-14D007-EDL.VBF` (calibration)

Three candidate patches targeting what we believe is the LKA minimum-speed gate at **10.0 m/s = 22.37 mph ≈ 23 mph** in the PSCM calibration. See [`analysis/f150/cal_findings.md`](../../../analysis/f150/cal_findings.md) for full RE.

## ⚠️ WARNING — Signature likely enforced

Unlike Transit PSCM, the F-150 PSCM cal VBF has a 256-byte RSA-2048 signature and 32-byte SHA trailer. **These patches do not re-sign the file.** There's a non-trivial chance the PSCM's SBL will reject the flash. Flash only with:

1. Full backup of the stock `ML34-14D007-EDL.VBF` on hand.
2. Understanding that the module may brick if signature is checked mid-flash.
3. VCM-II or TOPDON RLink + FORScan Extended.
4. A plan for module replacement/recovery if it bricks.

Try on bench/donor module before vehicle flash if possible.

## The three patches

| File | Cal offsets patched | New value | Aggressiveness |
|---|---|---|---|
| `LKA_MIN_SPEED_ZERO_PAIR.VBF` | `+0x0114`, `+0x0120` | 0.0 m/s | **Recommended first try** — narrowest change |
| `LKA_MIN_SPEED_ZERO.VBF` | `+0x00C4`, `+0x0114`, `+0x0120` | 0.0 m/s | Broader — zeros one more scalar |
| `LKA_MIN_SPEED_HALF.VBF` | `+0x00C4`, `+0x0114`, `+0x0120` | 0.5 m/s (~1 mph) | Safer if zero causes divide-by-zero DTCs |

## What we expect each patch to do (if LKA min-speed hypothesis is correct)

- **LKA engages at any vehicle speed** (above 0 or above 0.5 mph).
- **Possibly LCA too** if `0x0120` is the LCA gate (the config block structure suggests it is).
- **APA behavior should be unchanged** (APA-specific thresholds look to be elsewhere in cal, `cal+0x7xxx` region).

## What we do NOT know

- **Whether flashing will succeed given the signature.** Try it.
- **Which offset is LKA specifically vs LCA** — the `0x0114`/`0x0120` pair is almost certainly two separate gates, but we don't know which is which without strategy disassembly or live testing.
- **Whether there are upstream gates** (IPMA refuses to command LKA below 23 mph, regardless of PSCM cal). If that's the case, patching the PSCM cal alone won't help — the IPMA would also need to be unlocked.

## After flashing

1. Clear DTCs in FORScan. Check for any persistent P/C codes.
2. Drive at low speed (5–15 mph) in a lane-marked empty lot or quiet road.
3. Engage LKA via dash switch. Try to drift out of the lane.
4. **Expected:** steering tug applied even below 23 mph.
5. **Fail mode A:** nothing happens below 23 mph → PSCM rejected patch OR IPMA gates it → check UDS DID F188 on PSCM (should report the cal PN).
6. **Fail mode B:** DTCs, no steering → revert immediately to stock.

## Reverting

Keep `firmware/F150_2021_Lariat_BlueCruise/ML34-14D007-EDL.VBF` as your restore file. Flash it back to return to stock.

## Report back

File issues at <https://github.com/ghostdev137/ford-pscm-re/issues> with:
- Which patch file was tried
- Flash result (succeeded / rejected at which stage)
- Test drive result
- Any DTCs observed
