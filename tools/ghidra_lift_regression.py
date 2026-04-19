#!/usr/bin/env python3
"""Run reproducible Ghidra headless lift checks for Transit and F-150 PSCM images."""

from __future__ import annotations

import argparse
from collections import Counter
import glob
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


TRANSIT_RESULT_RE = re.compile(
    r"RESULT total_fns=(?P<total>\d+) sampled=(?P<sampled>\d+) clean=(?P<clean>\d+) "
    r"warnings=(?P<warnings>\d+) baddata=(?P<baddata>\d+) failed=(?P<failed>\d+)"
)

F150_RESULT_RE = re.compile(
    r"RESULT total=(?P<total>\d+) completed=(?P<completed>\d+) clean=(?P<clean>\d+) "
    r"warnings=(?P<warnings>\d+) baddata=(?P<baddata>\d+) failed=(?P<failed>\d+)"
)
DECOMPILER_WARN_RE = re.compile(
    r"WARN\s+Decompiling\s+(?P<addr>[0-9A-Fa-f]+)(?:,\s+pcode error at [0-9A-Fa-f]+)?:\s+"
    r"(?P<detail>.+?)\s+\(DecompileCallback\)"
)
SEED_SUMMARY_RE = re.compile(
    r"SeedFromJarls:\s+seeded=(?P<seeded>\d+)\s+failed=(?P<failed>\d+)\s+"
    r"switchTables=(?P<switch_tables>\d+)\s+switchFunctions=(?P<switch_functions>\d+)\s+"
    r"forcedExact=(?P<forced_exact>\d+)"
)
THUNK_CONFLICT_RE = re.compile(
    r"ERROR Failed to create function at (?P<entry>[0-9A-Fa-f]+) "
    r"since its body contains referring thunk at (?P<thunk>[0-9A-Fa-f]+)"
)
OFFCUT_WARN_RE = re.compile(
    r"Invalid delay slot or offcut instruction found at\s+(?P<addr>[0-9A-Fa-f]+)"
)
CTOR_FAIL_RE = re.compile(
    r"Unable to resolve constructor at\s+(?P<addr>[0-9A-Fa-f]+)"
)


@dataclass
class TransitThresholds:
    min_clean: int = 90
    max_baddata: int = 10
    max_failed: int = 10


@dataclass
class F150Thresholds:
    min_clean: int = 3200
    max_baddata: int = 80
    max_failed: int = 20


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def default_analyze_headless() -> str:
    env = os.environ.get("GHIDRA_ANALYZE_HEADLESS")
    if env:
        return env

    explicit = Path("/opt/homebrew/Cellar/ghidra/12.0.4/libexec/support/analyzeHeadless")
    if explicit.exists():
        return str(explicit)

    matches = sorted(glob.glob("/opt/homebrew/Cellar/ghidra/*/libexec/support/analyzeHeadless"))
    if matches:
        return matches[-1]

    found = shutil.which("analyzeHeadless")
    if found:
        return found

    raise FileNotFoundError("could not find analyzeHeadless; set GHIDRA_ANALYZE_HEADLESS")


def ensure_exists(path: Path, what: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"{what} not found: {path}")


def prepare_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def fresh_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def run_command(
    cmd: list[str],
    log_path: Path,
    env: dict[str, str] | None = None,
) -> str:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)

    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=merged_env,
        check=False,
    )
    log_path.write_text(proc.stdout, encoding="utf-8")
    if proc.returncode != 0:
        raise RuntimeError(
            f"command failed with rc={proc.returncode}: {' '.join(cmd)}\n"
            f"log: {log_path}"
        )
    return proc.stdout


def find_last_match(pattern: re.Pattern[str], text: str) -> dict[str, int]:
    matches = list(pattern.finditer(text))
    if not matches:
        raise ValueError(f"missing RESULT line for pattern {pattern.pattern!r}")
    return {k: int(v) for k, v in matches[-1].groupdict().items()}


def parse_measure_summary(path: Path) -> dict[str, int]:
    data: dict[str, int] = {}
    for line in read_text(path).splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not value:
            continue
        try:
            data[key] = int(value)
        except ValueError:
            continue
    return data


def pct(clean: int, sampled: int) -> float:
    return (clean / sampled * 100.0) if sampled else 0.0


def default_transit_full_elf(repo: Path) -> str:
    explicit = Path(
        "/Users/rossfisher/Desktop/Transit_2025_PSCM_dump/"
        "set_03_cal_AH_strategy_AH_cal_AD/decompressed/"
        "transit_pscm_KK21-3F964-AH_full.elf"
    )
    if explicit.exists():
        return str(explicit)

    candidates = sorted((repo / "firmware").glob("**/*_full.elf"))
    if candidates:
        return str(candidates[0])
    return ""


def infer_transit_variant(image: Path) -> str:
    match = re.search(r"-([A-Z0-9]{2,})_full\.elf$", image.name)
    if match:
        return match.group(1)
    return image.stem.upper().replace("-", "_")


def normalize_failure_detail(detail: str) -> str:
    normalized = detail.strip()
    normalized = re.sub(r"\s+at\s+(?:ram:)?[0-9A-Fa-f]+$", "", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def parse_decompile_failures(text: str, limit: int = 10) -> dict[str, object]:
    counter: Counter[str] = Counter()
    examples: list[dict[str, str]] = []
    for match in DECOMPILER_WARN_RE.finditer(text):
        detail = normalize_failure_detail(match.group("detail"))
        counter[detail] += 1
        if len(examples) < limit:
            examples.append(
                {
                    "address": f"0x{match.group('addr').lower()}",
                    "detail": detail,
                }
            )
    return {
        "total": sum(counter.values()),
        "top_buckets": [
            {"detail": detail, "count": count}
            for detail, count in counter.most_common(limit)
        ],
        "examples": examples,
    }


def parse_seed_metrics(text: str) -> dict[str, object]:
    summary = SEED_SUMMARY_RE.search(text)
    thunk_conflicts = [
        {
            "entry": f"0x{match.group('entry').lower()}",
            "thunk": f"0x{match.group('thunk').lower()}",
        }
        for match in THUNK_CONFLICT_RE.finditer(text)
    ]
    data: dict[str, object] = {
        "switch_table_lines": text.count("SeedFromJarls: table @"),
        "thunk_conflicts": thunk_conflicts[:20],
        "thunk_conflict_count": len(thunk_conflicts),
    }
    if summary:
        data.update({k: int(v) for k, v in summary.groupdict().items()})
    return data


def parse_issue_addresses(pattern: re.Pattern[str], *texts: str, limit: int = 64) -> dict[str, object]:
    values: list[str] = []
    seen: set[str] = set()
    for text in texts:
        for match in pattern.finditer(text):
            addr = f"0x{match.group('addr').lower()}"
            if addr in seen:
                continue
            seen.add(addr)
            values.append(addr)
    return {
        "count": len(values),
        "addresses": values[:limit],
    }


def parse_bogus_report(path: Path) -> dict[str, object]:
    if not path.exists():
        return {
            "no_ref_count": 0,
            "suspicious_count": 0,
            "examples": [],
        }
    no_ref = 0
    suspicious = 0
    examples: list[dict[str, int]] = []
    for line in read_text(path).splitlines():
        if line.startswith("no_ref_count="):
            no_ref = int(line.split("=", 1)[1])
            continue
        if line.startswith("suspicious_count="):
            suspicious = int(line.split("=", 1)[1])
            continue
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        addr, size, score = parts
        try:
            examples.append(
                {
                    "address": addr,
                    "size": int(size),
                    "score": int(score),
                }
            )
        except ValueError:
            continue
    return {
        "no_ref_count": no_ref,
        "suspicious_count": suspicious,
        "examples": examples,
    }


def parse_sample_lift(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    rows: list[dict[str, object]] = []
    for idx, line in enumerate(read_text(path).splitlines()):
        if idx == 0 or not line.strip():
            continue
        parts = line.split("\t", 3)
        if len(parts) < 4:
            continue
        addr, size, status, detail = parts
        try:
            rows.append(
                {
                    "address": f"0x{int(addr, 16):08x}",
                    "size": int(size),
                    "status": status,
                    "detail": detail,
                }
            )
        except ValueError:
            continue
    return rows


def summarize_sample_lift(rows: list[dict[str, object]], limit: int = 20) -> dict[str, object]:
    status_counts: Counter[str] = Counter()
    non_clean: list[dict[str, object]] = []
    for row in rows:
        status = str(row["status"])
        status_counts[status] += 1
        if status != "clean":
            non_clean.append(row)
    non_clean.sort(key=lambda row: (str(row["status"]), str(row["address"])))
    return {
        "counts": dict(sorted(status_counts.items())),
        "top_failures": non_clean[:limit],
    }


def compare_run_metrics(
    current: dict[str, object],
    baseline: dict[str, object],
) -> dict[str, object]:
    metrics = ("sampled", "clean", "warnings", "baddata", "failed")
    deltas = {
        metric: int(current.get(metric, 0)) - int(baseline.get(metric, 0))
        for metric in metrics
    }
    regressions: list[str] = []
    if deltas["clean"] < 0:
        regressions.append("clean decreased")
    if deltas["baddata"] > 0:
        regressions.append("baddata increased")
    if deltas["failed"] > 0:
        regressions.append("failed increased")

    baseline_measure = baseline.get("measure", {}) if isinstance(baseline.get("measure"), dict) else {}
    current_measure = current.get("measure", {}) if isinstance(current.get("measure"), dict) else {}
    measure_deltas: dict[str, int] = {}
    for key in ("total", "halt_baddata", "bad_bm", "median_size"):
        if key in current_measure or key in baseline_measure:
            measure_deltas[key] = int(current_measure.get(key, 0)) - int(baseline_measure.get(key, 0))

    return {
        "baseline_input": baseline.get("input"),
        "current_input": current.get("input"),
        "deltas": deltas,
        "measure_deltas": measure_deltas,
        "regressions": regressions,
    }


def transit_script_paths(repo: Path) -> str:
    return ";".join(
        [
            str(repo / "tools" / "scripts"),
            str(repo / "tools" / "scripts" / "transit_cleanup"),
            str(repo / "tools" / "ghidra_v850_patched" / "seeds"),
        ]
    )


def run_transit_block0(
    analyze_headless: str,
    repo: Path,
    image: Path,
    out_root: Path,
    thresholds: TransitThresholds,
    with_state_trace: bool,
    with_switch_seeding: bool,
    with_elf_oracle_seeds: bool,
) -> dict[str, object]:
    ensure_exists(image, "Transit block0 image")
    fresh_dir(out_root)
    logs_dir = out_root / "logs"
    prepare_dir(logs_dir)

    project_dir = out_root / "project"
    prepare_dir(project_dir)
    project_name = "TransitBlock0Lift"
    script_path = transit_script_paths(repo)
    program_name = image.name

    import_log = logs_dir / "01_import_seed.log"
    analysis_log = import_log
    switch_log = logs_dir / "02_switch_tables.log"
    offcut_log = logs_dir / "03_offcut_repair.log"
    cleanup_log = logs_dir / "04_cleanup_pass1.log"
    cleanup_log_2 = logs_dir / "05_cleanup_pass2.log"
    bogus_log = logs_dir / "06_bogus_report.log"
    measure_log = logs_dir / "07_measure.log"
    sample_log = logs_dir / "08_sample.log"
    state_log = logs_dir / "09_state_trace.log"
    measure_out = out_root / "measure.tsv"
    sample_out = out_root / "sample_lift.tsv"
    bogus_out = out_root / "bogus_functions.tsv"
    image_dir = image.parent
    transit_env = {
        "TRANSIT_BLOCK1_PATH": str(image_dir / "block1_ram.bin"),
        "TRANSIT_BLOCK2_PATH": str(image_dir / "block2_ext.bin"),
    }

    elf_oracle_seed_path: Path | None = None
    if with_elf_oracle_seeds:
        sibling_full_elf = next(iter(sorted(image_dir.glob("*_full.elf"))), None)
        if sibling_full_elf is not None:
            elf_oracle_seed_path = out_root / "elf_function_starts.txt"
            oracle_project_dir = out_root / "elf_seed_project"
            prepare_dir(oracle_project_dir)
            run_command(
                [
                    analyze_headless,
                    str(oracle_project_dir),
                    "TransitElfSeedOracle",
                    "-import",
                    str(sibling_full_elf),
                    "-processor",
                    "v850e3:LE:32:default",
                    "-scriptPath",
                    str(repo / "tools" / "scripts"),
                    "-postScript",
                    "ExportFunctionStarts.java",
                    "0x01000000",
                    "0x010FFFEF",
                    "-deleteProject",
                ],
                logs_dir / "00_export_elf_seeds.log",
                env={"FUNCTION_STARTS_OUT": str(elf_oracle_seed_path)},
            )
            transit_env["TRANSIT_EXTRA_SEED_PATHS"] = str(elf_oracle_seed_path)

    seed_args = ["SeedFromJarls.java"]
    if not with_switch_seeding:
        seed_args.append("skip-switches")

    run_command(
        [
            analyze_headless,
            str(project_dir),
            project_name,
            "-import",
            str(image),
            "-loader",
            "BinaryLoader",
            "-loader-baseAddr",
            "0x01000000",
            "-processor",
            "v850e3:LE:32:default",
            "-noanalysis",
            "-scriptPath",
            script_path,
            "-preScript",
            "SetOptions.java",
            "-postScript",
            *seed_args,
        ],
        import_log,
        env=transit_env,
    )

    run_command(
        [
            analyze_headless,
            str(project_dir),
            project_name,
            "-process",
            program_name,
            "-noanalysis",
            "-scriptPath",
            script_path,
            "-postScript",
            "RH850SwitchTableDetector.java",
        ],
        switch_log,
    )

    run_command(
        [
            analyze_headless,
            str(project_dir),
            project_name,
            "-process",
            program_name,
            "-noanalysis",
            "-scriptPath",
            script_path,
            "-postScript",
            "TransitTargetedOffcutRepair.java",
        ],
        offcut_log,
        env={"TRANSIT_ANALYSIS_LOG": str(analysis_log)},
    )

    run_command(
        [
            analyze_headless,
            str(project_dir),
            project_name,
            "-process",
            program_name,
            "-noanalysis",
            "-scriptPath",
            script_path,
            "-postScript",
            "CleanupBoundaries.java",
        ],
        cleanup_log,
    )

    run_command(
        [
            analyze_headless,
            str(project_dir),
            project_name,
            "-process",
            program_name,
            "-noanalysis",
            "-scriptPath",
            script_path,
            "-postScript",
            "CleanupBoundaries.java",
        ],
        cleanup_log_2,
    )

    run_command(
        [
            analyze_headless,
            str(project_dir),
            project_name,
            "-process",
            program_name,
            "-noanalysis",
            "-scriptPath",
            script_path,
            "-postScript",
            "TransitBogusFunctionReport.java",
            "-readOnly",
        ],
        bogus_log,
        env={"TRANSIT_BOGUS_REPORT_OUT": str(bogus_out)},
    )

    run_command(
        [
            analyze_headless,
            str(project_dir),
            project_name,
            "-process",
            program_name,
            "-noanalysis",
            "-scriptPath",
            script_path,
            "-postScript",
            "MeasureQuality.java",
            "-readOnly",
        ],
        measure_log,
        env={"MEASURE_OUT": str(measure_out)},
    )

    sample_output = run_command(
        [
            analyze_headless,
            str(project_dir),
            project_name,
            "-process",
            program_name,
            "-noanalysis",
            "-scriptPath",
            script_path,
            "-postScript",
            "SampleProjectLift.java",
            "0x01000000",
            "0x010FFFEF",
            "100",
            "40",
            "-readOnly",
        ],
        sample_log,
        env={"SAMPLE_LIFT_OUT": str(sample_out)},
    )

    state_trace_enabled = False
    if with_state_trace:
        run_command(
            [
                analyze_headless,
                str(project_dir),
                project_name,
                "-process",
                program_name,
                "-noanalysis",
                "-scriptPath",
                str(repo / "tools" / "scripts"),
                "-postScript",
                "TransitStateTrace.java",
                "-readOnly",
            ],
            state_log,
            env={"TRANSIT_STATE_TRACE_OUT": str(out_root / "state_trace")},
        )
        state_trace_enabled = True

    summary = find_last_match(TRANSIT_RESULT_RE, sample_output)
    summary["clean_pct"] = round(pct(summary["clean"], summary["sampled"]), 1)
    summary["passes_thresholds"] = (
        summary["clean"] >= thresholds.min_clean
        and summary["baddata"] <= thresholds.max_baddata
        and summary["failed"] <= thresholds.max_failed
    )
    summary["measure"] = parse_measure_summary(Path(str(measure_out) + ".summary"))
    summary["thresholds"] = asdict(thresholds)
    summary["processor"] = "v850e3:LE:32:default"
    summary["input"] = str(image)
    summary["project_dir"] = str(project_dir)
    summary["logs_dir"] = str(logs_dir)
    summary["state_trace_enabled"] = state_trace_enabled
    summary["switch_seeding_enabled"] = with_switch_seeding
    summary["elf_oracle_seeds"] = str(elf_oracle_seed_path) if elf_oracle_seed_path else None
    summary["sample_lift_tsv"] = str(sample_out)
    summary["sample_lift"] = summarize_sample_lift(parse_sample_lift(sample_out))
    summary["import_seed"] = parse_seed_metrics(read_text(import_log))
    summary["decompile_failures"] = parse_decompile_failures(read_text(import_log))
    summary["analysis_issues"] = {
        "offcut": parse_issue_addresses(
            OFFCUT_WARN_RE,
            read_text(analysis_log),
            read_text(offcut_log),
        ),
        "constructors": parse_issue_addresses(
            CTOR_FAIL_RE,
            read_text(cleanup_log),
            read_text(cleanup_log_2),
            read_text(measure_log),
            read_text(sample_log),
        ),
    }
    summary["bogus_functions"] = parse_bogus_report(bogus_out)
    return summary


def run_transit_full_elf(
    analyze_headless: str,
    repo: Path,
    image: Path,
    out_root: Path,
    thresholds: TransitThresholds,
    with_state_trace: bool,
    with_switch_seeding: bool,
) -> dict[str, object]:
    ensure_exists(image, "Transit full ELF")
    fresh_dir(out_root)
    logs_dir = out_root / "logs"
    prepare_dir(logs_dir)

    project_dir = out_root / "project"
    prepare_dir(project_dir)
    variant = infer_transit_variant(image)
    project_name = f"Transit_{variant}_FullLift"
    script_path = transit_script_paths(repo)
    program_name = image.name

    import_log = logs_dir / "01_import_seed.log"
    switch_log = logs_dir / "02_switch_tables.log"
    offcut_log = logs_dir / "03_offcut_repair.log"
    cleanup_log = logs_dir / "04_cleanup_pass1.log"
    cleanup_log_2 = logs_dir / "05_cleanup_pass2.log"
    bogus_log = logs_dir / "06_bogus_report.log"
    measure_log = logs_dir / "07_measure.log"
    sample_log = logs_dir / "08_sample.log"
    state_log = logs_dir / "09_state_trace.log"
    measure_out = out_root / "measure.tsv"
    sample_out = out_root / "sample_lift.tsv"
    bogus_out = out_root / "bogus_functions.tsv"

    seed_args = ["SeedFromJarls.java"]
    run_noreturn_fixup = os.environ.get("TRANSIT_RUN_NORETURN_FIXUP", "0") == "1"
    analysis_env = {}
    for key in (
        "TRANSIT_FUNCTION_START_SEARCH",
        "TRANSIT_NONRETURN_DISCOVERY",
        "TRANSIT_FSS_SEARCH_DATABLOCKS",
    ):
        value = os.environ.get(key)
        if value is not None:
            analysis_env[key] = value
    if not with_switch_seeding:
        seed_args.append("skip-switches")

    run_command(
        [
            analyze_headless,
            str(project_dir),
            project_name,
            "-import",
            str(image),
            "-noanalysis",
            "-processor",
            "v850e3:LE:32:default",
            "-scriptPath",
            script_path,
            "-preScript",
            "SetOptions.java",
            "-postScript",
            *seed_args,
        ],
        import_log,
        env=analysis_env or None,
    )

    analysis_log = logs_dir / "01b_seeded_analysis.log"
    no_return_log = logs_dir / "02_no_return.log"
    run_command(
        [
            analyze_headless,
            str(project_dir),
            project_name,
            "-process",
            program_name,
            "-scriptPath",
            script_path,
            "-preScript",
            "SetOptions.java",
        ],
        analysis_log,
        env=analysis_env or None,
    )

    if run_noreturn_fixup:
        run_command(
            [
                analyze_headless,
                str(project_dir),
                project_name,
                "-process",
                program_name,
                "-noanalysis",
                "-scriptPath",
                script_path,
                "-postScript",
                "FixupNoReturnFunctionsScript.java",
            ],
            no_return_log,
        )

    run_command(
        [
            analyze_headless,
            str(project_dir),
            project_name,
            "-process",
            program_name,
            "-noanalysis",
            "-scriptPath",
            script_path,
            "-postScript",
            "RH850SwitchTableDetector.java",
        ],
        switch_log,
    )

    run_command(
        [
            analyze_headless,
            str(project_dir),
            project_name,
            "-process",
            program_name,
            "-noanalysis",
            "-scriptPath",
            script_path,
            "-postScript",
            "TransitTargetedOffcutRepair.java",
        ],
        offcut_log,
        env={"TRANSIT_ANALYSIS_LOG": str(analysis_log)},
    )

    run_command(
        [
            analyze_headless,
            str(project_dir),
            project_name,
            "-process",
            program_name,
            "-noanalysis",
            "-scriptPath",
            script_path,
            "-postScript",
            "CleanupBoundaries.java",
        ],
        cleanup_log,
    )

    run_command(
        [
            analyze_headless,
            str(project_dir),
            project_name,
            "-process",
            program_name,
            "-noanalysis",
            "-scriptPath",
            script_path,
            "-postScript",
            "CleanupBoundaries.java",
        ],
        cleanup_log_2,
    )

    run_command(
        [
            analyze_headless,
            str(project_dir),
            project_name,
            "-process",
            program_name,
            "-noanalysis",
            "-scriptPath",
            script_path,
            "-postScript",
            "TransitBogusFunctionReport.java",
            "-readOnly",
        ],
        bogus_log,
        env={"TRANSIT_BOGUS_REPORT_OUT": str(bogus_out)},
    )

    run_command(
        [
            analyze_headless,
            str(project_dir),
            project_name,
            "-process",
            program_name,
            "-noanalysis",
            "-scriptPath",
            script_path,
            "-postScript",
            "MeasureQuality.java",
            "-readOnly",
        ],
        measure_log,
        env={"MEASURE_OUT": str(measure_out)},
    )

    sample_output = run_command(
        [
            analyze_headless,
            str(project_dir),
            project_name,
            "-process",
            program_name,
            "-noanalysis",
            "-scriptPath",
            script_path,
            "-postScript",
            "SampleProjectLift.java",
            "0x01000000",
            "0x20FFFFFF",
            "100",
            "40",
            "-readOnly",
        ],
        sample_log,
        env={"SAMPLE_LIFT_OUT": str(sample_out)},
    )

    state_trace_enabled = False
    if with_state_trace:
        run_command(
            [
                analyze_headless,
                str(project_dir),
                project_name,
                "-process",
                program_name,
                "-noanalysis",
                "-scriptPath",
                str(repo / "tools" / "scripts"),
                "-postScript",
                "TransitStateTrace.java",
                "-readOnly",
            ],
            state_log,
            env={"TRANSIT_STATE_TRACE_OUT": str(out_root / "state_trace")},
        )
        state_trace_enabled = True

    summary = find_last_match(TRANSIT_RESULT_RE, sample_output)
    summary["clean_pct"] = round(pct(summary["clean"], summary["sampled"]), 1)
    summary["passes_thresholds"] = (
        summary["clean"] >= thresholds.min_clean
        and summary["baddata"] <= thresholds.max_baddata
        and summary["failed"] <= thresholds.max_failed
    )
    summary["measure"] = parse_measure_summary(Path(str(measure_out) + ".summary"))
    summary["thresholds"] = asdict(thresholds)
    summary["processor"] = "v850e3:LE:32:default"
    summary["input"] = str(image)
    summary["project_dir"] = str(project_dir)
    summary["logs_dir"] = str(logs_dir)
    summary["state_trace_enabled"] = state_trace_enabled
    summary["variant"] = variant
    summary["switch_seeding_enabled"] = with_switch_seeding
    summary["noreturn_fixup_enabled"] = run_noreturn_fixup
    summary["sample_lift_tsv"] = str(sample_out)
    summary["sample_lift"] = summarize_sample_lift(parse_sample_lift(sample_out))
    summary["import_seed"] = parse_seed_metrics(read_text(import_log))
    summary["decompile_failures"] = parse_decompile_failures(read_text(import_log))
    summary["analysis_issues"] = {
        "offcut": parse_issue_addresses(
            OFFCUT_WARN_RE,
            read_text(analysis_log),
            read_text(offcut_log),
        ),
        "constructors": parse_issue_addresses(
            CTOR_FAIL_RE,
            read_text(cleanup_log),
            read_text(cleanup_log_2),
            read_text(measure_log),
            read_text(sample_log),
        ),
    }
    summary["bogus_functions"] = parse_bogus_report(bogus_out)
    return summary


def run_f150_full(
    analyze_headless: str,
    repo: Path,
    image: Path,
    out_root: Path,
    thresholds: F150Thresholds,
) -> dict[str, object]:
    ensure_exists(image, "F150 ELF")
    fresh_dir(out_root)
    logs_dir = out_root / "logs"
    prepare_dir(logs_dir)
    log_path = logs_dir / "f150_lift.log"
    project_dir = out_root / "project"
    prepare_dir(project_dir)

    output = run_command(
        [
            analyze_headless,
            str(project_dir),
            "F150LiftRegression",
            "-import",
            str(image),
            "-processor",
            "v850e3:LE:32:default",
            "-scriptPath",
            str(repo / "tools" / "scripts"),
            "-postScript",
            "F150LiftReport.java",
            "-deleteProject",
        ],
        log_path,
    )

    summary = find_last_match(F150_RESULT_RE, output)
    total = summary["total"]
    summary["clean_pct"] = round(pct(summary["clean"], total), 1)
    summary["passes_thresholds"] = (
        summary["clean"] >= thresholds.min_clean
        and summary["baddata"] <= thresholds.max_baddata
        and summary["failed"] <= thresholds.max_failed
    )
    summary["thresholds"] = asdict(thresholds)
    summary["processor"] = "v850e3:LE:32:default"
    summary["input"] = str(image)
    summary["logs_dir"] = str(logs_dir)
    return summary


def build_parser() -> argparse.ArgumentParser:
    repo = repo_root()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--analyze-headless",
        default=default_analyze_headless(),
        help="Path to Ghidra analyzeHeadless",
    )
    parser.add_argument(
        "--output-root",
        default=str(repo / "analysis" / "headless_lift"),
        help="Directory for run artifacts and summary output",
    )
    parser.add_argument(
        "--transit-block0",
        default=str(repo / "firmware" / "Transit_2025" / "decompressed" / "AM" / "block0_strategy.bin"),
        help="Transit block0 strategy image for the canonical seeded lift check",
    )
    parser.add_argument(
        "--transit-full-elf",
        default=default_transit_full_elf(repo),
        help="Transit full ELF used for the primary headless lift regression",
    )
    parser.add_argument(
        "--skip-transit",
        action="store_true",
        help="Skip the Transit run",
    )
    parser.add_argument(
        "--skip-transit-full",
        action="store_true",
        help="Skip the Transit full-ELF run",
    )
    parser.add_argument(
        "--with-state-trace",
        action="store_true",
        help="Also export TransitStateTrace artifacts",
    )
    parser.add_argument(
        "--with-switch-seeding",
        action="store_true",
        help="Enable the heavier Transit switch-target seeding pass during import",
    )
    parser.add_argument(
        "--with-elf-oracle-seeds",
        action="store_true",
        help="Seed block0 from function starts exported from a matching sibling full ELF when available",
    )
    parser.add_argument(
        "--f150-elf",
        default=str(repo / "firmware" / "F150_2021_Lariat_BlueCruise" / "f150_pscm_full.elf"),
        help="F150 full ELF used as a non-regression control",
    )
    parser.add_argument(
        "--skip-f150",
        action="store_true",
        help="Skip the F150 regression control run",
    )
    parser.add_argument("--transit-min-clean", type=int, default=TransitThresholds.min_clean)
    parser.add_argument("--transit-max-baddata", type=int, default=TransitThresholds.max_baddata)
    parser.add_argument("--transit-max-failed", type=int, default=TransitThresholds.max_failed)
    parser.add_argument("--f150-min-clean", type=int, default=F150Thresholds.min_clean)
    parser.add_argument("--f150-max-baddata", type=int, default=F150Thresholds.max_baddata)
    parser.add_argument("--f150-max-failed", type=int, default=F150Thresholds.max_failed)
    parser.add_argument(
        "--baseline-summary",
        help="Optional prior summary.json to compare against and flag regressions",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    repo = repo_root()
    analyze_headless = os.path.abspath(args.analyze_headless)
    ensure_exists(Path(analyze_headless), "analyzeHeadless")

    output_root = Path(args.output_root).resolve()
    prepare_dir(output_root)

    transit_thresholds = TransitThresholds(
        min_clean=args.transit_min_clean,
        max_baddata=args.transit_max_baddata,
        max_failed=args.transit_max_failed,
    )
    f150_thresholds = F150Thresholds(
        min_clean=args.f150_min_clean,
        max_baddata=args.f150_max_baddata,
        max_failed=args.f150_max_failed,
    )

    summary: dict[str, object] = {
        "analyze_headless": analyze_headless,
        "repo_root": str(repo),
        "runs": {},
    }

    failed_checks: list[str] = []

    if not args.skip_transit:
        transit_summary = run_transit_block0(
            analyze_headless=analyze_headless,
            repo=repo,
            image=Path(args.transit_block0).resolve(),
            out_root=output_root / "transit_block0",
            thresholds=transit_thresholds,
            with_state_trace=args.with_state_trace,
            with_switch_seeding=args.with_switch_seeding,
            with_elf_oracle_seeds=args.with_elf_oracle_seeds,
        )
        summary["runs"]["transit_block0"] = transit_summary
        if not transit_summary["passes_thresholds"]:
            failed_checks.append("transit_block0")

    if not args.skip_transit_full:
        if not args.transit_full_elf:
            raise FileNotFoundError("Transit full ELF path is empty; pass --transit-full-elf or use --skip-transit-full")
        transit_full_elf = Path(args.transit_full_elf).expanduser()
        transit_full_summary = run_transit_full_elf(
            analyze_headless=analyze_headless,
            repo=repo,
            image=transit_full_elf.resolve(),
            out_root=output_root / "transit_full_elf",
            thresholds=transit_thresholds,
            with_state_trace=args.with_state_trace,
            with_switch_seeding=args.with_switch_seeding,
        )
        summary["runs"]["transit_full_elf"] = transit_full_summary
        if not transit_full_summary["passes_thresholds"]:
            failed_checks.append("transit_full_elf")

    if not args.skip_f150:
        f150_summary = run_f150_full(
            analyze_headless=analyze_headless,
            repo=repo,
            image=Path(args.f150_elf).resolve(),
            out_root=output_root / "f150_full",
            thresholds=f150_thresholds,
        )
        summary["runs"]["f150_full"] = f150_summary
        if not f150_summary["passes_thresholds"]:
            failed_checks.append("f150_full")

    if args.baseline_summary:
        baseline_path = Path(args.baseline_summary).expanduser().resolve()
        baseline = json.loads(read_text(baseline_path))
        comparisons: dict[str, object] = {}
        for run_name, run_summary in summary["runs"].items():
            baseline_run = baseline.get("runs", {}).get(run_name)
            if not isinstance(baseline_run, dict):
                continue
            comparison = compare_run_metrics(run_summary, baseline_run)
            comparisons[run_name] = comparison
            if comparison["regressions"]:
                failed_checks.append(f"{run_name}:baseline")
        summary["baseline_summary"] = str(baseline_path)
        summary["comparisons"] = comparisons

    summary_path = output_root / "summary.json"
    write_json(summary_path, summary)

    print(f"summary: {summary_path}")
    for name, run in summary["runs"].items():
        print(f"[{name}]")
        print(json.dumps(run, indent=2, sort_keys=True))

    if failed_checks:
        print("FAILED: " + ", ".join(failed_checks), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
