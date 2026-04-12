---
title: Getting Started
nav_order: 2
---

# Getting Started

A 10-minute read for people new to automotive firmware hacking. If you've reverse-engineered cars before, skip to [architecture](architecture.html) or [lka](lka.html).

## What is this project?

Modern cars are full of small computers (ECUs) running firmware. Ford ships every Transit with the same **steering computer** (the **PSCM** — Power Steering Control Module), but **artificially disables** some of its features via configuration. This repo documents how to change that configuration and turn those features back on.

Three features are in scope:
- **LKA (Lane Keep Aid)** — steers you back when you drift. Ford cripples it with a 10-second lockout after each tug. We fix that.
- **LCA / TJA (Lane Centering)** — keeps you in the lane continuously. Ford disables it entirely on Transit, but the same module has it on the Escape. We explore enabling it.
- **APA (Active Park Assist)** — steers you into a parking spot. Ford caps it at walking pace. We raise the cap.

## What you need to know first

### What's a PSCM?
A small Renesas V850E2M microcontroller bolted to the steering rack. It takes commands from other modules over CAN bus, runs steering motor math, and applies torque to the rack. Firmware lives in flash memory inside this chip.

### What's firmware?
The compiled program running on that microcontroller. For the PSCM, it's roughly:
- **Strategy** — Ford's logic (when to steer, how much, under what conditions).
- **Calibration** — tables of numbers (speed limits, timer values, gain curves) that tune the strategy without changing code.
- **EPS core** — low-level motor control, safety checks.

### What's a VBF?
A file format Ford uses to ship firmware updates. `.VBF` = "Versatile Binary Format." Think of it as a zip file containing one or more chunks of binary, each with a target flash address. See [VBF explained](vbf-explained.html).

### What's CAN?
The communication bus ECUs use to talk to each other. Small messages (8 bytes max in classical CAN) identified by numeric IDs like `0x730`. See [CAN reference](can-ids.html).

### What's UDS?
Unified Diagnostic Services. A standardized protocol running on top of CAN that lets you ask an ECU: "what's your part number?" "read memory at this address." "enter programming mode." "erase flash, I'm about to upload new firmware." See [can-ids](can-ids.html#uds-commands-used).

### What's FORScan?
A Windows app (~$40 extended license) that speaks UDS to Ford modules. It can read DTCs, change AS-built configuration, and — critically — flash firmware. It's what we use to write patched VBFs to the real vehicle.

### What hardware do I need?

| Item | Purpose | Cost |
|---|---|---|
| Ford vehicle (obviously) | Target | |
| FORScan Extended license | Programming software | ~$40/year |
| Ford VCM-II clone **or** TOPDON RLink X3 | J2534 adapter to reach MS-CAN | $60–$200 |
| 12 V battery maintainer | Keep voltage up during flash | $30 |
| Windows laptop | Runs FORScan | |

## The simplest thing you can try

1. Buy/borrow a J2534 adapter.
2. Install FORScan (Extended license trial works for one flash).
3. Download [`LKA_NO_LOCKOUT.VBF`](https://github.com/ghostdev137/ford-pscm-re/blob/main/firmware/patched/LKA_NO_LOCKOUT.VBF) from this repo.
4. Follow the [flashing guide](flashing.html).
5. Drive and feel continuous LKA instead of 10-second dropouts.

That's it — that's the whole "quick win" of this project. Everything else is context, exploration, or advanced work.

## If you want to understand what we did

Read in this order:
1. [Glossary](glossary.html) — vocabulary.
2. [VBF explained](vbf-explained.html) — what a firmware file actually contains.
3. [PSCM architecture](architecture.html) — how the module is laid out internally.
4. [Calibration map](calibration-map.html) — where the magic numbers live.
5. [LKA](lka.html) / [LCA](lca.html) / [APA](apa.html) — what we patched and why.

## If you want to contribute

Read the above, then:
- **Drive the patched firmware and report what happens.** This is the highest-value contribution.
- **Help with LCA.** The AS-built revert mystery needs more eyes. See [lca](lca.html).
- **Fill in the calibration map.** Most of the 65,520-byte cal is still undocumented. See [calibration-map](calibration-map.html).
- **Help get the emulator working.** See [emulator notes](emulator-notes.html).

## Safety / ethics / legal

- Bricking the PSCM means **no power steering** until you replace or recover the module. This is not fine. I have bricked one.
- Out-of-spec firmware on a public-road vehicle is your own legal responsibility. Understand your jurisdiction.
- Ford's disabled features were not enabled because of hardware limitations — they're artificial software gates. That doesn't make bypassing them risk-free.
- **Do not flash to somebody else's vehicle** without their informed consent.

With that said — have fun and report back.
