# Copyright (c) 2026 Santiago Hofwimmer
"""Check native VACASK tutorials and optionally the installed IHP corner examples."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import verify_examples as checks

DATASHEETS = {"vacask_basics": {"op.yaml": 6, "step.yaml": 3,
                               "frequency.yaml": 3, "dc.yaml": 6, "mixed.yaml": 6}}


def verify_native(workspace):
    import numpy as np
    import pandas as pd
    from chipify.uikit.services.equation_service import apply_transient_equations
    from chipify.util import Stimuli

    project = workspace / "vacask_basics"
    shutil.copytree(checks.ROOT / "vacask_basics", project,
                    ignore=shutil.ignore_patterns("out", "work", "__pycache__"))
    records = checks.run_cli(project, "--batch", "datasheets", "--reports")
    for record in records:
        if "yaml" in record:
            checks.check_reports(record, min_pages=2 if record["yaml"] == "frequency.yaml" else 3)
    for sheet, count in DATASHEETS["vacask_basics"].items():
        rows = checks.read_results(project / "out" / Path(sheet).stem, count)
        if sheet in {"op.yaml", "mixed.yaml"}:
            for row in rows:
                supply, top, bottom = (float(row[k]) for k in ("input_voltage", "r_top", "r_bottom"))
                expected = supply * bottom / (top + bottom)
                checks.require(math.isclose(float(row["vc_voltage"]), expected, rel_tol=1e-8),
                               "VACASK divider differs from the analytical voltage")
                checks.require(math.isclose(float(row["vc_current"]), supply / (top + bottom), rel_tol=1e-8),
                               "VACASK branch current differs from the analytical current")
                if sheet == "mixed.yaml":
                    checks.require(abs(float(row["vc_voltage"]) - float(row["ng_voltage"])) < 1e-5,
                                   "VACASK and ngspice disagree on the same divider case")
        elif sheet == "step.yaml":
            for row in rows:
                tau = float(row["resistance"]) * float(row["capacitance"]) + 1e-6
                checks.require(math.isclose(float(row["vc_time_63"]), tau, rel_tol=0.02),
                               "VACASK sampled rise time differs from R*C plus source delay")
        elif sheet == "dc.yaml":
            for row in rows:
                total = float(row["vc_forward_voltage"]) + float(row["vc_forward_current"]) * float(row["series_resistance"])
                checks.require(math.isclose(total, 1.0, abs_tol=5e-6), "VACASK diode violates KVL")

    step_dir = checks.check_waves(project / "out/step", "transient", "step", 3, ["time", "vin", "vout"])
    waveform = pd.read_csv(next(step_dir.glob("run_*.csv")))
    equations = Stimuli(project / "datasheets/step.yaml").transient_equations
    derived = apply_transient_equations(waveform, equations)
    checks.require("vc_resistor_drop" in derived and
                   np.allclose(derived.vc_resistor_drop, waveform.vin - waveform.vout),
                   "VACASK waveform equation failed")
    ac_out = project / "out/frequency"
    directory = checks.check_waves(ac_out, "ac", "frequency", 3, ["frequency", "vout_mag", "vout_phase"])
    rows = {row["run_id"].zfill(6): row for row in checks.read_results(ac_out, 3)}
    for path in directory.glob("run_*__frequency.csv"):
        row = rows[path.name[4:].split("__", 1)[0]]
        frame = pd.read_csv(path)
        tau = float(row["resistance"]) * float(row["capacitance"])
        expected = 1 / (1 + 2j * np.pi * frame.frequency.to_numpy() * tau)
        checks.require(np.allclose(frame.vout_mag, np.abs(expected), rtol=1e-5),
                       f"{path}: incorrect AC magnitude")
        checks.require(np.allclose(frame.vout_phase, np.degrees(np.angle(expected)), atol=1e-4),
                       f"{path}: incorrect AC phase")
    checks.check_waves(project / "out/dc", "dc", "clamp", 6, ["sweep", "vout"])
    batch = records[-1]
    checks.require([row["yaml"] for row in batch["batch_summary"]] == list(DATASHEETS["vacask_basics"]),
                   "VACASK batch order differs from project.yaml")
    saved = {path: (path.stat().st_mtime_ns, path.read_bytes()) for path in (project / "out").rglob("*.csv")}
    rebuilt = checks.run_cli(project, "--batch", "datasheets", "--report-only")
    checks.require(Path(rebuilt[-1]["combined_report"]).is_file(), "VACASK report-only produced no combined PDF")
    checks.require(all((path.stat().st_mtime_ns, path.read_bytes()) == before for path, before in saved.items()),
                   "VACASK report-only modified simulation data")
    print("VACASK: 24 cases, OP/DC/transient/AC data, mixed engines and reports passed.", flush=True)


def verify_source_follower(workspace):
    # Keep the shipped project intact; override worker count only in the test copy.
    project = workspace / "source_follower"
    shutil.copytree(checks.ROOT / "source_follower", project,
                    ignore=shutil.ignore_patterns("out", "work", "__pycache__"))
    settings_path = project / "settings.json"
    settings = json.loads(settings_path.read_text())
    settings.update(num_cores=2, sim_timeout_sec=30)
    settings_path.write_text(json.dumps(settings))
    for sheet in ("corners_ngspice.yaml", "corners_vacask.yaml"):
        records = checks.run_cli(project, "-c", sheet)
        checks.require(records[-1]["total"] == 27 and records[-1]["valid"] == 27,
                       f"{sheet}: IHP corner simulations failed")
        rows = checks.read_results(project / "out", 27)
        keys = ("outp", "outn", "gain", "bandwidth") if "vacask" in sheet else ("vd", "ve", "gain", "bandwidth")
        checks.require(all(math.isfinite(float(row[key])) for row in rows for key in keys),
                       f"{sheet}: missing or invalid circuit measurements")
        if "vacask" in sheet:
            checks.require(all(abs(float(row["outp"]) - float(row["outn"])) < 0.1 for row in rows),
                           "VACASK source-follower differential offset is unexpected")
        print(f"{sheet}: all 27 IHP cases passed in the container.", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--source-follower", action="store_true",
                        help="Also run both 27-case IHP corner datasheets; requires Xschem and the IHP PDK")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="chipify_vacask_examples_") as directory:
        workspace = Path(directory)
        checks.configure_environment(workspace)
        checks.validate_definitions(DATASHEETS)
        if not args.validate_only:
            checks.require(shutil.which("vacask") is not None, "VACASK is not on PATH")
            checks.require(shutil.which("ngspice") is not None, "ngspice is needed for the mixed-engine example")
            verify_native(workspace)
            if args.source_follower:
                checks.require(shutil.which("xschem") is not None, "Xschem is needed for the IHP source follower")
                verify_source_follower(workspace)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ImportError, OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        print(f"VACASK verification failed: {exc}", file=sys.stderr)
        sys.exit(1)
