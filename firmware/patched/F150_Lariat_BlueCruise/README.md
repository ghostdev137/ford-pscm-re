# F-150 Lariat BlueCruise — Patched Cal VBFs

**Target vehicle:** 2021+ Ford F-150 Lariat 502A with BlueCruise
**Stock base file:** [`ML34-14D007-EDL.VBF`](../../F150_2021_Lariat_BlueCruise/ML34-14D007-EDL.VBF)
**PSCM flash addr for cal:** `0x101D0000`

All 6 VBFs below have **valid CRC32 file_checksum** (verified — the header's `file_checksum` is a standard zlib CRC32 over everything after the ASCII header; our patcher recomputes it correctly).

## Is the F-150 VBF signed? — direct comparison with the Transit that already flashed

**Transit PSCM (known to flash fine with CRC-only patches):**
- `file_checksum` is a **zlib CRC32** over `block_header + data`.
- **No trailer.** File ends immediately after the cal data.
- Patching: change bytes, recompute CRC32, flash. Confirmed working — the author's Transit has been running `LKA_NO_LOCKOUT.VBF` built this way since 2026-04-11.

**F-150 PSCM (unknown — untested):**
- `file_checksum` is the **same zlib CRC32** algorithm (confirmed — see the CRC breakthrough below).
- **But the F-150 adds a 296-byte trailer** after the cal data, structured as:
  - ~248 bytes of high-entropy content (likely RSA-2048 signature)
  - 12 bytes of block-header repeat
  - 32 bytes of hash (likely SHA-256 variant)
- **Trailer is content-dependent.** Comparing the BDL (older) and EDL (newer) cal trailers: only **14 / 296 bytes match** — the trailer is computed from the cal content, it's not fixed padding or a manufacturing timestamp. That's the fingerprint of a crypto signature + hash.

**So here's the honest answer:**

1. These patches will **pass the CRC32 `file_checksum` check** that the SBL certainly runs during flashing.
2. **Whether the SBL also verifies the trailer signature is unknown until someone tries.** We cannot recompute it — no Ford signing key.
3. If Ford added this trailer purely for manufacturing traceability (not actively verified by the module), the patches flash and work.
4. If the SBL verifies it at `0x31 RoutineControl` checksum routine, the patches get rejected and the flash aborts cleanly (no brick — the SBL just refuses to commit).
5. If the SBL accepts but the PSCM boot ROM verifies the trailer at next power-cycle, the module could refuse to boot or fall back to a previous cal.

Given the risk, **bench/donor module test is the right first step.**

### Full verification layers table

| Verification layer | What it is | Enforced by | Recomputed in our patches? |
|---|---|---|---|
| `file_checksum` in ASCII header | zlib CRC32 of (block header + name tag + data + trailer) | SBL during flash | ✅ Yes |
| Per-block CRC16-CCITT (Transit-style) | Not used on F-150 cal | — | N/A |
| 256-byte RSA-like signature (in trailer) | High-entropy blob, likely RSA-2048 over a digest | Possibly by PSCM boot ROM; unknown if enforced at flash time | ❌ No (cannot, without Ford key) |
| 32-byte SHA-256 hash (last 32 bytes) | Hash — algorithm unclear (not stock SHA-256 of any obvious region) | Possibly by SBL | ❌ No (unknown what it covers) |

**All four F-150 VBF types** (cal `DATA`, supplementary `DATA`, strategy `EXE`, bootloader `SBL`) have the same ~300-byte trailer structure. This means the **RSA signature layer is present on every file**, not just cal.

### What's likely to happen when flashing

**Optimistic case:** SBL only checks CRC32 `file_checksum` and the 32-byte hash doesn't cover the patched region. Flash succeeds, patch takes effect.

**Likely case:** SBL checks CRC32 (passes) but also verifies the 32-byte hash or RSA signature → flash **rejected** at `0x31 RoutineControl` step.

**Worst case:** Flash succeeds but PSCM boot ROM rejects the cal at next power-cycle → module goes to safe mode / DTCs / needs stock reflash.

There is no way to know without trying. **Test on a donor/bench module before doing it on a driveable vehicle.**

## Files

### LKA-focused (remove 10-second lockout ± min-speed gate)

| File | Size | Changes | When to try |
|---|---|---|---|
| `LKA_LOCKOUT_ONLY.VBF` | 197,409 | `cal+0x07ADC` 10000→0, `cal+0x07ADE` 10000→0 (LKA arm + re-arm timers) | **First try.** Narrowest change, highest chance of flashing cleanly. |
| `LKA_FULL_UNLOCK.VBF` | 197,409 | + `cal+0x0114` 10.0→0.0 (LKA engage min-speed ~22 mph) | If lockout removal works but LKA still won't engage below 23 mph. |
| `LKA_AGGRESSIVE.VBF` | 197,409 | + `cal+0x07E64` 10000→0 (third related timer) | Last-resort LKA unlock. |

### APA-focused (raise speed cap)

| File | Size | Changes | Effect |
|---|---|---|---|
| `APA_HIGH_SPEED.VBF` | 197,409 | `cal+0x0144` 8.0→80.0 | Single scalar change. APA engages up to ~50 mph if unit is kph. |
| `APA_UNLOCK.VBF` | 197,409 | `cal+0x0140` 0.5→0.0 (min), `cal+0x0144` 8.0→200.0 (max) | APA engages at any speed. Higher risk of PAM-side refusal. |

### Combined

| File | Size | Changes |
|---|---|---|
| `LKA_AND_APA_UNLOCK.VBF` | 197,409 | LKA lockout (2 timers) + LKA min-speed + APA max — one-shot everything |

## Why each change was chosen — cal offsets and rationale

### `cal+0x07ADC` / `cal+0x07ADE` — LKA lockout timer pair (HIGH confidence)

```
cal+0x07ADC:  10 27  = u16 LE 10000 = 10,000 ms = 10 s  (arm timer)
cal+0x07ADE:  10 27  = u16 LE 10000 = 10,000 ms = 10 s  (re-arm timer)
```

Two adjacent u16 values both equal to 10000 in a mixed float/int region surrounded by related control parameters (1500, 300, 257, 3). This is the classic Ford LKA arm/re-arm pair — 10 seconds each is the canonical lockout duration across the entire Ford lineup. Unchanged between the older `BDL` and newer `EDL` cal revisions, consistent with Ford never relaxing the lockout. Zeroing both to `0000` should eliminate the 10-s silence between LKA interventions.

### `cal+0x0114` — LKA engage minimum speed (MEDIUM-HIGH confidence)

```
cal+0x0114:  00 00 20 41  = float32 LE 10.0  (m/s → 22.37 mph ≈ user-reported 23 mph)
```

Lives in a structured feature-config block `[max=250, max=40, max=40, MIN=10, gain=1, max=200, ...]` — canonical `[max, MIN, gain, max, MIN, gain]` layout for two separate speed gates. The second gate at `cal+0x0120` is **left untouched** (suspected LCA/BlueCruise engage min — LCA works correctly, don't disturb).

### `cal+0x0144` — APA engage maximum speed (HIGH confidence)

```
cal+0x0144:  00 00 00 41  = float32 LE 8.0  (likely kph — matches Transit's APA cap pattern)
```

In a feature-config block `[min=0.5, MAX=8.0, step=0.05, 20.0, 20.0, 40.0, 100.0, ...]`. Transit PSCM has its APA cap at the same value `8.0` in a similar block (big-endian, at `cal+0x02E0`). F-150 uses little-endian at `cal+0x0144`. Same pattern, same value → same meaning.

Raising to 80.0 (HIGH_SPEED variant) or 200.0 (UNLOCK variant) should let APA engage at higher speeds. Note: the PAM module (Park Assist Module) may refuse to command APA above a threshold regardless of PSCM cal — in which case patching PSCM alone doesn't help.

## How to flash

1. **Read the current cal PN** via FORScan → PSCM → ReadByIdentifier `0xF10A` (or `0xF188`). Confirm it reports `ML34-14D007-EDL`. If it says something else, **do not flash these files** — they are only valid for this specific revision.
2. **Backup:** confirm `firmware/F150_2021_Lariat_BlueCruise/ML34-14D007-EDL.VBF` (stock) is on your laptop as your restore file.
3. **Battery maintainer on.** 13.5–14.0 V.
4. **FORScan** → Service → Module Programming → PSCM → Load from file → select one of the `.VBF` files in this folder.
5. Watch for `0x31 RoutineControl` checksum step. If it fails there, the signature layer rejected the patch — stop, move on.
6. If flash succeeds, clear DTCs, power-cycle, drive and test.

## How the patches are made — for your own variants

Use `tools/vbf_patch_f150.py`:

```bash
# Example: zero the LKA lockout pair only
python tools/vbf_patch_f150.py \
    firmware/F150_2021_Lariat_BlueCruise/ML34-14D007-EDL.VBF \
    firmware/patched/F150_Lariat_BlueCruise/MY_PATCH.VBF \
    --patch 0x07ADC:0000 \
    --patch 0x07ADE:0000
```

The tool verifies the stock CRC32 first, applies your patches, and writes out a new file with a recomputed `file_checksum`. It does **not** touch the RSA signature trailer — that's not possible without Ford's signing key.

## Report results

Open an issue at <https://github.com/ghostdev137/ford-pscm-re/issues> with:
- Which patch file
- Flash outcome (succeeded / rejected at which step)
- Test drive result
- Any DTCs (especially `C` or `B` codes on PSCM)
