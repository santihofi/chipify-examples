# Copyright (c) 2026 Santiago Hofwimmer
"""Check the PDK-free tutorials in temporary projects using real ngspice."""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
DATASHEETS = {
    "voltage_divider": {"divider.yaml": 6},
    "rc_filter": {"step.yaml": 3, "frequency.yaml": 3},
    "diode_sweep": {"sweep.yaml": 6},
    "monte_carlo": {"tolerance.yaml": 64},
}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def validate_definitions(definitions=None):
    definitions = DATASHEETS if definitions is None else definitions
    from jinja2 import StrictUndefined, Template
    import yaml
    from chipify.schema import validate_datasheet

    total_cases = 0
    total_sheets = 0
    for project, sheets in definitions.items():
        for name, expected in sheets.items():
            path = ROOT / project / "datasheets" / name
            stim = validate_datasheet(yaml.safe_load(path.read_text()))
            count = math.prod(len(values) for values in stim.params.values())
            total_cases += count
            total_sheets += 1
            require(count == expected, f"{path}: expected {expected} cases, got {count}")
            names = [value.name for test in stim.tests for value in test.value_lst]
            require(len(names) == len(set(names)), f"{path}: duplicate measurements")
            require(not set(names) & set(stim.params), f"{path}: measurement/input collision")
            for test in stim.tests:
                require(test.engine in {"ngspice", "vacask"} and test.netlist_source == "netlist",
                        f"{path}: introductory benches must use imported netlists")
                extension = ".sim" if test.engine == "vacask" else ".spice"
                deck = ROOT / project / "tb" / f"{test.tb_path}{extension}"
                require(deck.is_file(), f"{path}: missing testbench {deck}")
                first = {key: values[0] for key, values in stim.params.items()}
                rendered = Template(deck.read_text(), undefined=StrictUndefined).render(**first)
                if test.engine == "vacask":
                    require(rendered.endswith("\n"),
                            f"{deck}: VACASK needs a final newline after template rendering")
            plot_names = [spec.name for spec in stim.reports.plots]
            require(all(plot_names) and len(plot_names) == len(set(plot_names)),
                    f"{path}: plot names must be explicit and unique")

    # Catch broken navigation, including references to the legacy project.
    for path in ROOT.rglob("*.md"):
        if any(part in {".git", ".venv", "out"} for part in path.relative_to(ROOT).parts):
            continue
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", path.read_text()):
            if "://" in target or target.startswith("#"):
                continue
            destination = target.split("#", 1)[0]
            require((path.parent / destination).exists(), f"{path}: broken link {target}")
    print(f"Validated {total_sheets} datasheets ({total_cases} cases), templates and local documentation links.")


def run_cli(project, *args, timeout=240):
    completed = subprocess.run(
        [sys.executable, "-m", "chipify.cli", *args, "--json"],
        cwd=project, capture_output=True, text=True, timeout=timeout,
    )
    log = completed.stdout + "\n" + completed.stderr
    (project / "verification.log").write_text(log)
    require(completed.returncode == 0, f"{project.name}: CLI failed\n{log[-6000:]}")
    warnings = [line for line in completed.stdout.splitlines() if line.startswith("[!]")]
    require(not warnings, f"{project.name}: unexpected warning(s): {warnings}")
    return [json.loads(line) for line in completed.stdout.splitlines()
            if line.startswith("{")]


def read_results(out_dir, expected, allow_fail=False):
    with (out_dir / "simulation_results.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    require(len(rows) == expected, f"{out_dir}: wrong case count")
    for row in rows:
        require(row["sim_error"] == "None", f"{out_dir}: {row['sim_error']}")
        require(not any(key.endswith("_capture") and value for key, value in row.items()),
                f"{out_dir}: waveform capture failed")
        if not allow_fail:
            require(row["global_pass"] == "True", f"{out_dir}: unexpected spec failure")
    return rows


def check_reports(record, min_pages=3):
    from pypdf import PdfReader

    directory = Path(record["reports_dir"])
    require(record["crashes"] == 0, f"{record['yaml']}: simulator errors")
    for extension in ("png", "svg", "pdf", "md"):
        paths = list(directory.glob(f"*.{extension}"))
        require(paths and all(path.stat().st_size > 0 for path in paths),
                f"{directory}: missing/empty {extension} outputs")
    for path in directory.glob("*.pdf"):
        require(len(PdfReader(path).pages) >= min_pages, f"{path}: incomplete report")


def check_waves(out_dir, kind, bench, expected, columns):
    import pandas as pd

    # Resolve through the saved run's metadata, rather than the latest pointer.
    sidecars = sorted((out_dir / "history").glob("run_*.meta.json"))
    require(bool(sidecars), f"{out_dir}: no history metadata")
    metadata = json.loads(sidecars[-1].read_text())
    directory = out_dir / metadata["analysis_dirs"][kind]
    paths = list(directory.glob(f"run_*__{bench}.csv"))
    require(len(paths) == expected, f"{directory}: expected {expected} waveform CSVs")
    for path in paths:
        frame = pd.read_csv(path)
        require(len(frame) >= 100 and set(columns) <= set(frame.columns),
                f"{path}: incomplete waveform")
        require(frame[columns].notna().all().all(), f"{path}: invalid waveform values")
    return directory


def verify_runtime(workspace):
    import pandas as pd
    from pypdf import PdfReader
    from chipify.uikit.services.equation_service import (
        apply_scalar_equations, apply_transient_equations,
    )
    from chipify.util import Stimuli

    projects = {}
    records = {}
    for name in DATASHEETS:
        project = workspace / name
        shutil.copytree(ROOT / name, project,
                        ignore=shutil.ignore_patterns("out", "work", "__pycache__"))
        projects[name] = project
        args = (["--batch", "datasheets"] if name == "rc_filter"
                else ["-c", next(iter(DATASHEETS[name]))])
        records[name] = run_cli(project, *args, "--reports")
        for record in records[name]:
            if "yaml" in record:
                check_reports(record)
        print(f"{name}: real simulation and reports passed", flush=True)

    divider = projects["voltage_divider"]
    rows = read_results(divider / "out", 6)
    for row in rows:
        vin, top, bottom = (float(row[key]) for key in ("vin", "r_top", "r_bottom"))
        for key, expected in {
            "divider_vout": vin * bottom / (top + bottom),
            "divider_gain": bottom / (top + bottom),
            "divider_current": vin / (top + bottom),
        }.items():
            require(math.isclose(float(row[key]), expected, rel_tol=1e-5),
                    f"divider: {key} differs from the analytical result")
    stim = Stimuli(divider / "datasheets/divider.yaml")
    frame = pd.read_csv(divider / "out/simulation_results.csv")
    derived, names, logs = apply_scalar_equations(frame, stim.equations)
    require("divider_power_mw" in names, f"Scalar equation failed: {logs}")
    require(((derived.divider_power_mw - frame.vin * frame.divider_current * 1000).abs()
             < 1e-10).all(), "Divider power equation is incorrect")

    rc = projects["rc_filter"]
    step_out, ac_out = rc / "out/step", rc / "out/frequency"
    for row in read_results(step_out, 3):
        expected = float(row["resistance"]) * float(row["capacitance"]) + 1e-6
        require(math.isclose(float(row["step_time_63"]), expected, rel_tol=0.003),
                "RC step time differs from R*C plus the source delay")
    for row in read_results(ac_out, 3):
        expected = 1 / (2 * math.pi * float(row["resistance"]) * float(row["capacitance"]))
        require(math.isclose(float(row["ac_cutoff"]), expected, rel_tol=0.003),
                "RC cutoff differs from 1/(2*pi*R*C)")
    step_dir = check_waves(step_out, "transient", "step", 3, ["time", "v(in)", "v(out)"])
    check_waves(ac_out, "ac", "frequency", 3, ["frequency", "v(out)_mag", "v(out)_phase"])
    waveform = pd.read_csv(next(step_dir.glob("run_*.csv")))
    equations = Stimuli(rc / "datasheets/step.yaml").transient_equations
    derived = apply_transient_equations(waveform, equations)
    require("resistor_drop" in derived and
            ((derived.resistor_drop + derived["v(out)"] - derived["v(in)"]).abs()
             < 1e-10).all(), "Transient equation is incorrect")
    combined = records["rc_filter"][-1]
    require([row["yaml"] for row in combined["batch_summary"]] ==
            ["step.yaml", "frequency.yaml"], "Batch ignored datasheet_order")
    outline = PdfReader(combined["combined_report"]).outline
    require([entry["/Title"] for entry in outline if isinstance(entry, dict)] ==
            ["Summary", "step", "frequency"], "Combined PDF bookmarks are incomplete")
    saved = {path: (path.stat().st_mtime_ns, path.read_bytes())
             for path in (rc / "out").rglob("*.csv")}
    rebuilt = run_cli(rc, "--batch", "datasheets", "--report-only")
    require(Path(rebuilt[-1]["combined_report"]).is_file(), "Report-only produced no batch PDF")
    require(all((path.stat().st_mtime_ns, path.read_bytes()) == previous
                for path, previous in saved.items()), "Report-only rewrote simulation data")

    diode = projects["diode_sweep"] / "out"
    for row in read_results(diode, 6):
        voltage = float(row["diode_forward_voltage"])
        current = float(row["diode_forward_current"])
        require(math.isclose(voltage + current * float(row["series_resistance"]),
                             1.0, abs_tol=5e-6), "Diode measurements violate the circuit KVL")
    check_waves(diode, "dc", "clamp", 6, ["sweep", "v(out)"])

    mc = projects["monte_carlo"]
    rows = read_results(mc / "out", 64, allow_fail=True)
    require(0 < sum(row["global_pass"] == "True" for row in rows) < 64,
            "Monte Carlo must demonstrate both passing and failing samples")
    first = {row["seed"]: (row["mc_gain"], row["mc_offset"]) for row in rows}
    require(len(first) == 64, "Monte Carlo repeated a seed")
    report_dir = Path(records["monte_carlo"][0]["reports_dir"])
    for filename in ("gain_distribution_plot.csv", "gain_distribution_plot.tex"):
        require((report_dir / filename).stat().st_size > 0, f"Missing LaTeX export: {filename}")
    # A different worker count must preserve the sample associated with a seed.
    (mc / "settings.json").write_text(json.dumps({"num_cores": 1}))
    run_cli(mc, "-c", "tolerance.yaml")
    repeated = read_results(mc / "out", 64, allow_fail=True)
    second = {row["seed"]: (row["mc_gain"], row["mc_offset"]) for row in repeated}
    require(first == second, "Monte Carlo values changed when rerun with one worker")
    print("Analytical checks, waveform/equation checks, batch report-only and seeded rerun passed.")


def configure_environment(workspace):
    # Keep user plugins and plotting caches out of reproducibility checks.
    os.environ["CHIPIFY_PLUGINS"] = str(workspace / "plugins")
    os.environ["MPLCONFIGDIR"] = str(workspace / "matplotlib")
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    os.environ["OPENBLAS_NUM_THREADS"] = "1"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate-only", action="store_true",
                        help="Check definitions and local links without launching ngspice")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="chipify_examples_") as directory:
        workspace = Path(directory)
        configure_environment(workspace)
        validate_definitions()
        if not args.validate_only:
            require(shutil.which("ngspice") is not None, "ngspice is not on PATH")
            verify_runtime(workspace)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ImportError, OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        print(f"Verification failed: {exc}", file=sys.stderr)
        sys.exit(1)
