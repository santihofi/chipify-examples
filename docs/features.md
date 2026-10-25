# Feature walkthrough

Run commands from the relevant project directory after the root
[installation steps](../README.md#install-and-run-the-first-example).

## Find a feature

| Feature | Example | Where to look |
| --- | --- | --- |
| Input sweeps and numeric limits | [Divider](../voltage_divider/README.md) | `parameters`, `tests`; Measurements tab |
| Scalar equations | [Divider](../voltage_divider/datasheets/divider.yaml) | `equations`; GUI equation results |
| Transient overlays and waveform equations | [RC step](../rc_filter/datasheets/step.yaml) | `transient_signals`, `transient_equations`; Plots / Transient |
| AC magnitude and phase | [RC frequency](../rc_filter/datasheets/frequency.yaml) | `ac_signals`; Plots / Bode |
| DC transfer curves and includes | [Diode](../diode_sweep/README.md) | `dc_signals`, local model; Plots / DC Sweep |
| Curve grouping and hover | [RC](../rc_filter/README.md) and [diode](../diode_sweep/README.md) | `group` in report plots; Group by and curve hover in the GUI |
| Scatter, corner yield, correlation | [Divider](../voltage_divider/datasheets/divider.yaml) | Named report plots; Analytics tab |
| Sensitivity/tornado | [Diode](../diode_sweep/datasheets/sweep.yaml) | `forward_voltage_sensitivity`; Analytics tab |
| Monte Carlo and spec failures | [Tolerance](../monte_carlo/README.md) | Seed range, histograms, fail breakdown |
| QQ, ECDF, yield versus spec | [Tolerance](../monte_carlo/README.md) | GUI Analytics modes and measurement selector |
| PNG, SVG, PDF, Markdown, LaTeX | [Tolerance](../monte_carlo/datasheets/tolerance.yaml) | `reports`, `--reports`, generated files |
| Batch order, combined PDF, report-only | [RC](../rc_filter/README.md) | `project.yaml`, CLI recipes below |
| Native VACASK OP, transient, AC and DC | [VACASK basics](../vacask_basics/README.md) | `.sim` decks, raw-vector reductions and waveform capture |
| Mixed VACASK/ngspice measurements | [Engine comparison](../vacask_basics/datasheets/mixed.yaml) | `engine` per testbench, distinct scalar names |
| Container verification | [Container guide](vacask.md) | Installed IIC-OSIC-TOOLS, temporary copies, numerical and report checks |
| Foundry PVT and load-dependent timing | [SKY130A / GF180MCU](pdks.md) | Installed model libraries, process corners, voltage/temperature and capacitive loads |
| Xschem and per-testbench engines | [Source follower](../source_follower/README.md) | `.sch` files and `engine` keys |

## Single-datasheet reports

In `voltage_divider/`:

```bash
chipify-cli -c divider.yaml --reports --json
chipify-cli -c divider.yaml --report-only --json
```

The second command uses the newest finished history run for that datasheet.
It regenerates figures and documents without launching the simulator. Keep
measurement limits and testbench identity unchanged when regenerating an
old run; use a copied datasheet and a new simulation to explore changed specs.

The CLI prints the generated paths. `.latest` is a text file naming the
newest report directory, not a symlink or a PDF itself.

## Combined batch report

In `rc_filter/`:

```bash
chipify-cli --batch datasheets --reports --json
chipify-cli --batch datasheets --report-only --json
```

Batch mode searches `*.yaml` in the supplied directory. `datasheet_order`
in `project.yaml` determines the order; its `name` and `description` supply
the combined report title/subtitle. Each datasheet's `description` appears
on its own cover and in the batch summary.

Per-datasheet outputs are under `out/<datasheet-stem>/`. The combined PDF is
under the project's `out/reports/<timestamp>/`. The final JSON line records
its path as `combined_report` alongside the per-datasheet summaries.

## GUI tour

1. Launch `chipify` from a project directory and choose a datasheet. Run a
   simulation, or select a timestamped history entry for that datasheet.
2. In **Datasheet Editor**, change parameter values or specs; **Reports…**
   edits the report block. The equations panel edits scalar/waveform equations.
3. In **Measurements**, check PASS/FAIL/ERROR, failure counts and worst cases.
4. In **Histogram**, choose a measured output, a fit and an optional grouping.
5. In **Analytics**, try the relevant scatter, correlation, corner-yield,
   tornado or distribution mode.
6. In **Plots**, choose Transient, DC Sweep or Bode. Select signals, group by
   a swept parameter, and hover a curve to inspect its run.
7. Open **Multi-Plot Dashboard** to arrange several views, then use individual
   plot export actions or **Generate Reports** for the configured files.

The report plot registry currently offers scatter, histogram, transient,
DC, Bode, corner yield, correlation, tornado and fail breakdown. QQ/ECDF/
yield-versus-spec are built-in GUI plot plugins; they are not `reports.plots`
type names in the validated Chipify revision.

## Run selections and output formats

Waveform report plots accept `runs: all_valid`, `runs: failing`, or
`runs: first:1`. The RC/diode examples use all valid cases and explicit
signals. Overlays are capped at 500 selected runs, so use smaller selections
when plotting a large Monte Carlo experiment.

Use `formats: [latex]` on a supported plot to produce a CSV and pgfplots TeX
source. The Monte Carlo histogram is a complete example. Its figure is
ungrouped so the same distribution is represented in every requested format.

See [troubleshooting](troubleshooting.md) if expected figures or measurements
are missing.
