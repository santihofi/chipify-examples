# VACASK and container verification

Use IIC-OSIC-TOOLS for example verification: it supplies VACASK, ngspice,
Xschem and the IHP, SKY130A and GF180MCU PDKs in one configured environment. The check scripts run
on temporary project copies and inspect measurements, capture files and
reports, rather than trusting the simulator or CLI exit code alone.

## Run the installed image from the host

Keep the Chipify and chipify-examples checkouts beside one another, or set
`CHIPIFY_SOURCE` to the tool checkout. From the examples repository:

```bash
bash scripts/verify_in_container.sh --source-follower
```

This uses the locally installed `hpretl/iic-osic-tools:latest` image without
pulling a replacement. It launches a disposable headless container, mounts
both repositories read-only, installs the missing pure-Python PDF dependency
into `/tmp`, and runs:

1. All four ngspice introductory projects, including the seeded rerun.
2. All five native/mixed VACASK datasheets and report-only regeneration.
3. Both 27-case IHP source-follower corner datasheets when
   `--source-follower` is supplied.
4. The 66 [SKY130A/GF180MCU inverter cases](pdks.md), always included.

Set `CHIPIFY_IIC_IMAGE` to an installed tag or digest to choose another image.
The script does not restart an existing GUI container. A missing local image
is an error; install your chosen IIC-OSIC-TOOLS image separately if needed.

## Use an existing running container

Assume the host repositories are available at `/foss/designs/chipify` and
`/foss/designs/chipify-examples`. Substitute your actual container name and
mount paths:

```bash
docker exec iic-osic-tools_xserver bash -lc '
  cd /tmp
  python3 -m pip install --target /tmp/chipify-test-deps pypdf
  export PYTHONPATH="/foss/designs/chipify:/tmp/chipify-test-deps:$PYTHONPATH"
  export MPLBACKEND=Agg QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1
  python3 -c "import chipify; print(chipify.version_info())"
  python3 /foss/designs/chipify-examples/scripts/verify_examples.py
  python3 /foss/designs/chipify-examples/scripts/verify_vacask.py --source-follower
  python3 /foss/designs/chipify-examples/scripts/verify_pdks.py
'
```

Use `bash -lc`: the login profile configures the PDK and simulator paths.
The printed Chipify path must be your checkout, because the image also ships
an installed copy that can have the same version number. Use the documented
[tested core revision](../README.md#install-and-run-the-first-example) when
reproducing the checks. These commands do not install packages into the
container's system Python.

## Run individual examples interactively

In a container login shell with the correct `PYTHONPATH`, change to a
**writable copy** of a project and run its README commands. For example:

```bash
cp -a /foss/designs/chipify-examples/vacask_basics /tmp/vacask-basics
cd /tmp/vacask-basics
python3 -m chipify.cli --batch datasheets --reports --json
```

The [VACASK basics](../vacask_basics/README.md) need only standard VACASK
modules. The [IHP source follower](../source_follower/README.md) additionally
uses the image's converted IHP models/OSDI files and Xschem symbols.
A per-project `settings.json` can set `vacask_binary`, `vacask_pdk_dir` and
`num_cores`. The wrapper uses the image's installed tools, not a downloaded
host-side VACASK binary.

## Capture and compatibility

- Keep one analysis per VACASK testbench in these tutorials. VACASK writes
  one raw file per analysis and the current Chipify engine selects one file
  from an invocation; multiple output files are not merged automatically.
- The new decks use `options rawfile="ascii"`. The built-in reader handles
  those files even if the optional PyOPUS reader API is unavailable. A warning
  about importing `RawFile` can therefore precede a successful fallback;
  check the actual numeric values and capture files.
- Use plain raw-node names (`vin`, `vout`), reduce waveform expressions to
  scalars, and retain the extra trailing blank line in the `.sim` templates.
- The AC tutorial validates complete complex waveforms. Avoid deriving an AC
  magnitude from the scalar expression path, which currently coerces raw
  vectors to real arrays; do AC postprocessing on the captured magnitude/
  phase data instead.
- `vacask --version` is not accepted by the tested build. Invoking `vacask`
  prints its build banner; record that build alongside ngspice/Xschem versions.

## What was verified

The environment used for these additions is IIC-OSIC-TOOLS image digest
`sha256:306585de35d198e70ea58950f77147c86f56c698726a19afea9f1c83009557be`:
VACASK `fb8cc20`, ngspice 47, Xschem 3.4.8RC and Python 3.12.3.
The original introductory suite's 82 cases and seeded rerun passed in this
container. Both original IHP corner datasheets completed all 27 cases without
simulator errors, including the VACASK OP/ngspice AC combination.

The new 24-case VACASK suite checks OP/DC/step measurements against circuit
formulas, every AC magnitude/phase sample against the analytical transfer,
all waveform files, mixed-engine agreement, and configured reports.
The 100-seed IHP statistical experiment and an on-screen/HiDPI GUI are
outside this automated corner check; the separate introductory Monte Carlo
example is tested with both worker counts. TeX source generation is checked,
not TeX compilation.

The CI workflow uses the same pinned IIC-OSIC-TOOLS image and container wrapper.
See the upstream [IIC-OSIC-TOOLS project](https://github.com/iic-jku/iic-osic-tools)
and [VACASK project](https://codeberg.org/arpadbuermen/VACASK) for tool details.
