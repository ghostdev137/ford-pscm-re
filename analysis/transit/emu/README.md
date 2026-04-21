# Transit emulation — status + limits

Adaptation of the F-150 Unicorn harness to Transit (`tools/unicorn_transit_override_harness.py`).

## What works

- Full Transit AH firmware load: strategy @ `0x01000000`, cal @ `0x00FD0000`, block2 ext @ `0x20FF0000`, ram_init @ `0x10000400`
- Runtime memory map: lowmem, stack/EP window, `0xFEF00000` RAM, peripherals, SYSIO, CAN SFRs
- Execution starts and block hooks fire
- Baseline V850 instructions decode and execute correctly
- Example: `FUN_010B4AD4` (LCA dispatcher) runs 2 blocks cleanly before hitting an extension opcode

## What doesn't work

Unicorn-pr1918 RH850 doesn't decode all **V850E2M extension opcodes** that Transit PSCM uses. Failure modes observed:

1. **CPU exception at extension opcode.** Example: `FUN_010BABF2` (angle scaler, `mulhi 0x67c2`) throws `UC_ERR_EXCEPTION` at `0x010BAC20` (after 5 blocks). The failing halfword is an extension arithmetic op.
2. **Translation hang.** Example: LCA dispatcher at `0x010B4AD4` executes 2 blocks, then Unicorn gets stuck in TCG translation on halfword `0x7355` at `0x010B4B94`. Requires `timeout` on `emu_start` to unjam.
3. **First-instruction failure for many functions in the `0x010B4xxx-0x010B8xxx` override-candidate range.** All 4 indexed functions scanned (`010B4262`, `010B4336`, `010B43EC`, `010B4510`) fail at block 1.

This matches the documented finding in `analysis/f150/angle_scale_patch.md`:

> Ghidra 12 ships with a working V850 processor spec for baseline V850 only.
> When it hits an RH850 extension opcode, it fails to decode that instruction...
> Transit PSCM runs RH850-extended.

The same decoder gap that limits Ghidra on Transit limits Unicorn-pr1918 on Transit.

## Implications for override-hunting

Static sweeping via Unicorn — the approach that proved `_DAT_fef263de` on F-150 — is **not viable** on Transit without either:

- a patched Unicorn/SLEIGH decoder with V850E2M extensions (multi-day work), OR
- a different emulator.

## Alternative paths

### 1. Athrill2 (V850E2M)

The repo has `simulator/athrill/` scaffolding targeting Transit. Build script references `/tmp/athrill-ford` paths and WSL (`/mnt/c/`). Would need a macOS port or Docker wrapper. Athrill's V850E2M decoder is more complete than Unicorn's.

### 2. BN-based execution via bn-v850 arch

Per `transit_pscm_lifter_sprint_2026_04.md`, the Binary Ninja v850 lifter was rewritten during the April sprint, with 99.81% coverage on Transit linear decode. A BN-scripted emulator (iterated via IL execution) could cover the extension opcodes BN now decodes.

### 3. Drive-test empirical bisect

Patch a candidate threshold in Transit cal (guided by F-150 offsets as a first-approximation landmark), flash, drive known-failing curve, observe. Less scientific than emulator sweep, but doesn't require emulation of extensions.

### 4. Static pattern-match using F-150 signature

Scan Transit strategy for functions matching the F-150 `FUN_101a3b84` fingerprint:
- reads 3+ absolute global addresses
- compares status byte against `3` and `5`
- multi-stage structure (quiet gate → rate → band → persist → final state)

Per `analysis/transit_disasm/rd_coverage.json`, current Transit disasm coverage may be high enough to grep the decomposition corpus. The indexed function count in `index.tsv` is 1687 — sparse relative to the ~4000 true functions, but targeted grep against the raw bytes could find candidates.

## Files

- `tools/unicorn_transit_override_harness.py` — harness (partial — emulates baseline V850 only)
- `analysis/transit/emu/scan_emulatable.py` — scanner against the disasm index
- `analysis/transit/emu/emulatable.csv` — outcomes (all 4 candidates failed at block 1)

## Bottom line

The emulator loads Transit firmware and executes baseline V850 instructions. Extension opcodes — which are widespread in Transit's LKA control logic — cause hangs or exceptions. The F-150 emulator-driven threshold-proof technique does not transfer to Transit in its current form. Path forward is either Athrill, a BN-driven emulator, or drive-test bisect.
