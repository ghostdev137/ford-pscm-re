# Transit — Combined LKA Unlock + APA High-Speed

**File:** `LKA_NO_LOCKOUT_APA_HIGH_SPEED.VBF` (66,915 bytes)
**Vehicle:** 2025 Ford Transit
**Base cal:** `LK41-14D007-AH`
**Flash address:** `0x00FD0000` (65,520-byte cal partition)

## Changes from stock

| Cal offset | Stock (big-endian) | Patched | Meaning |
|---|---|---|---|
| `+0x02DC` | `40 93 33 33` (float 4.6 kph) | `42 48 00 00` (float **50.0 kph**) | APA low-speed ref |
| `+0x02E0` | `41 00 00 00` (float 8.0 kph) | `43 48 00 00` (float **200.0 kph**) | APA max-engage speed |
| `+0x06B0..06C2` | timer table (incl. `03 E8` = 1000 = 10 s at `+0x06B6`) | all zero | LKA arm/re-arm timers |

Everything else identical to stock `LK41-14D007-AH`.

## Verification

- Header `file_checksum`: **0x4771F110** (zlib CRC32, recomputed — verified via re-read).
- `data_format_identifier`: `0x00` (uncompressed).
- Length: 66,915 bytes (same as stock patched files).
- Based on `LKA_NO_LOCKOUT.VBF` you already flashed successfully — identical structure, just the APA bytes added.

## Expected behavior

- **LKA** continuous — no 10-second silence between tug-backs. Same behavior as your current `LKA_NO_LOCKOUT.VBF`.
- **APA** will engage up to ~50 kph (~31 mph) and not abort until 200 kph. Stock was ~3 mph cap.

## Caveats

- Same caveats as `LKA_NO_LOCKOUT.VBF` — disengages from driver-override / hands-off / rate-limit checks in the EPS core remain active.
- APA above parking speed is uncharted territory. The PAM module (`H1BT`) probably won't command large steering inputs at highway speeds since it can't see lane markings — but keep a hand on the wheel during the first few test pulls.
- First-time test: trigger APA at 10-15 mph in an empty lot; confirm it engages where stock would refuse.

## Flash

Standard FORScan → PSCM → Module Programming → Load from file → `LKA_NO_LOCKOUT_APA_HIGH_SPEED.VBF`. Battery maintainer at 13.5-14.0 V. Clear DTCs after.

## Recovery

Revert by flashing stock `firmware/Transit_2025/LK41-14D007-AH.VBF`. Keep that file on your laptop before you start.
