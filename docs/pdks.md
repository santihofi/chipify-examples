# SKY130A and GF180MCU tests

Use the installed IIC-OSIC-TOOLS image for both foundry examples. They import
ngspice decks and need no Xschem installation. The tested image has
`sky130A` and `gf180mcuD` beneath `/foss/pdks`; GF180's installed variant is
**D**, and its typical corner is named **typical**, unlike SKY130's **tt**.

| Project | DC cases | Timing cases | Devices |
| --- | ---: | ---: | --- |
| [SKY130A inverter](../sky130a_inverter/README.md) | 27 | 6 | 1.8 V NMOS/PMOS |
| [GF180MCU inverter](../gf180_inverter/README.md) | 27 | 6 | 3.3 V NMOS/PMOS |

Both sweep `ss` and `ff` as well as the typical process. DC covers three
supplies and -40 / 27 / 125 C. Transient timing compares 10 fF and 50 fF
loads at nominal supply and 27 C. These ranges and limits illustrate
characterization; they do not replace device reliability rules or foundry
qualification data. The PDK models stay in the installed image and are not
copied into this repository.

## Verify from the host

With Docker running and a Chipify checkout beside this repository:

```bash
bash scripts/verify_in_container.sh --source-follower
```

The wrapper also runs the existing introductory and VACASK suites. The PDK
verifier is always included, adding 66 parameter cases. The optional
`--source-follower` flag selects the separate IHP corner checks.
See [container setup](vacask.md) for image selection and `CHIPIFY_SOURCE`.

To run just the two new projects from a container login shell:

```bash
export PYTHONPATH="/foss/designs/chipify:/tmp/chipify-test-deps:$PYTHONPATH"
export MPLBACKEND=Agg QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1
python3 -m pip install --target /tmp/chipify-test-deps pypdf
python3 /foss/designs/chipify-examples/scripts/verify_pdks.py
```

Substitute your mounted paths. The checker uses temporary project copies,
forces the shared initialization below, and takes its model root from
`PDK_ROOT` or `/foss/pdks`. Pass `--pdk-root /your/pdks` to override that root.
`--validate-only` checks definitions, template rendering and documentation
links without requiring installed models or launching ngspice.

## Model setup and geometry

Both projects load libraries through their datasheets' `pdk_root` parameter:

| PDK | Model files under `pdk_root` |
| --- | --- |
| SKY130A | `sky130A/libs.tech/ngspice/sky130.lib.spice` |
| GF180MCU | `gf180mcuD/libs.tech/ngspice/design.ngspice`, then `sm141064.ngspice` in the same directory |

GF180 needs `design.ngspice` for its global/statistical parameters. The
installed version disables global variation and mismatch by default; these
are deterministic corner sweeps, not Monte Carlo mismatch experiments.

**Geometry units differ.** SKY130's library sets `scale=1u`, so its instance
uses `w=1 l=0.15`. GF180 uses `w=1u l=0.28u`. Copying the unsuffixed SKY130
values into GF180 would change the physical device dimensions.

The container's default `PDK` can remain IHP. These decks select their models
explicitly, and the PDK verifier uses the shared
[ngspice initialization](../scripts/pdk-ngspice/.spiceinit) through an absolute
`SPICE_USERINIT_DIR`. It requests HSPICE compatibility before model parsing,
skips model checks as in the installed SKY130 initialization, and limits
ngspice to one solver thread per Chipify worker. The project settings allow
60 seconds per invocation for PDK loading; two workers avoid excessive
parallel model parsing.

For an individual project on a read-only mount, set the initialization path
before copying the project and keep it pointed at the original repository:

```bash
export SPICE_USERINIT_DIR=/foss/designs/chipify-examples/scripts/pdk-ngspice
cp -a /foss/designs/chipify-examples/sky130a_inverter /tmp/sky130a-inverter
cd /tmp/sky130a-inverter
python3 -m chipify.cli --batch datasheets --reports --json
```

Use `gf180_inverter` in the same pattern. If you edit the model root manually,
update `pdk_root` in both datasheets. Changing the shell variable alone does
not alter the parameter in an ordinary interactive CLI run.

## Numerical checks and simulator coverage

The automated checks require every case to complete, every scalar limit to
pass, and every requested waveform to be present and finite. They inspect
DC inversion and monotonicity, compare the switching voltage to interpolation
of the saved transfer curve, interpolate both transient edge delays, and
check that the larger load increases both delays. PNG/SVG/PDF/Markdown and
the combined batch PDF are checked as well.

The installed SKY130A and GF180MCU directories provide ngspice models but no
`libs.tech/vacask` model sets. These tests therefore use **ngspice**. Native
VACASK examples and the IHP VACASK test remain covered by the
[VACASK suite](../vacask_basics/README.md); converting foundry libraries is
outside these tests.

The tested image and tool versions are in [the container guide](vacask.md#what-was-verified).
Installed metadata records open_pdks `1689ac3f2dc763876eaf967227c7dfe831b031ae`,
SKY130 primitives `403964dc7f9cca5ec1a8cc7b4f2a6f532b781676`, and GF180
primitives `4d0b4cef59c7686fac5fd3f4c6fb41d251d1f90c`.
No layout, extraction, DRC/LVS, statistical foundry mismatch or GUI interaction
is included in this check.
