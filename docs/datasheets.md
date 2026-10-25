# Datasheets and testbenches

Start with the fully commented
[voltage-divider datasheet](../voltage_divider/datasheets/divider.yaml) and its
[testbench](../voltage_divider/tb/divider.spice).

## Responsibilities

| File/block | Responsibility |
| --- | --- |
| `tb/*.spice`, `tb/*.sim` or an Xschem testbench | Circuit, simulator analyses, and raw vectors or named measurements |
| `parameters:` | Values substituted into the testbench for every parameter case |
| `tests:` | Testbench selection, measurement limits, and requested waveform signals |
| `equations:` | Derived scalar results for the GUI |
| `transient_equations:` | Derived time-dependent signals |
| `reports:` | Plots, formats and documents to generate when requested |
| `project.yaml` | Shared defaults, project title, and batch order |

Simulator commands stay in the testbench. Chipify supplies measurement and
waveform capture automatically.

## Parameters and case count

Parameters form a Cartesian product: three values of one input and two of
another give six cases. A scalar is accepted as a single-value parameter,
but explicit lists make these examples easier to read.

The supported sequence strings are:

- `range(1, 65)`: values 1 through 64; the stop is excluded.
- `linspace(1.8, 5, 5)`: five evenly spaced values including both endpoints.
- `logspace(-7, -6, 3)`: three values between 10^-7 and 10^-6.

Use the Jinja placeholder `{{ name }}` in the deck for a swept parameter.
Current Chipify expands range values as floats; use `{{ seed | int }}` when
passing a positive seed to ngspice's `setseed`. The Monte Carlo testbench
shows the complete pattern.

## Testbench selection and scalar measurements

`tests.divider` selects `tb/divider.spice` when it has `source: netlist` and
`engine: ngspice`. With the default `source: xschem`, the same key selects
`tb/divider.sch`. VACASK netlists use `.sim` and `engine: vacask`.

For ngspice, every scalar measurement key must match a vector that the testbench defines.
For example, `divider_vout` in the YAML matches `let divider_vout = v(out)`.
Keep measurement names unique across all testbenches in one datasheet, and
use separate names for parameters, equations, and measured outputs.

For VACASK, the testbench's `measure:` mapping reduces raw vectors while
the measurement's own mapping supplies its limits:

```yaml
tests:
  divider:
    source: netlist
    engine: vacask
    measure:
      vc_voltage: last(vout)
    vc_voltage: {min: 0.8, max: 3.4, unit: V}
```

Raw names are plain node names; `vinput:flow(br)` becomes
`vinput_flow_br_`. See [VACASK basics](../vacask_basics/README.md) for
OP, waveform reductions, DC and mixed-engine examples. Retain the final
blank line in native `.sim` templates so Jinja rendering leaves the newline
VACASK requires after `endc`.

`min` and `max` are inclusive acceptance limits. `typ` is a reference value;
it does not introduce another sweep or an acceptance test. An empty mapping
such as `measurement: {}` still collects a value without numeric limits.

Use numeric values in base units: `0.00005` or `5e-5` for 50 uA, rather than
a SPICE suffix string such as `50u` in a YAML limit. `unit: A` labels the
measurement; it does not rescale the value or change the pass/fail math.

## Waveform capture

Declare the signals appropriate to the analysis that the testbench runs:

| Datasheet key | Testbench command | GUI mode |
| --- | --- | --- |
| `transient_signals` | `tran` | Transient |
| `dc_signals` | `dc` | DC Sweep |
| `ac_signals` | `ac` | Bode |

The RC and diode projects demonstrate these keys. For Bode plots, request a
complex AC signal such as `v(out)`, not an already converted dB vector.
The examples keep one analysis per testbench to make capture and measurements
easy to follow.

Define an actual `.control` block in each ngspice deck. Let Chipify inject
the scalar echo and `wrdata` capture; do not add them yourself or enable
`set wr_vecnames`. Avoid mentioning control-block delimiters in comments,
because the current capture injector locates them by text.

## Equations

`equations:` computes one result per parameter case. The divider's
`divider_power_mw` uses measured supply current and its input voltage.
Current Chipify applies these scalar equations when the GUI loads results;
headless reports in these examples use measured outputs instead.

`transient_equations:` computes a signal at every time sample. The RC step
datasheet's `resistor_drop` subtracts `v(out)` from `v(in)` and can be selected
or exported like a captured signal, including in CLI transient reports.

Names must be identifiers, such as `resistor_drop`. Expressions use the
available columns and math helpers, rather than arbitrary Python imports.
Do not reuse a measured column or bookkeeping name for an equation.

## Reports and verdicts

Add `--reports` to the CLI command or press **Generate Reports** in the GUI
to generate the datasheet's configured output. Without that request, running
a simulation writes its result CSV/history, not all configured reports.

Use explicit, distinct plot `name` values. `formats: [png, svg]` sets image
defaults; a plot can override them. Set `pdf: true` or `markdown: true` for
documents, and `plots_per_page: 2` to place two configured plots on a PDF page.
LaTeX is available for histograms and transient/DC/Bode overlays.

PASS means the usable measurements met their limits. FAIL means a measured
value was outside a limit. ERROR means a trustworthy measurement was not
available. Inspect the summary's `valid`, `crashes` and `yield` fields; a
zero CLI exit code alone is not a claim that all measurements passed.

For more recipes, see [features](features.md) and
[troubleshooting](troubleshooting.md).
