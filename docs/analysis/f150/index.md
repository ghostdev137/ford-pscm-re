---
title: F-150 Analysis
nav_order: 1
parent: Home
---

# F-150 PSCM Analysis

Published summary pages for the 2021 F-150 BlueCruise PSCM reverse-engineering work.

These pages are the GitHub Pages entrypoint for the deeper repo notes under `analysis/f150/`.

## Start here

- [Plain-language calibration map](cal-plain-language-map.html)
- repository note: `analysis/f150/lka_path_findings.md` for the canonical `LKA` path walkthrough
- repository note: `analysis/f150/lca_path_findings.md` for the canonical end-to-end `LCA / BlueCruise` path walkthrough
- repository note: `analysis/f150/apa_path_findings.md` for the canonical `APA` path walkthrough

## What this section covers

- lockout / re-arm timing behavior in the rack supervisor
- feature gates like LKA/LCA/APA speed envelopes
- DBC/message-level ownership for `LKA`, `LCA/BlueCruise`, `ESA`, `APA`, and shared PSCM feedback
- steering authority / limiter curve families
- driver-override threshold and hysteresis logic

## Source notes in the repo

The full proof notes still live in the repository under `analysis/f150/`, including:

- `cal_findings.md`
- `strategy_findings.md`
- `driver_override_findings.md`
- `eps_dbc_message_trace.md`
- `lka_path_findings.md`
- `lca_path_findings.md`
- `apa_path_findings.md`
- `lka_timer_ghidra_trace.md`
- `eps_supervisor_ghidra_trace.md`
- `eps_curve_family_ghidra_trace.md`
- `eps_envelope_threshold_trace.md`

The published Pages section is meant to be the readable front door; the repo-root notes remain the detailed working set.
