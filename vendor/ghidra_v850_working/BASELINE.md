# Transit RH850 SLEIGH Extension — Baseline

Phase 0 of the multi-agent project to extend `esaulenka/ghidra_v850` so Ford
Transit PSCM firmware (Renesas V850E3 / RH850) decompiles cleanly in Ghidra.

## Source

- **Upstream**: `esaulenka/ghidra_v850`
- **Forked from commit**: `14c1b5be32b8ec741ee626c8bca9885c58f7a473` ("rotl fix #41")
- **Branch**: `transit-rh850-extension`
- **Date**: 2026-04-13

## Cherry-picked (kept)

Source tree: `tools/ghidra_v850_patched` (commit `ef3ec08`, patch
`0001-Extend-sttc.sr-stvc.sr-selID-8-31-fix-floorf-mulf-re.patch`).

1. **`data/languages/v850_float.sinc`** — three FPU register-pair fixes so
   Ghidra does not error on odd register indices:
   - `cmovf.d` — drop `R1115pair`/`R0004pair` on the inputs, sext to 64-bit
     inside the semantics.
   - `floorf.duw` and `floorf.dw` — drop `R1115pair` on the input; single-
     precision input is correct per RH850 ISA.
   - `mulf.d` — drop input pairs, sext in the body; output stays paired.
2. **`data/languages/v850e3.sinc`** — extend `sttc.sr` and `stvc.sr` selID
   coverage from 0–7 to 0–31 (the existing `SR0004_[9a-f]` attach tables are
   already defined in stock; selIDs 8, 13 and 16–31 fall through to raw
   `R0004`). Constructors remain `unimpl` — behavior parity with the stock
   selID 0–7 entries. Adds 25 `sttc.sr` + 24 `stvc.sr` constructors.

Total: 2 files, +63 / −9 lines.

## Discarded

Intentionally NOT carried over from the patched backup:

1. **All `unk_op*` and `unk_opNN_xxx` stub decoders** (approx. 80 entries,
   latter portion of the same `0001-Extend-...` patch plus the separate
   `0001-Raise-Transit-RH850-clean-decompile-to-78-via-stub-o.patch`).
   These cover op2126 groups 0x01, 0x02, 0x07, 0x08–0x10, 0x11, 0x13, 0x15–0x17,
   0x1B, 0x20–0x2F, 0x30, 0x33–0x36, 0x38, 0x3A–0x3F with pure `unimpl`
   constructors. They force truncation at the first matching byte pattern and
   prevent real decoders from being written later. These will be *replaced*
   with real decoders in subsequent phases.
2. **`v850_arithmetic.sinc` / `v850_load_store.sinc` case normalization**
   (second patch, `0001-Raise-Transit-...`) — cosmetic `r1115` → `R1115`
   renames bundled with the stub pile. Not needed; stock compiles cleanly.
3. **`*.sinc.bak` files** created by that second patch — build noise.

No ambiguous hunks were encountered: the kept set is exactly the FPU pair
fixes and the sttc/stvc selID table extensions; everything else in the two
prior patches is either cosmetic or a truncating stub.

## Build

```
cd /Users/rossfisher/ford-pscm-re/vendor/ghidra_v850_working
make SLEIGH=/opt/homebrew/Cellar/ghidra/12.0.4/libexec/support/sleigh
```

As of 2026-04-13 this produces:
- `data/languages/v850e2.sla` — 30,174 bytes
- `data/languages/v850e3.sla` — 45,411 bytes

Only warning is `N NOP constructors found` (24 for e2, 26 for e3), expected
for the many stock `unimpl` constructors.

## Not yet done

- No install to `~/Library/ghidra/.../Extensions/`. Integration with a Ghidra
  install is a later phase.
- No real decoders for the discarded op2126 groups; those are the target of
  later phases.
