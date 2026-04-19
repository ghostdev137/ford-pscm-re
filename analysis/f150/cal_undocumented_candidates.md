# F-150 calibration undocumented candidate tables

Source:

- raw cal: `analysis/f150/cal_bdl_raw.bin`
- existing notes: `analysis/f150/cal_findings.md`, `analysis/f150/strategy_findings.md`

This file is a shortlist of **still-underdocumented** candidate tables/blocks worth tracing next.

Recently promoted out of this shortlist:

- the timer/supervisor split is now documented in [eps_supervisor_ghidra_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/eps_supervisor_ghidra_trace.md)
- the interpolation-heavy context records are now documented in [eps_curve_family_ghidra_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/eps_curve_family_ghidra_trace.md)

So the entries below should be read as the remaining open targets, not as a flat list of equally unexplored data.

## 1. Repeated monotonic u16 breakpoint curves

These appear as repeated 4x variant copies and look like real breakpoint tables, not random scalars.

### Candidate A

Offsets:

- `0x0DA8`
- `0x1CFC`
- `0x2C50`
- `0x3BA4`
- `0x4AF8`

Representative values:

```text
[0, 51, 66, 78, 100, 135, 182, 240, 307, 387, 479, 582, 735, 897, 1067, 1245, ...]
```

Why it looks real:

- monotonic increasing
- repeated copies in multiple variant blocks
- non-linear spacing consistent with breakpoints or ramp schedule

Best current guess:

- authority/rate/assist breakpoint axis
- likely shared by LKA/LCA or another steering feature family

### Candidate B

Offset:

- `0x06BA`

Values:

```text
[0, 640, 1920, 3840, 7680, 10240, 12800, 15360, 19200]
```

Why it looks real:

- clean monotonic axis
- regular-ish scale growth

Best current guess:

- fixed-point breakpoint table or speed/angle/rate axis
- direct same-offset `fef206ba` mirror checks produced no users, so it is probably not exposed as a
  plain passive RAM mirror in the current strategy image

## 2. Small repeated u16 tables near 0x0800

Offsets:

- `0x080C`
- `0x081E`
- `0x0830`
- `0x0842`
- `0x0854`
- `0x0866`
- `0x0878`

Representative values:

```text
[10, 20, 30, 80, 100, 100, 100, 100]
[5, 10, 15, 60, 80, 80, 80, 80]
[0, 5, 10, 30, 40, 40, 40, 40]
[0, 5, 10, 20, 30, 30, 30, 30]
```

Why they look real:

- grouped tightly
- multiple sibling shapes
- values look like low-speed/low-angle gates or step schedules

Best current guess:

- family of threshold or gain tables for related states/features
- direct same-offset `fef208xx` xrefs are misleading here: the live `fef208xx` page is a mutable
  runtime workspace, not a passive cal mirror
- these flash tables likely feed another gp/context-backed record instead

## 3. Dense float neighborhood around `0x07D68..0x07E3F`

Representative runs:

### Candidate C

Offset:

- `0x07D68`

Values:

```text
[1.0, 1.0, 0.7, 0.6, 0.5, 0.4, 0.2]
```

### Candidate D

Offset:

- `0x07D88`

Values:

```text
[3.0, 1.5789, 1.2857, 1.1114, 1.0227, 0.8871, 0.8]
```

### Candidate E

Offset:

- `0x07DCC`

Values:

```text
[-1.4, -0.98, -0.665, -0.56, -0.56, -0.525, -0.28]
```

### Candidate F

Offset:

- `0x07DF0`

Values:

```text
[0.06, 0.06, 0.036, 0.036, 0.036, 0.032, 0.018]
```

### Candidate G

Offsets:

- `0x07E14`
- `0x07E38`

Values:

```text
[-0.469, -0.469, -0.402, -0.335, -0.335, -0.335, -0.1675]
[-0.098, -0.098, -0.084, -0.07, -0.07, -0.07, -0.035]
```

Why this whole area looks real:

- multiple adjacent monotonic float runs
- directly adjacent to the known timer neighborhoods:
  - `0x07ADC/0x07ADE`
  - `0x07E64/0x07E68`
- values look like calibrated gains, slopes, or saturations rather than raw flags

Best current guess:

- LKA/LCA/ESA helper gains or hysteresis curves closely related to the timer/state supervisor region

## 4. Dense float block near `0x0100..0x0160`

Representative values:

```text
0x0100: 40.0, 40.0, 250.0, 40.0, 40.0, 10.0, 1.0, 200.0, 10.0, 1.0, 66.0, 50.0 ...
0x0140: 0.5, 8.0, 0.05, 20.0, 20.0, 40.0, 100.0, 85.0, 85.0, 1.0, 1000.0, 30.0 ...
```

Known items in this neighborhood:

- `0x0114 = 10.0`
- `0x0120 = 10.0`
- `0x0140 = 0.5`
- `0x0144 = 8.0`

Why the rest matters:

- this is clearly not four unrelated scalars
- it is a dense parameter block with many still-unmapped floats right next to known engage thresholds

Best current guess:

- engage/disengage/hysteresis/saturation block for LKA/LCA/APA family features
- direct same-offset `fef201xx` mirror checks produced no users across the tested block, so the
  access path is likely indirect through gp/context-backed records

## 5. Suspicious “timer-like” changed table from BDL vs EDL

Already noted in `cal_findings.md`, but still unresolved semantically.

Offsets:

- around `0x1402..0x1416`

Observed change:

- older BDL had repeated `655`
- newer EDL zeroed them

Why it still matters:

- this strongly suggests a deprecated or disabled timer-like table
- it may explain part of Ford’s own lockout behavior changes between revisions

## Recommended next trace order

1. `0x07D68..0x07E3F` float block
2. repeated breakpoint curves at `0x0DA8` / `0x1CFC` / `0x2C50` / `0x3BA4` / `0x4AF8`
3. `0x0100..0x0160` dense engage-parameter block via gp/context records, not same-offset mirrors
4. the `0x080C..0x0878` step-table family via gp/context records, not same-offset mirrors
5. the changed `0x1402..0x1416` timer-like table
