# Patched V850 / RH850 SLEIGH for Ghidra 12

Fork of [esaulenka/ghidra_v850](https://github.com/esaulenka/ghidra_v850) patched
to raise clean-decompile rate on Ford Transit 2025 PSCM (RH850) from
42% → **90%** on a 100-function sample.

## Changes

1. **Case fix** in `loop` (`v850e3.sinc`): `r0004` → `R0004` matching attach table.
2. **Stub decoders** for 7 undocumented RH850 ext ops (`op2126 = 0x03, 0x0A, 0x0D,
   0x31, 0x32, 0x37, 0x39`). Covers ~660 Transit instances that previously
   triggered `halt_baddata()`.
3. **Extended `sttc.sr`/`stvc.sr`** for selID 8–31 (was 0–7 only).
4. **FPU register-pair fix** (`v850_float.sinc`): `floorf.dw`, `floorf.duw`,
   `mulf.d` now use plain `R1115`/`R0004` instead of `*pair` forms.
5. **Register-field casing fixes** across several .sinc files.

## Install

```bash
cp -r tools/ghidra_v850_patched ~/Library/ghidra/ghidra_<VERSION>_PUBLIC/Extensions/ghidra_v850
cd tools/ghidra_v850_patched
$(brew --prefix)/Cellar/ghidra/*/libexec/support/sleigh data/languages/v850e2.slaspec
$(brew --prefix)/Cellar/ghidra/*/libexec/support/sleigh data/languages/v850e3.slaspec
```

Restart Ghidra. Language `v850e3:LE:32:default` appears in the picker — use
that for Transit 2025 PSCM (RH850) firmware.

## Impact

| Processor spec | Clean decompile |
|---|---|
| Stock Ghidra 12 V850 | 0 / 48 |
| esaulenka baseline | 42 / 100 |
| **This patch** | **90 / 100** |

Remaining 10 failures are `jr` tail-calls to flash banks we don't load (not
SLEIGH bugs).

## Reproduce

```bash
$(brew --prefix)/Cellar/ghidra/*/libexec/support/analyzeHeadless /tmp/proj TestRun \
  -import /path/to/transit_AH_blk0_0x01000000.bin \
  -loader BinaryLoader -loader-baseAddr 0x01000000 \
  -processor "v850e3:LE:32:default" \
  -scriptPath ../scripts \
  -postScript ProbeWithSeed.java -deleteProject \
  2>&1 | grep RESULT
```

## Patches

- `0001-Raise-Transit-RH850-clean-decompile-to-78-via-stub-o.patch` — stubs + case fixes (42%→78%)
- `0001-Extend-sttc.sr-stvc.sr-selID-8-31-fix-floorf-mulf-re.patch` — sttc/stvc + FPU (78%→90%)

Original: [esaulenka/ghidra_v850](https://github.com/esaulenka/ghidra_v850) (MIT).
