# F-150 EPS Envelope / Threshold Trace

This note captures the next refinement for the still-underdocumented F-150 calibration blocks:

- the dense feature-envelope block at `cal+0x0100..0x015C`
- the compact step-table family at `cal+0x080C..0x0878`
- the smaller axis candidate at `cal+0x06BA`

The important result from this pass is negative but useful: the easy
`fef20000 + cal_offset` mirror model does **not** explain these blocks cleanly in the
current analyzed image.

## 1. Direct mirror check for `cal+0x0100..0x015C`

I reran the direct-reader checks for the best-known anchors in this block:

- `fef20114` (`cal+0x0114 = 10.0`)
- `fef20140` (`cal+0x0140 = 0.5`)
- `fef20144` (`cal+0x0144 = 8.0`)
- `fef200c4` (`cal+0x00C4 = 10.0`)

Headless Ghidra result from [`F150APASpeedCheck.java`](/Users/rossfisher/ford-pscm-re/tools/scripts/F150APASpeedCheck.java):

```text
=== fef20140 ===
  NO direct readers (may be read via FP register or indirect)

=== fef20144 ===
  NO direct readers (may be read via FP register or indirect)

=== fef20114 ===
  NO direct readers (may be read via FP register or indirect)

=== fef200c4 ===
  NO direct readers (may be read via FP register or indirect)
```

I also scanned the whole `fef20100..fef2015c` neighborhood using
[`F150FindMirrorUsers.java`](/Users/rossfisher/ford-pscm-re/tools/scripts/F150FindMirrorUsers.java).
That produced **zero direct readers and zero writers** for every tested address in the
`0x0100..0x015C` block.

### Plain-English EPS meaning

The envelope block still looks real and important, but the current strategy image is not
accessing it through a simple same-offset RAM mirror.

Best current fit:

- these values are likely copied into a gp-backed or context-backed record before use
- the block still behaves like an EPS feature-envelope record
- the exact access path remains indirect, unlike the more obvious scalar or status globals

### Consequence

This strengthens the earlier warning: for the `0x0100..0x015C` block, raw value semantics
can be inferred structurally, but **same-offset `fef201xx` xrefs are not a valid proof path**
right now.

## 2. What the `fef208xx` region actually is

The step-table candidate family at `cal+0x080C..0x0878` looked at first like another
same-offset mirror candidate:

- `fef2080c`
- `fef2081e`
- `fef20830`
- `fef20854`
- `fef20866`
- `fef20878`

The grouped-reader scan did find live users for those addresses, but the follow-on decompile
shows that these `fef208xx` locations are **mutable runtime workspace**, not passive
calibration mirrors.

### Proven runtime users

- [`FUN_101a5bd6`](/tmp/pscm/f150_lka/dumps/101a5bd6_FUN_101a5bd6.c)
  writes `DAT_fef2080c`
- [`FUN_101a5c4a`](/tmp/pscm/f150_lka/dumps/101a5c4a_FUN_101a5c4a.c)
  is a large supervisor/state-machine function that reads and writes:
  - `DAT_fef20809`
  - `DAT_fef2080b`
  - `DAT_fef2080c`
  - `DAT_fef20828`
  - `DAT_fef20829`
  - plus sibling flags in the same low `fef208xx` page
- [`FUN_10180842`](/tmp/pscm/f150_lka/dumps/10180842_FUN_10180842.c)
  repacks `DAT_fef20800..0f` into `fef212b6..c5`
- [`FUN_1017fda6`](/tmp/pscm/f150_lka/dumps/1017fda6_FUN_1017fda6.c)
  maintains `_DAT_fef2081c` / `DAT_fef2081e`
- [`FUN_10180044`](/tmp/pscm/f150_lka/dumps/10180044_FUN_10180044.c)
  computes `_DAT_fef20830` as a filtered live signal
- [`FUN_10180ca8`](/tmp/pscm/f150_lka/dumps/10180ca8_FUN_10180ca8.c)
  updates `_DAT_fef20850` / `_DAT_fef20854`
- [`FUN_10181270`](/tmp/pscm/f150_lka/dumps/10181270_FUN_10181270.c)
  updates `_DAT_fef20874`, `_DAT_fef20878`, `_DAT_fef2087c`, `_DAT_fef20880`, `_DAT_fef20884`

### Plain-English EPS meaning

The `fef208xx` page is acting like a **live rack-control workspace**:

- mode and supervisor bytes
- filtered intermediate control values
- staged outputs and status bytes
- per-step runtime quantities used by the control chain

That means:

- direct xrefs to `fef2080c` / `fef20830` / `fef20854` / `fef20878` do **not** prove that
  the flash tables at `cal+0x080C..0x0878` are consumed there as same-offset mirrors
- instead, these offsets are being reused in RAM for a dynamic state/control record

## 3. Updated read on the `0x080C..0x0878` flash family

The flash tables are still real-looking:

```text
0x080C: [10, 20, 30, 80, 100, 100, 100, 100]
0x081E: [10, 20, 30, 80, 100, 100, 100, 100]
0x0830: [10, 20, 30, 80, 100, 100, 100, 100]
0x0854: [5, 10, 15, 60, 80, 80, 80, 80]
0x0866: [0, 5, 10, 30, 40, 40, 40, 40]
0x0878: [0, 5, 10, 20, 30, 30, 30, 30]
```

But after this pass the correct interpretation is narrower:

- they still look like threshold / gain-step schedules
- they are still likely EPS calibration data
- **however**, the same-offset `fef208xx` region is not the proof path for them
- they likely feed some other gp-backed or context-backed record, just like the larger
  feature-envelope block

## 4. `cal+0x06BA`

The smaller monotonic axis candidate at `cal+0x06BA` also produced no direct same-offset
users via `fef206ba`.

Current read:

- the table still looks real
- it is probably accessed indirectly or copied into a different runtime record
- it should stay on the open-target list until a consumer is proven

## 5. Best current conclusion

For the remaining unresolved F-150 calibration families:

- `0x0100..0x015C`
- `0x06BA`
- `0x080C..0x0878`

the next useful proof path is **not** more same-offset `fef2xxxx` scanning. The current
image is telling us that these blocks are either:

- copied into gp-backed records before use, or
- normalized into larger context structures whose low offsets overlap live runtime state

That is consistent with the already-proven initializer-driven context model from:

- [eps_supervisor_ghidra_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/eps_supervisor_ghidra_trace.md)
- [eps_curve_family_ghidra_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/eps_curve_family_ghidra_trace.md)
