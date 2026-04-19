# F-150 LKA timer trace from Ghidra

**Target:** `firmware/F150_2021_Lariat_BlueCruise/f150_pscm_full.elf`  
**Method:** headless Ghidra trace on the saved `F150TimerOffsets` project  
**Status:** function-level behavior is now explicit; exact flash offset for the backing config struct is still not fully pinned

## What Ghidra proves

The "10 second LKA timer" on this image is not one naked compare in the main LKA controller.  
It sits inside a smaller 4-state helper rooted at:

- `FUN_10091a9c`
- `FUN_1009189c`
- `FUN_1009158c`
- `FUN_10091612`
- `FUN_100916de`
- `FUN_1009174c`
- `FUN_100917bc`
- `FUN_10091820`

The timer helpers operate on three timer handles:

- `0xfebf4394` via `gp-0xd5f0`
- `0xfebf4390` via `gp-0xd5f4`
- `0xfebf438c` via `gp-0xd5f8`

The timebase helpers are:

- `FUN_10090518`: current time in **milliseconds**, computed from the 8 kHz free-running tick
- `FUN_10090586(start, out)`: `out = now_ms - start`, so this is **elapsed milliseconds**

That part is explicit in decompile:

```c
void FUN_10090518(uint32_t *out_ms) {
    ticks64 = HW_COUNTER64();
    *out_ms = (int)((double)ticks64 / 8000.0);
}

void FUN_10090586(int start_ms, int *out_elapsed_ms) {
    FUN_10090518(local_now);
    *out_elapsed_ms = local_now[0] - start_ms;
}
```

## The config fields the state machine actually reads

The timer/state logic does **not** read the `fef264xx` thresholds used by `FUN_101a3b84`.

Instead it dereferences:

- `context = *(gp - 0x1574c)`
- `cfg = *(context + 0xa4)`

Then it reads these fields from `cfg`:

- `cfg+0x1c` as `float`
- `cfg+0x28` as `float`
- `cfg+0x34` as `float`
- `cfg+0x40` as `float`
- `cfg+0x48` as `u8`
- `cfg+0x49` as `u8`

The key timer fields are the two bytes at:

- `cfg+0x48`
- `cfg+0x49`

Those are scaled as:

```c
timeout_ms = cfg_byte * 10000;
```

So a byte value of `1` means **10.0 s**.

## Exact timer behavior

### 1. `FUN_1009158c` - fixed 10 s auxiliary window

This helper gates one branch of the state machine using a hard-coded 10-second threshold:

```c
if (secondary_mode != 0 &&
    current_metric <= cfg->f_1c &&
    abs(scaled_short) <= cfg->f_40 &&
    status_byte != 3) {
    elapsed_ms = now_ms - timer_4394_start;
    out = (elapsed_ms < 0x2711);   // < 10001 ms
} else {
    out = 1;
    reset_timer_4394();
}
```

So this branch uses a **fixed** `10001 ms` grace/qualification window.

### 2. `FUN_10091612` - two per-state configurable timers

This helper uses the current substate byte at `gp-0xc4f4` and evaluates two independent timers:

```c
if (current_substate == 2) {
    elapsed_ms = now_ms - timer_4390_start;
    state2_timeout = (cfg->u8_49 * 10000) < elapsed_ms;
} else {
    state2_timeout = 0;
    reset_timer_4390();
}

if (current_substate == 1) {
    elapsed_ms = now_ms - timer_438c_start;
    state1_timeout = (cfg->u8_48 * 10000) < elapsed_ms;
} else {
    state1_timeout = 0;
    reset_timer_438c();
}
```

So:

- `cfg+0x49` is the timeout for **substate 2**
- `cfg+0x48` is the timeout for **substate 1**

And both are in **10-second units**

## The 4-state machine that uses them

`FUN_1009189c` dispatches by current substate `DAT_febf5491`:

- substate `0` -> `FUN_10091820`
- substate `1` -> `FUN_100916de`
- substate `2` -> `FUN_1009174c`
- substate `3` -> `FUN_100917bc`

The upstream inputs are:

- `primary_mode` = sanitized byte from `gp-0x15049`
- `secondary_mode` = sanitized byte from `gp-0x150c3`
- `entry_gate` from `FUN_100914fc`
- `aux_window_flag` from `FUN_1009158c`
- `state1_timeout` / `state2_timeout` from `FUN_10091612`

### Substate 0: `FUN_10091820`

Entry conditions:

- if `primary_mode in {2,3,5}`
- and `current_float < cfg->f_34`
- and `entry_gate == 0`
- then enter **substate 1**

Alternate entry:

- if `primary_mode == 0`
- and `current_float < cfg->f_34`
- and `entry_gate == 0`
- then enter **substate 2**

### Substate 1: `FUN_100916de`

Transitions:

- if `state1_timeout == 1` and `primary_mode in {0,3}` -> advance to **substate 2**
- else if `primary_mode == 1` -> collapse to **substate 0**
- else if `aux_window_flag != 0` -> collapse to **substate 0**
- else if `current_float > cfg->f_34` -> collapse to **substate 0**

### Substate 2: `FUN_1009174c`

Transitions:

- if `state2_timeout == 1` and `primary_mode in {1,6}` -> advance to **substate 3**
- else if `current_float > cfg->f_34` -> collapse to **substate 0**
- else if `aux_window_flag != 0` -> collapse to **substate 0**

### Substate 3: `FUN_100917bc`

Transitions:

- if `primary_mode == 0` -> force output substate **2**
- else if `primary_mode == 1` -> collapse to **substate 0**
- else if `FUN_100916a8() == 1` -> collapse to **substate 0**
- else if `current_float > cfg->f_34` -> collapse to **substate 0**

## What this means for the F-150 "LKA timer"

What is now solid from code:

- there is one **fixed** 10-second auxiliary window in `FUN_1009158c`
- there are two **configurable** per-substate timers in `FUN_10091612`
- those configurable timers are **byte fields scaled by 10000 ms**

What is **not** solid yet:

- the exact flash offset that backs `cfg+0x48` and `cfg+0x49`
- whether the previously identified `cal+0x07ADC/0x07ADE = 10000/10000` words are the direct backing fields for this state machine, or whether they belong to a sibling higher-level qualifier

## Best current mapping to the cal neighborhood

The cal neighborhood around the previously identified F-150 timer cluster is:

```text
cal+0x07ADC: 10 27 10 27 DC 05 2C 01 01 01 03 00 ...
             ^^^^^ ^^^^^ ^^^^^ ^^^^^ ^  ^
             10000 10000 1500   300  1  1
```

The **new** Ghidra result makes the adjacent byte pair especially interesting:

- `cal+0x07AE4 = 0x01`
- `cal+0x07AE5 = 0x01`

Because the live code uses:

- `cfg+0x48 * 10000`
- `cfg+0x49 * 10000`

So the best current fit is:

- the real per-substate 10-second timers are likely the adjacent `01/01` bytes
- the `10000/10000` u16 pair at `0x07ADC/0x07ADE` may be a related higher-level arm/re-arm pair in the same feature block, but this pass did **not** prove that direct code path

That is a stronger and more defensible position than the earlier "two explicit 10-second scalars" claim.

## Practical takeaway

For patching and behavioral reasoning:

- there is definitely a **10-second LKA-adjacent timing behavior** in this image
- the tightest proven code path is the smaller 4-state helper, not `FUN_101a3b84`
- the state helper uses:
  - one fixed 10-second window
  - two config-byte timers with 10-second units

So if the goal is to remove post-intervention waiting/lockout behavior, the right mental model is:

- **not** one scalar
- **not** only the main LKA controller
- but a multi-stage timer-driven substate machine with three timer checks

## Broader EPS supervisor context

This timer helper is only one part of the rack-side supervisor.

Additional tracing now shows:

- `context + 0x68` is a mixed float/int continuous-control block
- `context + 0x6c` is a packed `u16 * 10 ms` debounce/persistence bundle
- `context + 0x74` is a lookup/curve block

That broader split is documented in [eps_supervisor_ghidra_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/eps_supervisor_ghidra_trace.md).

The practical consequence is that removing the apparent "10 second timer" in flash may not eliminate the whole waiting behavior unless the associated dwell-latch bundle is also understood.
