# Troubleshooting

## A command or datasheet is not found

Activate the environment where Chipify is installed, and check
`chipify-cli --version` and `ngspice --version`. A missing executable and a
simulation that ran but failed are different problems.

Launch from the example's project directory. For example:

```bash
cd voltage_divider
chipify-cli -c divider.yaml --reports --json
```

Use the filename `divider.yaml`, rather than `datasheets/divider.yaml`, with
`-c`. If an older Chipify rejects `--reports`, `--report-only` or `--batch`,
use the source installation documented in the root README.

## Results say FAIL

Check `crashes` and `valid` in the JSON summary. The Monte Carlo tutorial
intentionally produces some valid out-of-spec runs. Its failure counts
demonstrate yield analysis; they are not installation failures.

In the GUI, inspect the measurement limits and worst-case conditions. Keep
units in mind: the YAML `unit` field is a label, not a scale conversion.

## Results say ERROR, or measurements are missing

Read `out/chipify.log`, the result CSV's error fields, and the GUI's simulation
error section. For these ngspice examples, every scalar key must have a
matching `let` or `meas` vector in the deck. A misspelled vector can leave
the managed measurement output incomplete.

For waveforms, make sure the testbench runs the corresponding `tran`, `dc`
or `ac` analysis and that the requested signals exist. Keep one analysis
per testbench as in these tutorials. Let Chipify own scalar echo/`wrdata`
capture and leave `set wr_vecnames` disabled.

## A model include works manually but fails in Chipify

Simulator decks execute in scratch space. Relative include paths are resolved
against the testbench directory, not the launch directory. Follow the
[diode example](../diode_sweep/tb/clamp.spice): its model lives in `../models/`
relative to `tb/`. Bare filenames can instead come from the project's
`work/` directory for staged `.lib`, `.mod` and `.inc` files.

Regenerate persisted netlist templates after moving a project: resolved
include paths in those templates can be absolute host paths.

## Reports or GUI history do not show what you expect

- Add `--reports` or use Generate Reports; a `reports:` block alone does not
  request generation during an ordinary CLI simulation.
- Batch output lives under `out/<datasheet-stem>/`; single-datasheet output
  lives directly under `out/`. Use the same mode for simulation and report-only.
- Current GUI history only discovers the single-project `out/history/`.
  Run a single datasheet when following the GUI tutorials.
- Select the matching datasheet and a named history run before inspecting
  results. Keep the run's waveform folders with its CSV and metadata.
- Top-level scalar equations are currently applied in the GUI. The supplied
  CLI report configurations use measured scalars; transient equations also
  work in the CLI's transient renderer.
- Changing a datasheet's limits does not reliably regrade old saved verdicts.
  Use a copied datasheet and run a new simulation for a changed specification.

## A run times out

The supplied circuits are small and should finish well within the default
per-run timeout. For larger experiments, set `sim_timeout_sec` in the GUI's
Settings / Simulation panel or in a project-local `settings.json`.
Use `num_cores` to limit simultaneous workers on memory-constrained machines.
The introductory projects default to two workers.

## The IHP source follower cannot find models or symbols

That project additionally needs Xschem, IHP SG13G2, and the PDK's ngspice
initialization, including its compiled device models. Follow
[its setup guide](../source_follower/README.md); the four introductory
projects do not need this environment.

## VACASK reports a syntax error at the end of the file

Keep an extra blank line after `endc` in `.sim` templates. Jinja removes one
trailing newline when Chipify renders a deck; the tested VACASK parser needs
a newline after the final command. See the supplied
[divider template](../vacask_basics/tb/divider.sim).

## VACASK warns about PyOPUS or has missing measurements

The optional PyOPUS `RawFile` API is unavailable in the tested image, but
Chipify's built-in reader handles the new decks' ASCII raw files. Inspect
actual values and capture files before treating the warning as a failed run.
Use plain node names such as `vout`, scalar reductions such as `last(vout)`,
and one analysis per deck. See [VACASK compatibility](vacask.md#capture-and-compatibility).

## SKY130A or GF180 models fail to load, time out, or have incorrect dimensions

Use the [shared PDK initialization and model setup](pdks.md#model-setup-and-geometry)
before launching Chipify. Set `SPICE_USERINIT_DIR` to its absolute directory;
the container's default IHP initialization and a project-local `.spiceinit`
are insufficient for these runs in Chipify's scratch directory. Keep the
60-second timeout from the supplied project settings for model loading.

Check `pdk_root` in both datasheets. GF180's installed directory is
`gf180mcuD`, its typical corner is `typical`, and it needs `design.ngspice`
before the corner library. SKY130 and GF180 also use different geometry
conventions; use the supplied transistor instance lines as a reference.
