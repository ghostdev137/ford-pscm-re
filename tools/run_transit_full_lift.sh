#!/bin/zsh
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: $0 /path/to/transit_full.elf [project_dir] [project_name] [artifact_dir]" >&2
  exit 1
fi

ELF_PATH="${1:A}"
ELF_STEM="${ELF_PATH:t:r}"
DEFAULT_PROJECT_NAME="${ELF_STEM//[^[:alnum:]_]/_}_FullLift"
PROJECT_DIR="${2:-${ELF_PATH:h}/ghidra_project_${ELF_STEM}}"
PROJECT_NAME="${3:-${DEFAULT_PROJECT_NAME}}"
ARTIFACT_DIR="${4:-${ELF_PATH:h}/${ELF_STEM}_ghidra_runtime_trace}"

SCRIPT_ROOT="${TRANSIT_SCRIPT_ROOT:-/Users/rossfisher/ford-pscm-re/tools/scripts}"
TRANSIT_CLEANUP_ROOT="${TRANSIT_CLEANUP_ROOT:-/Users/rossfisher/ford-pscm-re/tools/scripts/transit_cleanup}"
SEED_ROOT="${TRANSIT_SEED_ROOT:-/Users/rossfisher/ford-pscm-re/tools/ghidra_v850_patched/seeds}"
ANALYZE_HEADLESS="${TRANSIT_ANALYZE_HEADLESS:-/opt/homebrew/Cellar/ghidra/12.0.4/libexec/support/analyzeHeadless}"
PROCESSOR="${TRANSIT_PROCESSOR:-v850e3:LE:32:default}"
SAMPLE_START="${TRANSIT_SAMPLE_START:-0x01000000}"
SAMPLE_END="${TRANSIT_SAMPLE_END:-0x20FFFFFF}"
SWITCH_SEEDING="${TRANSIT_SWITCH_SEEDING:-0}"
RUN_NORETURN_FIXUP="${TRANSIT_RUN_NORETURN_FIXUP:-0}"
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
export SAMPLE_LIFT_OUT="$ARTIFACT_DIR/sample_lift.tsv"
export TRANSIT_FUNCTION_START_SEARCH="${TRANSIT_FUNCTION_START_SEARCH:-1}"
export TRANSIT_NONRETURN_DISCOVERY="${TRANSIT_NONRETURN_DISCOVERY:-1}"

echo "[1/6] Import + seeded analysis into $PROJECT_DIR/$PROJECT_NAME"
SEED_ARGS=("SeedFromJarls.java")
if [[ "$SWITCH_SEEDING" != "1" ]]; then
  SEED_ARGS+=("skip-switches")
fi
"$ANALYZE_HEADLESS" "$PROJECT_DIR" "$PROJECT_NAME" \
  -import "$ELF_PATH" \
  -noanalysis \
  -processor "$PROCESSOR" \
  -scriptPath "$SCRIPT_PATHS" \
  -preScript SetOptions.java \
  -postScript "${SEED_ARGS[@]}" \
  2>&1 | tee "$LOG_DIR/01_import_seed.log"

echo "[1b/6] Seeded analysis"
"$ANALYZE_HEADLESS" "$PROJECT_DIR" "$PROJECT_NAME" \
  -process "$(basename "$ELF_PATH")" \
  -scriptPath "$SCRIPT_PATHS" \
  -preScript SetOptions.java \
  2>&1 | tee "$LOG_DIR/01b_seeded_analysis.log"

if [[ "$RUN_NORETURN_FIXUP" == "1" ]]; then
  echo "[2/7] No-return repair"
  "$ANALYZE_HEADLESS" "$PROJECT_DIR" "$PROJECT_NAME" \
    -process "$(basename "$ELF_PATH")" \
    -noanalysis \
    -scriptPath "$SCRIPT_PATHS" \
    -postScript FixupNoReturnFunctionsScript.java \
    2>&1 | tee "$LOG_DIR/02_no_return.log"
else
  echo "[2/6] No-return repair skipped"
fi

echo "[3/6] Switch table recovery"
"$ANALYZE_HEADLESS" "$PROJECT_DIR" "$PROJECT_NAME" \
  -process "$(basename "$ELF_PATH")" \
  -noanalysis \
  -scriptPath "$SCRIPT_PATHS" \
  -postScript RH850SwitchTableDetector.java \
  2>&1 | tee "$LOG_DIR/03_switch_tables.log"

echo "[4/7] Targeted offcut repair"
TRANSIT_ANALYSIS_LOG="$LOG_DIR/01b_seeded_analysis.log" \
  "$ANALYZE_HEADLESS" "$PROJECT_DIR" "$PROJECT_NAME" \
  -process "$(basename "$ELF_PATH")" \
  -noanalysis \
  -scriptPath "$SCRIPT_PATHS" \
  -postScript TransitTargetedOffcutRepair.java \
  2>&1 | tee "$LOG_DIR/04_offcut_repair.log"

echo "[5/9] Boundary cleanup pass 1"
"$ANALYZE_HEADLESS" "$PROJECT_DIR" "$PROJECT_NAME" \
  -process "$(basename "$ELF_PATH")" \
  -noanalysis \
  -scriptPath "$SCRIPT_PATHS" \
  -postScript CleanupBoundaries.java \
  2>&1 | tee "$LOG_DIR/05_cleanup_pass1.log"

echo "[6/9] Boundary cleanup pass 2"
"$ANALYZE_HEADLESS" "$PROJECT_DIR" "$PROJECT_NAME" \
  -process "$(basename "$ELF_PATH")" \
  -noanalysis \
  -scriptPath "$SCRIPT_PATHS" \
  -postScript CleanupBoundaries.java \
  2>&1 | tee "$LOG_DIR/06_cleanup_pass2.log"

echo "[7/9] Bogus function report"
TRANSIT_BOGUS_REPORT_OUT="$ARTIFACT_DIR/bogus_functions.tsv" \
  "$ANALYZE_HEADLESS" "$PROJECT_DIR" "$PROJECT_NAME" \
  -process "$(basename "$ELF_PATH")" \
  -noanalysis \
  -scriptPath "$SCRIPT_PATHS" \
  -postScript TransitBogusFunctionReport.java \
  -readOnly \
  2>&1 | tee "$LOG_DIR/07_bogus_report.log"

echo "[8/9] Quality measurement"
"$ANALYZE_HEADLESS" "$PROJECT_DIR" "$PROJECT_NAME" \
  -process "$(basename "$ELF_PATH")" \
  -noanalysis \
  -scriptPath "$SCRIPT_PATHS" \
  -postScript MeasureQuality.java \
  -readOnly \
  2>&1 | tee "$LOG_DIR/08_measure.log"

echo "[9/9] Sample decompile quality"
"$ANALYZE_HEADLESS" "$PROJECT_DIR" "$PROJECT_NAME" \
  -process "$(basename "$ELF_PATH")" \
  -noanalysis \
  -scriptPath "$SCRIPT_PATHS" \
  -postScript SampleProjectLift.java "$SAMPLE_START" "$SAMPLE_END" 100 40 \
  -readOnly \
  2>&1 | tee "$LOG_DIR/09_sample.log"

echo "[10/10] Runtime state trace export"
"$ANALYZE_HEADLESS" "$PROJECT_DIR" "$PROJECT_NAME" \
  -process "$(basename "$ELF_PATH")" \
  -noanalysis \
  -scriptPath "$SCRIPT_PATHS" \
  -postScript TransitStateTrace.java \
  -readOnly \
  2>&1 | tee "$LOG_DIR/10_state_trace.log"

echo
echo "Project: $PROJECT_DIR/$PROJECT_NAME"
echo "Artifacts:"
echo "  $ARTIFACT_DIR/measure.tsv"
echo "  $ARTIFACT_DIR/measure.tsv.summary"
echo "  $ARTIFACT_DIR/bogus_functions.tsv"
echo "  $ARTIFACT_DIR/sample_lift.tsv"
echo "  $ARTIFACT_DIR/state_trace/summary.txt"
echo "  $LOG_DIR"
