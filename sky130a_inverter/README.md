# SKY130A CMOS inverter

A two-transistor inverter using the installed `sky130A` ngspice models.
It demonstrates PVT transfer curves, measurement limits, transient capture,
load-dependent propagation delay and batch reports. No Xschem is required.
The nominal supply is 1.8 V; these are teaching limits, not foundry guarantees.

## Run inside IIC-OSIC-TOOLS

Use a writable examples checkout in the container's login shell, with
`PYTHONPATH` pointing at the documented Chipify revision. From this directory:

```bash
export SPICE_USERINIT_DIR="$(cd ../scripts/pdk-ngspice && pwd)"
python3 -m chipify.cli -c transfer.yaml --reports --json
python3 -m chipify.cli -c timing.yaml --reports --json
# Or generate both datasheets and a combined PDF:
python3 -m chipify.cli --batch datasheets --reports --json
```

The absolute initialization path must be set **before** launching Chipify.
Chipify runs ngspice in scratch storage, so a `.spiceinit` in your launch
directory alone is insufficient. See [the PDK guide](../docs/pdks.md) for
read-only mounts, copying a single project, model paths and verification.

## Datasheets

| Datasheet | Cases | Checks |
| --- | ---: | --- |
| [transfer.yaml](datasheets/transfer.yaml) | 27 | Three process corners, three supplies and three temperatures; high/low output levels, switching voltage and peak supply current |
| [timing.yaml](datasheets/timing.yaml) | 6 | Three corners and 10 fF / 50 fF loads at nominal supply and 27 C; both propagation delays and captured logic levels |

Expect 27/27 and 6/6 valid, passing cases, with no capture errors. Batch
outputs live under `out/transfer/` and `out/timing/`; the combined PDF is
under `out/reports/<timestamp>/`. The project limits execution to two workers
and allows 60 seconds per simulator invocation for loading the full PDK.

## Circuit and measurements

The transistor subcircuits are `sky130_fd_pr__nfet_01v8` and `sky130_fd_pr__pfet_01v8`.
Wn=1, Wp=2 and L=0.15 are in micrometres because the SKY130 library sets `scale=1u`.
The model library's typical corner is `tt`; slow and fast corners
are `ss` and `ff`. The complete sweep values are in the datasheets.
`pdk_root` defaults to `/foss/pdks`; edit that single-value parameter in both
datasheets if your installation is elsewhere.

The DC bench sweeps the input from ground to the supply. It records output
levels at both endpoints, normalizes them to the supply, and measures the
input voltage where the output crosses half the supply. The switching
fraction limits are intentionally broad. Higher input voltage should give
lower output voltage throughout the transfer curve.

The timing bench uses a 20 ns input period and 100 ps edges. It measures the
second pair of transitions, avoiding the initial operating point, and captures
both input and output. The 50 fF load should delay both output edges more
than the 10 fF load at the same corner.

The [PDK verifier](../scripts/verify_pdks.py) independently interpolates the
saved waveform crossings and compares them with ngspice's scalar delay and
switching-voltage measurements. It also checks DC monotonicity, logic rails,
load ordering, all waveform files and configured reports.

These benches use ngspice. The installed PDK has no native VACASK model
directory; this project does not claim to validate a VACASK conversion.
