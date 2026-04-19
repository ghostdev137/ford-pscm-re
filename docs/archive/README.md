# Archive

These docs were accurate at the time of writing but have been superseded by current docs. Kept for historical reference.

| File | Superseded by | Reason |
|---|---|---|
| `emulator-notes.md` | `docs/simulator.md` | Rewritten with current status; old version had stale "future work" framing and didn't reflect PC-injection limitation finding |
| `firmware-architecture-transit.md` | `docs/architecture.md` | Merged into updated architecture.md; content was redundant and had some outdated claims |
| `lka-signal-space.md` | `docs/lka.md` + `docs/calibration-map.md` | Agent handoff notes; specific findings folded into canonical docs |
| `openpilot-drive-findings.md` | `docs/lka.md` + drive logs on-device | Per-drive analysis; key findings (torque cap evidence, speed floor) are now in lka.md |
| `pscm-telemetry-observed.md` | (open question) | EPAS_INFO signal decode issues noted; kept here because SteMdule_I_Est decode question unresolved |
| `OVERNIGHT_STATUS.md` | `docs/calibration-map.md` + `docs/lka.md` | Single 2026-04-14 overnight session log; patch coordinates & test results absorbed into canonical docs |
| `can_reader_hunt_state.md` | `docs/transit-arbiter-map.md` | Unresolved 0x3A8 RX-scaling hunt; superseded by the Q15 multiplier patch path at `FUN_010babf2` / `0x010babf8` |
