# FDRS MDX Archive

110 Ford ETIS Runtime `.mdx` diagnostic files extracted from a FDRS
installation, in Ford's proprietary binary serialization format (not
standard Java serialization, not XML).

## Format

Ford ETIS Runtime binary records with type-tagged length-prefixed strings:

- `FC <u8-len> <utf8>` — short string records (≤ 250 chars)
- `FD <u16-be-len> <utf8>` — long string records (≤ 60 KB)

Between string records are numeric fields, reference pointers, and
type markers we haven't fully decoded. The string content is recovered
~completely; the object-graph structural metadata (bit ranges, numeric
scaling, access refs) is not.

Full byte-accurate round-trip deserialization to the XML MDX schema
would require further format RE — not a blocker for our work since the
string content includes every DID name, routine name, DTC description,
enum value, and unit label.

## Layout

- `raw/` — 110 original binary `.mdx` files (~140 MB)
- `extracted/_index.json` — per-file overview (ECU name guess, DID count)
- `extracted/<GNNNNNNN>.mdx.json` — structured per-file extraction
- `extracted/strings/<GNNNNNNN>.mdx.txt` — plaintext record dumps
  (offset `\t` string), 87 MB total, suitable for grep
- `extract_mdx.py` — parser that generated the JSON
- `dump_all_strings.py` — parser that generated the string dumps

## What this bundle covers

The ECU-label auto-detection is unreliable (often picks up a DTC
description rather than the owning ECU). Confirmed findings from
directed search:

| File | Role |
|---|---|
| `G2354864.mdx` | **F-150 family PSCM** (newer version than `DS-ML34-3F964-AE.mdx`). 106 DIDs vs 74. Has additional LKA DIDs: `0xEE08` SPA Quality, `0xEE09` EPS Operation Time, `0xEE24-27` Connected Vehicle Counters, `0xFDB5` TSU torque, `0xFD0x`/`0xFDAx` dual-CPU version IDs. Also new routine `0x3054 Clear Power Steering Lockout Counter`. See `analysis/f150/diagnostics/g2354864_dids.json`. |
| `G1591250.mdx` | Powertrain Control Module (PCM). Contains reference to DS-KK21-11240-AE inside a DID description — NOT the Transit PSCM MDX (despite that part-number hit). |
| `G2158838.mdx` / `G2443680.mdx` | Also F-150-family PSCM-adjacent specs with 11/11 F-150 LKA DID overlap. |

**No Transit-specific PSCM MDX is in this bundle.** The Transit PSCM
diagnostic spec was obtained separately from a VIN-session FDRS dump
and lives at `firmware/Transit_2025/diagnostics/730_PSCM.xml`.

## How to find what you need

```bash
# grep the strings dumps
grep -l "Transit" firmware/_fdrs_archive/extracted/strings/*.txt
grep -l "Power Steering Control Module" firmware/_fdrs_archive/extracted/strings/*.txt
grep "did_330C" firmware/_fdrs_archive/extracted/strings/*.txt
```

```python
# load the index
import json
idx = json.load(open('firmware/_fdrs_archive/extracted/_index.json'))
for e in idx:
    if e['did_count'] > 100:
        print(e['file'], e['ecu_name'])
```

## Re-deriving

To regenerate the extracted artifacts from scratch:

```bash
python3 extract_mdx.py       firmware/_fdrs_archive/raw  firmware/_fdrs_archive/extracted
python3 dump_all_strings.py  # edits paths inline
```

## Provenance

Pulled from a Ford FDRS installation; original FDRS server + tool
required to obtain. Content is Ford Motor Company diagnostic metadata
distributed via the FDRS delivery pipeline. No signatures, encryption,
or DRM — the format is just a custom binary layout not designed for
third-party tools.
