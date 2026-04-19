#!/bin/zsh
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: $0 /path/to/transit_block0_strategy.bin [project_dir] [project_name] [artifact_dir]" >&2
  exit 1
fi

BIN_PATH="${1:A}"
PROJECT_DIR="${2:-${BIN_PATH:h}/ghidra_block0_project}"
PROJECT_NAME="${3:-Transit_AM_Block0Lift}"
ARTIFACT_DIR="${4:-${BIN_PATH:h}/ghidra_block0_trace}"

SCRIPT_ROOT="/Users/rossfisher/ford-pscm-re/tools/scripts"
TRANSIT_CLEANUP_ROOT="/Users/rossfisher/ford-pscm-re/tools/scripts/transit_cleanup"
SEED_ROOT="/Users/rossfisher/ford-pscm-re/tools/ghidra_v850_patched/seeds"
ANALYZE_HEADLESS="/opt/homebrew/Cellar/ghidra/12.0.4/libexec/support/analyzeHeadless"
SCRIPT_PATHS="${SCRIPT_ROOT};${TRANSIT_CLEANUP_ROOT};${SEED_ROOT}"
LOG_DIR="$ARTIFACT_DIR/logs"

mkdir -p "$PROJECT_DIR" "$ARTIFACT_DIR" "$LOG_DIR"

if [[ -e "$PROJECT_DIR/$PROJECT_NAME.gpr" || -d "$PROJECT_DIR/$PROJECT_NAME.rep" ]]; then
  echo "project already exists: $PROJECT_DIR/$PROJECT_NAME" >&2
  echo "remove it or choose a different project name" >&2
  exit 1
fi

export MEASURE_OUT="$ARTIFACT_DIR/measure.tsv"
export TRANSIT_STATE_TRACE_OUT="$ARTIFACT_DIR/state_trace"
export TRANSIT_BLOCK1_PATH="${BIN_PATH:h}/block1_ram.bin"
export TRANSIT_BLOCK2_PATH="${BIN_PATH:h}/block2_ext.bin"

echo "[1/4] Import + seeded analysis into $PROJECT_DIR/$PROJECT_NAME"
"$ANALYZE_HEADLESS" "$PROJECT_DIR" "$PROJECT_NAME" \
  -import "$BIN_PATH" \
  -loader BinaryLoader \
  -loader-baseAddr 0x01000000 \
  -processor "v850e3:LE:32:default" \
  -scriptPath "$SCRIPT_PATHS" \
  -preScript SetOptions.java \
  -postScript SeedFromJarls.java \
  2>&1 | tee "$LOG_DIR/01_import_seed.log"

echo "[2/5] Switch table recovery"
"$ANALYZE_HEADLESS" "$PROJECT_DIR" "$PROJECT_NAME" \
  -process "$(basename "$BIN_PATH")" \
  -noanalysis \
  -scriptPath "$SCRIPT_PATHS" \
  -postScript RH850SwitchTableDetector.java \
  2>&1 | tee "$LOG_DIR/02_switch_tables.log"

echo "[3/5] Boundary cleanup"
"$ANALYZE_HEADLESS" "$PROJECT_DIR" "$PROJECT_NAME" \
  -process "$(basename "$BIN_PATH")" \
  -noanalysis \
  -scriptPath "$SCRIPT_PATHS" \
  -postScript CleanupBoundaries.java \
  2>&1 | tee "$LOG_DIR/03_cleanup.log"

echo "[4/6] Quality measurement"
"$ANALYZE_HEADLESS" "$PROJECT_DIR" "$PROJECT_NAME" \
  -process "$(basename "$BIN_PATH")" \
  -noanalysis \
  -scriptPath "$SCRIPT_PATHS" \
  -postScript MeasureQuality.java \
  -readOnly \
  2>&1 | tee "$LOG_DIR/04_measure.log"

echo "[5/6] Sample decompile quality"
"$ANALYZE_HEADLESS" "$PROJECT_DIR" "$PROJECT_NAME" \
  -process "$(basename "$BIN_PATH")" \
  -noanalysis \
  -scriptPath "$SCRIPT_PATHS" \
  -postScript SampleProjectLift.java 0x01000000 0x010FFFEF 100 40 \
  -readOnly \
  2>&1 | tee "$LOG_DIR/05_sample.log"

echo "[6/6] Runtime state trace export"
"$ANALYZE_HEADLESS" "$PROJECT_DIR" "$PROJECT_NAME" \
  -process "$(basename "$BIN_PATH")" \
  -noanalysis \
  -scriptPath "$SCRIPT_PATHS" \
  -postScript TransitStateTrace.java \
  -readOnly \
  2>&1 | tee "$LOG_DIR/06_state_trace.log"

echo
echo "Project: $PROJECT_DIR/$PROJECT_NAME"
echo "Artifacts:"
echo "  $ARTIFACT_DIR/measure.tsv"
echo "  $ARTIFACT_DIR/measure.tsv.summary"
echo "  $ARTIFACT_DIR/state_trace/summary.txt"
echo "  $LOG_DIR"
