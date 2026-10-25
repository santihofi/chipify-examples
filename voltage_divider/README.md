# Voltage divider: your first sweep

This ideal two-resistor circuit introduces the complete Chipify workflow
without schematic entry or device models.

```text
vin ── Rtop ──┬── vout
             Rbottom
              │
              0
```

## Run

From this directory:

```bash
chipify-cli -c divider.yaml --reports --json
```

Or run `chipify`, select `divider.yaml`, and start the simulation in the GUI.
All six cases should pass without simulation errors.

## Read the files

- [datasheets/divider.yaml](datasheets/divider.yaml) selects three input
  voltages and two bottom-resistor values. Chipify simulates every
  combination, giving six cases.
- [tb/divider.spice](tb/divider.spice) uses `{{ vin }}`, `{{ r_top }}`, and
  `{{ r_bottom }}`. It runs an operating-point analysis and defines the three
  measurement vectors named in the datasheet.
- [project.yaml](project.yaml) selects the default datasheet and two workers.

The analytical checks are:

```text
vout = vin × r_bottom / (r_top + r_bottom)
gain = r_bottom / (r_top + r_bottom)
current = vin / (r_top + r_bottom)
```

With 10 kohm resistors and a 1.8 V input, expect 0.9 V, gain 0.5 and 90 uA.
With a 20 kohm bottom resistor, gain becomes 2/3.
The report includes output versus supply, a corner-yield matrix, and a
correlation heatmap. These are deterministic sweep results, not a random
sample of manufactured devices.

## Try the features

1. Open Measurements to compare the observed ranges with the YAML limits.
2. In the GUI's equation results, inspect `divider_power_mw`, calculated
   from supply voltage and current. Current Chipify applies top-level scalar
   equations when the GUI loads data; this example's CLI reports use the
   measured vectors directly.
3. Copy `divider.yaml` to `stricter.yaml`, set `divider_vout.max` to `2.0`,
   and run `chipify-cli -c stricter.yaml --reports --json`. You should get
   valid simulations with some FAIL verdicts. Keeping a separate datasheet
   also keeps the original limits available for comparison.
4. Change the input values to `linspace(1.8, 5, 5)` for a denser sweep.

Next: [RC filter](../rc_filter/README.md) for waveform capture and a combined
report. See the [datasheet guide](../docs/datasheets.md) for the field meanings.
