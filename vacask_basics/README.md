# VACASK basics: native netlists and mixed engines

Five small datasheets cover native VACASK operating point, transient, AC and
DC simulation, then solve the same divider with VACASK and ngspice in each
case. Only VACASK's standard resistor/capacitor/diode modules are used; no
foundry PDK or Xschem is needed for this project.

The recommended environment is the installed IIC-OSIC-TOOLS container.
See the [VACASK and container guide](../docs/vacask.md) for setup and testing.

## Run

From this project directory **inside the container's login shell**:

```bash
python3 -m chipify.cli --batch datasheets --reports --json
python3 -m chipify.cli --batch datasheets --report-only --json
```

The batch has 24 parameter cases. Expect all 24 to complete without simulator
or capture errors. Each datasheet's output is under `out/<stem>/`; the
combined PDF is under `out/reports/<timestamp>/`.

| Datasheet | Cases | Circuit and lesson |
| --- | ---: | --- |
| [op.yaml](datasheets/op.yaml) | 6 | Divider OP; raw vectors reduced to scalar measurements |
| [step.yaml](datasheets/step.yaml) | 3 | RC step response, sampled rise time and waveform equation |
| [frequency.yaml](datasheets/frequency.yaml) | 3 | Complex AC capture and grouped Bode curves |
| [dc.yaml](datasheets/dc.yaml) | 6 | Diode DC sweep, temperature and a relative model include |
| [mixed.yaml](datasheets/mixed.yaml) | 6 | Per-testbench engines, distinct measurement names and comparison |

The AC datasheet captures curves without defining scalar AC acceptance
limits. Its PASS summary is not a measured bandwidth verdict. The verifier
compares every captured magnitude/phase sample with the analytical RC
transfer function.

## Native deck syntax

`source: netlist` with `engine: vacask` selects `tb/<testbench>.sim`.
The decks load installed OSDI modules, define models, instantiate the circuit,
and run one analysis inside a native `control` / `endc` block. This is a
VACASK deck, not ngspice text with a different extension.

The standard module names such as `resistor.osdi` use VACASK's installed
module path. The [diode model](models/diode.lib) is a local include resolved
relative to [clamp.sim](tb/clamp.sim).

**Keep the blank line after `endc` in these templates.** Chipify's current
Jinja rendering removes one final newline; the container's VACASK parser
requires the closing directive to remain newline-terminated. A deck that
runs directly can otherwise fail after template rendering.

## Scalars and waveform names

VACASK writes node voltages with plain names such as `vin` and `vout`.
Use those names in `transient_signals`, `dc_signals` or `ac_signals`.
The supplied decks request ASCII raw files, which Chipify's built-in reader
can consume; Chipify does not inject ngspice-style capture commands into them.

A datasheet `measure:` expression operates on the raw vectors. Use a
reduction such as `last(vout)` when a scalar is required. In the step example,
`time[argmin(abs(vout - 0.6321205588))]` selects the sample nearest 63.2% of
1 V. It includes the 1 us source delay and is limited by the saved timestep.

A branch name such as `vinput:flow(br)` becomes `vinput_flow_br_` in the
expression namespace; `-last(vinput_flow_br_)` is positive supply current.
This naming is separate from the ngspice deck's `let` vectors.

## Expected behavior

The OP divider has the same six analytical results as the
[ngspice divider](../voltage_divider/README.md). RC time constants are about
100 us, 316 us and 1 ms; their cutoff frequencies are about 1.59 kHz, 503 Hz
and 159 Hz. The diode voltage falls as temperature increases.

The mixed datasheet assigns engines explicitly to its two testbenches and
uses `vc_*` and `ng_*` measurement names. Its scatter plot should lie on the
identity line. The GUI-only `voltage_difference` equation helps inspect the
small numerical difference. A global `--simulator` override does not replace
an explicit per-testbench `engine:` selection.

To verify these circuits and reports in a temporary container copy, run
`python3 scripts/verify_vacask.py` from the repository root inside the
configured container, or use the host-side wrapper described in the guide.
