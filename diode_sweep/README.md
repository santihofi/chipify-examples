# Diode clamp: a DC sweep with a local model

This circuit uses ngspice's built-in diode model. It needs no foundry PDK.

```text
in ── Rseries ──┬── out
              Dclamp
                 │
                 0
```

## Run

From this directory:

```bash
chipify-cli -c sweep.yaml --reports --json
```

The three temperatures and two resistances give six parameter cases. All
six should pass. Each case contains a DC sweep of the input from 0 to 1 V
in 10 mV increments; those 101 waveform points are not additional Chipify
parameter cases.

## What to inspect

- [tb/clamp.spice](tb/clamp.spice) runs the DC analysis and measures the diode
  voltage and forward current at the final 1 V input.
- [models/diode.lib](models/diode.lib) defines an illustrative generic diode.
  Its relative include is resolved from `tb/clamp.spice`, so it works when
  Chipify runs the rendered deck from its scratch directory.
- [datasheets/sweep.yaml](datasheets/sweep.yaml) selects `dc_signals`, groups
  the transfer curves by temperature, and requests a sensitivity plot.

The output initially follows the input, then the diode conducts and limits
the voltage. Its forward voltage falls as temperature rises. At the final
input point, current is approximately `(1 - diode_forward_voltage) /
series_resistance`.

The tornado chart summarizes correlation with the swept inputs; it is not a
causal model or a transistor-level sensitivity derivative.

## Try it

Launch `chipify` from this directory and run `sweep.yaml`. In Plots, choose
**DC Sweep**, select `v(out)`, and change Group by between `temperature` and
`series_resistance`.

Add a temperature or edit the diode model, then run again. Keep the teaching
limits broad while exploring; tighten them afterward to see valid FAILs.
The model is intentionally generic and is not suitable for foundry signoff.

Next: [Monte Carlo](../monte_carlo/README.md) for random component variation.
