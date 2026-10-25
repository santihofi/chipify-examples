# IHP SG13G2 source follower

This existing advanced example uses a differential source follower built from
IHP SG13G2 devices. Start with the [ideal divider](../voltage_divider/README.md)
if you want to learn Chipify before configuring a PDK.

## Additional requirements

- Xschem and ngspice on `PATH`.
- IHP-Open-PDK / `ihp-sg13g2`, including its Xschem symbols and ngspice
  compiled-device models/initialization.
- For the VACASK datasheet, VACASK and its IHP models/OSDI files.

The [IIC-OSIC-TOOLS environment](https://github.com/iic-jku/iic-osic-tools)
provides these EDA tools. Launch from a shell that has initialized the PDK
environment. Outside that environment, configure `PDK_ROOT`, `PDK`, the
Xschem library paths and simulator initialization for your local installation.
See the [IHP PDK repository](https://github.com/IHP-GmbH/IHP-Open-PDK) for
installation details.

The project's [xschemrc](xschemrc) sources the PDK configuration and adds
`sch/` to the symbol path. Run Chipify and Xschem from this directory so
project-local configuration and relative symbol paths resolve consistently.
The existing VACASK bench/settings contain `/foss/pdks/...` paths; adapt
them if your PDK lives elsewhere.

## Files and entry points

| File | Purpose |
| --- | --- |
| [sch/source_follower.sch](sch/source_follower.sch) | Circuit schematic; its symbol is beside it |
| [tb/tb_sf_op.sch](tb/tb_sf_op.sch) | Operating point, differential offset `vd`, common-mode `ve` |
| [tb/tb_sf_gain.sch](tb/tb_sf_gain.sch) | AC gain and bandwidth |
| [tb/tb_sf_tran.sch](tb/tb_sf_tran.sch) | Transient testbench for waveform experiments |
| [tb/tb_sf_op_vacask.sch](tb/tb_sf_op_vacask.sch) | VACASK operating point |
| [datasheets/corners_ngspice.yaml](datasheets/corners_ngspice.yaml) | 27 temperature/supply/process cases using ngspice |
| [datasheets/mismatch_ngspice.yaml](datasheets/mismatch_ngspice.yaml) | 1000 mismatch seeds; a larger experiment |
| [datasheets/corners_vacask.yaml](datasheets/corners_vacask.yaml) | VACASK OP plus ngspice AC in the same datasheet |

From this directory, start with:

```bash
chipify-cli -c corners_ngspice.yaml --json
chipify
```

Choose `corners_ngspice.yaml` in the GUI. The included `settings.json`
contains a saved Multi-Plot Dashboard configuration to explore after loading
results. For a short mismatch experiment, copy its datasheet to a new name
and reduce the seed range before running the full 1000 cases.

## Adapting the existing datasheets

The original datasheets predate the introductory tutorials' report blocks.
Add a `reports:` block using [the guide](../docs/datasheets.md) before expecting
`--reports` to produce configured documents and figures.

Check measurement names against each testbench: the ngspice OP bench exposes
`vd` and `ve`, while the VACASK OP bench exposes `outp` and `outn`.
An equation must use columns available in that run. For seeded experiments,
render positive integer seeds in the testbench, as shown in the standalone
[Monte Carlo example](../monte_carlo/tb/tolerance.spice).

The existing mismatch datasheet requests transient signals on `tb_sf_op`,
which runs only an operating-point analysis. To add transient capture, select
`tb_sf_tran` as a separate testbench with `transient_signals` and avoid asking
it for the OP bench's scalar measurements.

The new automated check covers the four PDK-free projects. This legacy IHP/
VACASK example needs a configured PDK environment for end-to-end validation.
