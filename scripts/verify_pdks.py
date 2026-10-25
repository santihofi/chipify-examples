# Copyright (c) 2026 Santiago Hofwimmer
"""Verify the installed SKY130A and GF180MCU ngspice inverter examples."""
from __future__ import annotations

import argparse
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import verify_examples as checks

DATASHEETS = {
    "sky130a_inverter": {"transfer.yaml": 27, "timing.yaml": 6},
    "gf180_inverter": {"transfer.yaml": 27, "timing.yaml": 6},
}
MODEL_FILES = {
    "sky130a_inverter": ("sky130A/libs.tech/ngspice/sky130.lib.spice",),
    "gf180_inverter": ("gf180mcuD/libs.tech/ngspice/design.ngspice",
                       "gf180mcuD/libs.tech/ngspice/sm141064.ngspice"),
}


def crossing_times(time, voltage, level, rising):
    """Linearly interpolate saved samples; independent of ngspice meas output."""
    import numpy as np

    before, after = voltage[:-1] - level, voltage[1:] - level
    mask = ((before < 0) & (after >= 0) if rising
            else (before > 0) & (after <= 0))
    index = np.flatnonzero(mask)
    return time[index] - before[index] * (time[index + 1] - time[index]) / (after[index] - before[index])


def check_transfer(project):
    import numpy as np
    import pandas as pd

    out = project / "out/transfer"
    rows = {row["run_id"].zfill(6): row for row in checks.read_results(out, 27)}
    directory = checks.check_waves(out, "dc", "transfer", 27, ["sweep", "v(in)", "v(out)"])
    for path in directory.glob("run_*__transfer.csv"):
        row = rows[path.name[4:].split("__", 1)[0]]
        frame = pd.read_csv(path)
        supply = float(row["supply"])
        vin, vout = frame["v(in)"].to_numpy(), frame["v(out)"].to_numpy()
        checks.require(np.isfinite(frame.to_numpy()).all(), f"{path}: non-finite DC samples")
        checks.require(np.allclose(frame["sweep"], vin) and np.all(np.diff(vin) > 0),
                       f"{path}: incorrect input sweep axis")
        checks.require(abs(vin[0]) < 1e-6 and abs(vin[-1] - supply) < 1e-5,
                       f"{path}: sweep did not reach both supply rails")
        checks.require(vout[0] > 0.99 * supply and abs(vout[-1]) < 0.01 * supply,
                       f"{path}: inverter does not invert its DC input")
        checks.require(np.all(np.diff(vout) <= 0.002 * supply),
                       f"{path}: DC transfer is not monotonic")
        switch = np.interp(supply / 2, vout[::-1], vin[::-1])
        checks.require(math.isclose(float(row["inv_switch_voltage"]), switch, abs_tol=1e-5),
                       f"{path}: scalar switching voltage disagrees with saved curve")
        for column, expected in (("inv_output_high", vout[0]), ("inv_output_low", vout[-1])):
            checks.require(math.isclose(float(row[column]), expected, rel_tol=1e-4, abs_tol=1e-6),
                           f"{path}: {column} disagrees with saved curve")


def check_timing(project):
    import numpy as np
    import pandas as pd

    out = project / "out/timing"
    rows = {row["run_id"].zfill(6): row for row in checks.read_results(out, 6)}
    directory = checks.check_waves(out, "transient", "timing", 6, ["time", "v(in)", "v(out)"])
    for path in directory.glob("run_*__timing.csv"):
        row = rows[path.name[4:].split("__", 1)[0]]
        frame = pd.read_csv(path)
        supply = float(row["supply"])
        time, vin, vout = (frame[key].to_numpy() for key in ("time", "v(in)", "v(out)"))
        checks.require(np.isfinite(frame.to_numpy()).all() and np.all(np.diff(time) > 0),
                       f"{path}: invalid transient samples")
        for key, rising in (("inv_tphl", True), ("inv_tplh", False)):
            trigger = crossing_times(time, vin, supply / 2, rising)
            target = crossing_times(time, vout, supply / 2, not rising)
            checks.require(len(trigger) >= 2 and len(target) >= 2, f"{path}: missing switching edges")
            delay = target[1] - trigger[1]
            checks.require(delay > 0 and math.isclose(float(row[key]), delay, rel_tol=0.01, abs_tol=1e-13),
                           f"{path}: {key} disagrees with independently interpolated edges")
        low, high = (time > 2e-9) & (time < 9e-9), (time > 13e-9) & (time < 19e-9)
        checks.require(low.any() and high.any() and np.max(np.abs(vout[low])) < 0.01 * supply
                       and np.min(vout[high]) > 0.99 * supply,
                       f"{path}: output failed to settle to inverted logic levels")
    for corner in {row["corner"] for row in rows.values()}:
        pair = sorted((row for row in rows.values() if row["corner"] == corner),
                      key=lambda row: float(row["load_capacitance"]))
        checks.require(len(pair) == 2, f"{project.name}: missing load pair at {corner}")
        checks.require(all(float(pair[1][key]) > float(pair[0][key]) for key in ("inv_tphl", "inv_tplh")),
                       f"{project.name}: larger capacitive load did not increase delay at {corner}")


def verify_project(name, workspace, pdk_root):
    import yaml
    from pypdf import PdfReader

    for relative in MODEL_FILES[name]:
        checks.require((pdk_root / relative).is_file(), f"Missing PDK model: {pdk_root / relative}")
    project = workspace / name
    shutil.copytree(checks.ROOT / name, project,
                    ignore=shutil.ignore_patterns("out", "work", "__pycache__"))
    for path in (project / "datasheets").glob("*.yaml"):
        definition = yaml.safe_load(path.read_text())
        definition["parameters"]["pdk_root"] = [str(pdk_root)]
        path.write_text(yaml.safe_dump(definition, sort_keys=False))
    records = checks.run_cli(project, "--batch", "datasheets", "--reports", timeout=600)
    summaries = [record for record in records if "yaml" in record]
    checks.require([record["yaml"] for record in summaries] == list(DATASHEETS[name]),
                   f"{name}: incorrect batch order")
    for record in summaries:
        count = DATASHEETS[name][record["yaml"]]
        checks.require(record["total"] == record["valid"] == record["passed"] == count,
                       f"{name}: incomplete or failing {record['yaml']}")
        checks.check_reports(record)
    combined = Path(records[-1]["combined_report"])
    checks.require(combined.is_file() and len(PdfReader(combined).pages) >= 7,
                   f"{name}: missing or incomplete combined report")
    check_transfer(project)
    check_timing(project)
    print(f"{name}: 27 PVT transfer cases, six loaded timing cases, waveform checks and reports passed.", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--pdk-root", type=Path, default=Path(os.environ.get("PDK_ROOT", "/foss/pdks")),
                        help="Installed PDK root (default: PDK_ROOT or /foss/pdks)")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="chipify_pdk_examples_") as directory:
        workspace = Path(directory)
        checks.configure_environment(workspace)
        checks.validate_definitions(DATASHEETS)
        if not args.validate_only:
            checks.require(shutil.which("ngspice") is not None, "ngspice is not on PATH")
            # Both models need HSPICE compatibility before deck parsing. The
            # image's default PDK can be IHP; isolate this override to this process.
            os.environ["SPICE_USERINIT_DIR"] = str(checks.ROOT / "scripts/pdk-ngspice")
            for name in DATASHEETS:
                verify_project(name, workspace, args.pdk_root.resolve())
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ImportError, OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        print(f"PDK verification failed: {exc}", file=sys.stderr)
        sys.exit(1)
