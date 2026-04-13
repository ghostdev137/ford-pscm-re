# Qwen3-Coder Transit PSCM Annotations

154 clean-decompiling functions from `transit_AH_blk0_0x01000000.bin` sent through
Qwen3-Coder-30B-A3B (MXFP4, running on a 5090 via llama.cpp) and asked to
guess function name, purpose, variable renames, and struct layout.

Format: `<addr>` → `{ name, purpose, vars{}, struct_fields[[offset, type, name]] }`.
Every guessed name is prefixed `maybe_` when the model is unsure.

## Candidates worth a manual look

| Address | Guessed name | Purpose |
|---|---|---|
| `0x01031ece` | `maybe_adjust_steering_input` | Clamps input steering angle + dispatches to control handler (likely the LKA angle-clamp path) |
| `0x0100f068` | `maybe_steering_control_limit` | Apply clamping limits to steering control parameters |
| `0x01009d86` | `maybe_update_steering_angle` | Updates steering angle sensor data |
| `0x0106fc66` | `maybe_power_steering_calibration_update` | Handles overflow protection for steering |

## Reproduce

```bash
# 1. Dump clean decompiles from Ghidra (see tools/scripts/DumpDecomps.java)
# 2. Run the annotation pipeline (needs local or remote OpenAI-compatible endpoint)
python3 tools/pipeline/annotate.py
```

`annotate.py` defaults to `http://100.69.219.3:8000/v1` and model `qwen3-coder`.
Change `ENDPOINT`/`MODEL`/`PARALLEL` at the top to suit your setup. **Important**:
if the server is llama.cpp with `--parallel N`, set `PARALLEL = N` or lower or
requests will queue and silently timeout.

## Caveats

- Qwen frequently guesses "power_steering_X" because it's biased by the domain
  hint in the prompt. Treat names as hints, not ground truth.
- `struct_fields` offsets come from what the function reads, so they're
  accurate but function-local — a single struct's full layout requires unioning
  offsets from all functions that touch it.
- Functions with RH850 extended ops still hitting `halt_baddata` aren't in
  this set (dump phase filters them out). See `tools/ghidra_v850_patched/`
  for the SLEIGH patch that got us from 42% → 90% clean coverage.
