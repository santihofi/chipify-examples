# RC filter: waveforms and a batch report

One resistor and one capacitor demonstrate transient and AC analyses, three
parameter corners, waveform equations, and grouped overlays.

```text
in ── Rseries ──┬── out
               Cload
                 │
                 0
```

## Run both analyses

From this directory:

```bash
chipify-cli --batch datasheets --reports --json
```

The two datasheets each run three cases; all six should pass without errors.
[project.yaml](project.yaml) puts the step response before the frequency
response in the combined report.

Batch output is isolated by datasheet:

```text
out/
├── step/                   # results, history, transient waveforms, reports
├── frequency/              # results, history, AC waveforms, reports
└── reports/<timestamp>/batch_report_<timestamp>.pdf
```

The combined PDF has a summary, start-page references and bookmarks, followed
by each datasheet's own report. To regenerate it from the saved runs:

```bash
chipify-cli --batch datasheets --report-only --json
```

## Step response

[step.yaml](datasheets/step.yaml) captures `v(in)` and `v(out)` from
[step.spice](tb/step.spice). `logspace(-7, -6, 3)` selects approximately
100 nF, 316 nF and 1 uF with a 1 kohm resistor.

The time constant `R × C` is approximately 100 us, 316 us or 1 ms.
`step_time_63` measures when the output reaches 63.2% of its final value;
it includes the source's 1 us delay. At 8 ms every corner is within 1 mV
of the final 1 V output.

The datasheet's `resistor_drop = v(in) - v(out)` is a waveform equation.
The exported plot shows it alongside `v(out)`, grouped by capacitance.
Unlike a scalar equation, it evaluates at every time sample.

## Frequency response

[frequency.yaml](datasheets/frequency.yaml) captures the complex `v(out)`
from [frequency.spice](tb/frequency.spice). Chipify derives the Bode magnitude
in dB and phase in degrees; the AC source amplitude is 1 V.

The analytical cutoff is `1 / (2 × pi × R × C)`: approximately 1.59 kHz,
503 Hz and 159 Hz. `ac_cutoff` measures the -3 dB point. Larger capacitors
give a slower step and a lower bandwidth.

## GUI and experiments

For GUI history and plotting, run a single datasheet from this directory:

```bash
chipify-cli -c step.yaml --reports
chipify
```

Select `step.yaml` and load its timestamped history run, or start a new run
in the GUI. In Plots, choose Transient, select the signals, and group by
`capacitance`. Repeat with `frequency.yaml` and Bode mode. Hover a curve to
see its run and parameters; use the Multi-Plot Dashboard to arrange views.
The current GUI history selector does not discover the CLI's nested batch
history folders, which is why the command above uses a single datasheet.

Try doubling `resistance` in both datasheets, then rerun the batch. The step
time should double and cutoff should halve; some original limits will now
fail. Use `runs: first:1` in a report
plot to export just one valid run instead of all three.

Next: [diode sweep](../diode_sweep/README.md) for DC capture and model includes.
