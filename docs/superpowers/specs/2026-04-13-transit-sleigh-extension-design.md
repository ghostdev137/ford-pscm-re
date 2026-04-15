# Transit RH850 SLEIGH Extension — Design

**Date:** 2026-04-13
**Owner:** Ross Fisher
**Target:** Ford Transit 2025 PSCM firmware (`transit_pscm.elf`)

## Problem

Ghidra cannot cleanly decompile the Transit PSCM firmware. Of 2,738 discovered functions, 1,844 (67%) truncate at `halt_baddata()` because the installed stock `esaulenka/ghidra_v850` SLEIGH spec is an incomplete implementation of the Renesas RH850 G3KH ISA. The repo's README explicitly lists "complete RH850 support" as a TODO.

The F150 PSCM (older V850E2 core) decompiles cleanly because stock SLEIGH covers V850E2. Transit uses V850E3 / RH850 G3KH, whose extension opcodes (FPU variants, system-register ops, some bit-manipulation and MPU instructions) are what truncate.

The authoritative ISA reference — `R01US0165EJ0120` (RH850 G3KH User's Manual: Software, rev 1.20, 2017-10-26) — is now on disk at `~/ford-pscm-re/docs/renesas/`. This means we can close the gaps.

## Goal

Extend the installed SLEIGH spec so that Transit PSCM decompiles with <5% function-level truncation, while also covering adjacent RH850 instructions within each manual section so the extension is genuinely useful for other Ford RH850 ECUs (Escape, future Transit revs, body-class PSCMs).

## Non-goals

- Full G3KH ISA completeness. Exotic instructions that no automotive firmware uses are out of scope.
- F150/V850E2 improvements. That path already works.
- Upstreaming to `esaulenka/ghidra_v850`. Local fork only for now; upstream PR is a downstream decision.
- Hand-done RE by the human user. The user does not write SLEIGH; opus-as-reviewer and QEMU cross-reference cover correctness.

## Architecture

Work is split into sequential phases with parallel fan-out inside Phase 2.

```
Phase 0: Cherry-pick         [1 agent, serial]
Phase 1: Gap analysis         ─┐
Phase 1b: Truncation enum     ─┴─ [2 agents, parallel]
Phase 2: SLEIGH authoring    [~6 sonnet agents, parallel, isolated worktrees]
Phase 2b: Opus review         [1 opus agent, serial, reads all NEEDS-OPUS-REVIEW flags]
Phase 3: Integration + test   [1 agent, serial]
Phase 4: Iterate if needed    [targeted agents, as needed]
```

Each Phase-2 agent owns one instruction category and works in its own `git worktree`, producing a self-contained patch against the shared base established by Phase 0. Integration applies patches sequentially with conflict resolution if files overlap.

## Phase detail

### Phase -1 — PDF preprocess (serial, ~5 min)

One agent:
- Converts `~/ford-pscm-re/docs/renesas/REN_r01us0165ej0120-rh850g3kh_MAS_20171026.pdf` to plain text or markdown using `pdftotext -layout` (preserves column structure of opcode tables) and/or `mutool convert -F text`.
- Same for G3MH manual as secondary reference.
- Outputs to `~/ford-pscm-re/docs/renesas/extracted/g3kh_software.txt` with page markers preserved (e.g. `=== page 123 ===`) so agents can still cite manual page numbers.
- Spot-checks the Instruction Set chapter to confirm opcode tables survived extraction readable.

All Phase-2 agents read this extracted text instead of the PDF.

### Phase 0 — Cherry-pick (serial, ~15 min)

One agent:
- Creates working fork at `~/ford-pscm-re/vendor/ghidra_v850_working/` from stock `ghidra_v850_stock` (already cloned).
- Extracts only the non-stub legitimate fixes from the patched backup tarball (`~/ford-pscm-re/backups/ghidra_v850_patched_installed_20260413-180352.tar.gz`): specifically `sttc.sr/stvc.sr` selID 8-31 extensions and the `floorf/mulf` FPU pair definitions.
- Applies as one clean commit. Does NOT carry over the 7 `ext op2126` stub decoders — those get replaced by real decoders in Phase 2.
- Rebuilds the SLA files and verifies they compile.

Output: clean baseline branch at a known commit hash, documented in the repo README of the working fork.

### Phase 1 — Gap analysis (serial, ~15 min; parallel with 1b)

One agent:
- Reads the `.sinc` files in the Phase-0 baseline.
- Catalogs every implemented instruction with its opcode-bit signature, organized by category (arithmetic, load/store, system/special-register, FPU, MPU, bit-manipulation, control-flow, DSP/saturating).
- Output: `~/ford-pscm-re/docs/superpowers/artifacts/sleigh_implemented.md` — structured list per category.

### Phase 1b — Truncation enumeration (serial, ~20 min; parallel with 1)

One agent:
- Runs headless Ghidra on `~/Desktop/Transit_2025_PSCM_dump/transit_pscm.elf` with stock SLEIGH.
- After auto-analysis + function seeding (use `SeedEntries.java` from existing tools), walks every function flagged with "Bad instruction" / `halt_baddata`, extracts the 4 bytes at the truncation address.
- Dedupes 4-byte patterns; for each unique pattern runs manual bit-field decode against the RH850 opcode map (Chapter 4 of manual) to identify the instruction.
- Output: `~/ford-pscm-re/docs/superpowers/artifacts/transit_missing_opcodes.md` — prioritized worklist with (byte pattern → probable mnemonic → count in binary → manual page reference).

### Phase 2 — SLEIGH authoring (parallel, ~30–60 min per agent)

Six sonnet agents dispatched in a single message, each with its own `git worktree` branched from Phase-0 baseline. Categories (final split may shift based on Phase-1 catalog):

1. **System / special registers** (`stc/ldc` variants, `caxi`, `synci`, `snooze`, `cll`, MPU ops, PSW manipulation)
2. **FPU** (single + double precision, conversions, compare variants not already covered)
3. **Bit manipulation + shifts** (`bsh`, `bsw`, `hsw`, advanced immediate shift forms)
4. **Load/store extensions** (`ldl.w`, `stc.w`, `prepare`/`dispose` variants, SP-relative forms)
5. **DSP / saturating arithmetic** (`sat*` family, multiply-accumulate)
6. **Control flow / exceptions** (`rie`, `rmtrap`, `eiret`, `feret`, `ctret`, exception vectors)

Each agent:
- Reads only its assigned manual page ranges via `Read` with `pages:` param (no full PDF reads — the manual is ~700 pages).
- Writes SLEIGH constructors for every gap in its category, prioritizing opcodes from the Phase-1b worklist and covering adjacent instructions in the same manual section.
- Adds a manual-citation comment on every constructor: `// R01US0165EJ0120 §X.Y p.Z`.
- Flags `NEEDS-OPUS-REVIEW` on any constructor that (a) sets CPU flags, (b) raises exceptions, (c) touches MPU or system state, (d) has ambiguous pseudocode in the manual.
- Writes byte-level regression tests: for each new instruction, an input 4-byte sequence, expected disassembly string, expected decompile snippet. Tests live in the agent's worktree at `test/regression/<category>.py`, runnable via headless Ghidra.
- Cross-references QEMU `target/rh850/translate.c` (upstream or contrib) where available; notes any pcode divergence in a comment.
- Pushes branch; produces patch file at `~/ford-pscm-re/docs/superpowers/artifacts/patches/<category>.patch`.

### Phase 2b — Opus review (serial, ~30 min)

One opus agent:
- Reads every `NEEDS-OPUS-REVIEW`-flagged constructor across all patches.
- Cross-checks pcode against manual pseudocode (via `Read` with `pages:`).
- Cross-checks against QEMU source if available.
- Outputs approval / corrections. Corrections get applied back to the authoring agent's patch.

### Phase 3 — Integration + test (serial, ~45 min)

One agent:
- Applies Phase-2 patches in dependency order (system first, then FPU, then others — since later categories may reference pcode from earlier ones).
- Resolves any file conflicts.
- Runs `make SLEIGH=...` to rebuild SLA files. Fixes any SLEIGH compile errors.
- Installs the rebuilt extension to `~/Library/ghidra/ghidra_12.0.4_PUBLIC/Extensions/ghidra_v850/` (backup the existing stock install first).
- Spins up N parallel headless Ghidra instances (N = CPU count) running all byte-level regression tests from all categories.
- Runs full Transit binary auto-analysis + decompile sweep.
- Measures truncation rate: count of `halt_baddata` in new decompile cache vs. stock baseline (67%) and old patched baseline.
- Output: `~/ford-pscm-re/docs/superpowers/artifacts/phase3_report.md` with metrics + list of still-truncating functions.

### Phase 4 — Iterate (as needed)

If truncation >5%:
- Run Phase 1b again against the new build to identify remaining unhandled opcodes.
- Dispatch targeted sonnet agent(s) for the remaining ops.
- Re-integrate.

## Validation layers

1. **Manual citation on every constructor** — forces the agent to reference a specific page, not hallucinate.
2. **QEMU cross-reference** for non-trivial ops — catches semantic drift.
3. **Opus review** for flag-setting, exception-raising, MPU, or ambiguous pseudocode — second independent pass on the risky subset.
4. **Byte-level regression tests** per new instruction — catches regressions during integration.
5. **Full-binary truncation metric** — end-to-end measure: did we actually improve?

## Risk register

- **Silent semantic bugs.** Wrong pcode produces plausible-but-wrong decompiles. Mitigated by layers 2+3+4 above; residual risk remains on unreviewed constructors. Acceptance: the user cannot audit pcode, so we operate under "best effort with diverse validation."
- **SLEIGH compile failures.** A bad constructor can break the whole spec build. Mitigated by isolated worktrees — integration-phase conflicts become local, not catastrophic. A broken patch can be dropped and re-worked without contaminating peers.
- **Extracted-text table mangling.** `pdftotext -layout` on the G3KH manual collapses multi-column tables (notably ADDF.S-style NaN/Inf propagation matrices). These only affect corner-case semantics (NaN propagation, rare exception paths) and land in `NEEDS-OPUS-REVIEW` anyway. Opus falls back to original PDF via `Read pages:` when encountered.
- **G3KH vs G3MH manual drift.** We have both manuals. Agents use G3KH as primary; G3MH only as cross-reference when G3KH is ambiguous.
- **Opcode overlap between categories.** E.g., `stc.w` arguably belongs to both system and load/store. Mitigated by Phase-0 baseline establishing ownership in .sinc files; Phase-2 integration handles any collisions.
- **Transit firmware uses a compiler-specific instruction mix** (Ford uses GHS Green Hills toolchain). Some GHS codegen patterns may be rare in the general RH850 ecosystem. Phase-1b prioritization ensures we target what's actually emitted, not hypothetical coverage.

## Success criteria

- Transit PSCM auto-analysis yields <5% of functions truncating at `halt_baddata`.
- All byte-level regression tests pass.
- F150 PSCM still decompiles cleanly (no regression on V850E2 path) — verified via spot check against existing F150 decompile cache.
- Opus review log shows no unresolved corrections.

## Out of scope (explicit)

- Full publishable G3KH SLEIGH spec with every exotic instruction.
- PR to upstream `esaulenka/ghidra_v850`.
- Dynamic analysis via Unicorn/QEMU. Referenced only as SLEIGH ground truth, not run.
- F150 (V850E2) improvements.
- Changes to Ghidra core or GhidraMCP.

## Deliverables

- `~/ford-pscm-re/vendor/ghidra_v850_working/` — working fork with full commit history
- `~/ford-pscm-re/docs/superpowers/artifacts/` — all intermediate reports and patches
- Installed updated SLEIGH at `~/Library/ghidra/ghidra_12.0.4_PUBLIC/Extensions/ghidra_v850/`
- `phase3_report.md` — truncation-rate delta and remaining gaps
