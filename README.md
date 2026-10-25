<p align="center">
  <img src="./doc/images/logo.png" alt="Chipify" width="440">
</p>

# Examples for Chipify

Small circuits for learning [Chipify](https://github.com/santihofi/chipify):
parameter sweeps, measurement limits, yield, waveform overlays, equations,
exports, and batch reports.

The four ngspice introductions and the VACASK basics use ordinary components
and imported netlists. They need **no PDK and no Xschem installation**. Use
the installed IIC-OSIC-TOOLS container to run and verify the examples; it also
provides Xschem and IHP SG13G2 for the existing source-follower project. See
[container setup and verification](docs/vacask.md).

## Start here

Follow the projects in this order. Each directory is an independent Chipify
project; run its commands from that directory.

| Project | Cases | What it teaches |
| --- | ---: | --- |
| [Voltage divider](voltage_divider/README.md) | 6 | Jinja parameters, Cartesian sweeps, scalar measurements, limits, equations, scatter and corner-yield plots |
| [RC low-pass filter](rc_filter/README.md) | 3 + 3 | Transient and Bode overlays, waveform equations, grouping, logarithmic parameter spacing, combined batch reports |
| [Diode sweep](diode_sweep/README.md) | 6 | DC curves, temperature, relative model includes, sensitivity plots |
| [Resistor Monte Carlo](monte_carlo/README.md) | 64 | Seeded random variation, intentional spec failures, histograms, distribution analysis, LaTeX export |
| [VACASK basics](vacask_basics/README.md) | 24 | Native OP, transient, AC and DC analyses; raw-vector measurements; ngspice comparison in one datasheet |
| [IHP source follower](source_follower/README.md) | 27 / 1000 | Foundry corners, device mismatch, schematic entry, per-testbench ngspice/VACASK selection |

The measurement limits in the introductory projects are teaching examples,
not component guarantees. The Monte Carlo example intentionally has yield
below 100%; its runs should still complete without simulation errors.

## Install and run the first example

You need Python 3.11 or newer, Chipify, and the `ngspice` executable on your
`PATH`. On Debian/Ubuntu, ngspice is available with `sudo apt install ngspice`.
The GUI also needs the Qt system libraries described in
[Chipify's prerequisites](https://github.com/santihofi/chipify#prerequisites).

These tutorials were validated against Chipify commit
[`1960c81`](https://github.com/santihofi/chipify/commit/1960c8132a68676c9aa496f267d135d6f5af2d74).
The source install below includes the netlist-import, reports, and batch
features used here; older PyPI installations may not include all of them.

```bash
git clone https://github.com/santihofi/chipify-examples.git
cd chipify-examples
python3 -m venv .venv
source .venv/bin/activate
python -m pip install "git+https://github.com/santihofi/chipify.git@1960c8132a68676c9aa496f267d135d6f5af2d74"
ngspice --version
chipify-cli --version

cd voltage_divider
chipify-cli -c divider.yaml --reports --json
```

On Windows, create the environment with `python -m venv .venv` and activate
it with `.venv\Scripts\Activate.ps1` in PowerShell. Install ngspice separately
and add its executable directory to `PATH`.

The first run should report **6 total, 6 valid, 6 passed, 100% yield**.
It writes:

- `out/simulation_results.csv`: parameter values, measurements and verdicts.
- `out/history/`: timestamped CSVs and run metadata.
- `out/reports/<timestamp>/`: PNG/SVG plots, a PDF and a Markdown report.
- `out/reports/.latest`: the path of the newest report directory.

For the desktop workflow, launch `chipify` from `voltage_divider/`, select
`divider.yaml`, and start a simulation. Open Measurements, Histogram, and
Analytics to inspect the results. Use **Generate Reports** for the same
configured outputs. See the [feature walkthrough](docs/features.md).

## How a project fits together

```text
project/
├── project.yaml           # title, default datasheet, worker count, batch order
├── datasheets/*.yaml      # parameter values, limits, signal capture, reports
├── tb/*.spice or *.sim    # circuit and simulator commands, with Jinja parameters
├── models/                # optional local model files
└── out/                   # generated results; ignored by git
```

Chipify uses the launch directory as the project root. A command such as
`chipify-cli -c divider.yaml` searches `datasheets/` beneath that root;
`-c` is a datasheet filename, not the project directory.
The introductory projects use two workers via `default_num_cores` in
`project.yaml`. A local `settings.json` can override that preference.

## Guides

- [Datasheet and testbench guide](docs/datasheets.md): how the YAML, SPICE
  measurements, units, equations, and reports connect.
- [Feature walkthrough](docs/features.md): where to try each feature in the
  CLI and GUI, including batch and report-only runs.
- [Troubleshooting](docs/troubleshooting.md): missing tools, paths, capture,
  measurement errors, and expected failures.
- [VACASK and container verification](docs/vacask.md): native simulations,
  mixed engines, capture conventions, and reproducible checks.
- [Source-follower setup](source_follower/README.md): additional IHP/Xschem
  and VACASK requirements.

## Verify the examples in IIC-OSIC-TOOLS

With Docker running and the IIC-OSIC-TOOLS image installed, keep a Chipify
checkout beside this repository and run:

```bash
bash scripts/verify_in_container.sh --source-follower
```

Set `CHIPIFY_SOURCE` if the tool checkout is elsewhere. The script mounts
both checkouts read-only and runs temporary project copies using the image's
VACASK, ngspice, Xschem and PDK. It checks 82 introductory ngspice cases,
24 native/mixed VACASK cases, and both 27-case IHP corner sweeps. It also
checks numerical formulas, waveforms, report-only regeneration and a seeded
64-case repeat with a different worker count. CI uses the same wrapper.
See [the container guide](docs/vacask.md) for image selection and commands
inside an already running container.

For an installation without the container, the four ngspice introductions
can also be checked with `python scripts/verify_examples.py`. The native
VACASK suite uses `python scripts/verify_vacask.py`; add `--source-follower`
only with Xschem and the IHP PDK configured. Both Python scripts accept
`--validate-only` to check definitions without launching simulators.
These checks need no display or TeX installation. They do not run the legacy
1000-seed IHP mismatch experiment.

## License

Copyright (c) 2026 Santiago Hofwimmer BSc, Institute for Integrated Circuits
and Quantum Computing, Johannes Kepler University (JKU), Linz, Austria.
Licensed under the [Apache License 2.0](LICENSE).

[Chipify repository](https://github.com/santihofi/chipify) ·
[Tutorial channel](https://www.youtube.com/@chipify-eda)
