# Resistor Monte Carlo: variation, yield and distributions

This 1 V divider uses two nominal 10 kohm resistors. Each receives an
independent Gaussian perturbation with a standard deviation of 1%.
There is no PDK dependency; these are component tolerances rather than
foundry transistor-mismatch models.

## Run

From this directory:

```bash
chipify-cli -c tolerance.yaml --reports --json
```

Expect **64 total and 64 valid cases**, with both passing and failing runs.
The gain limits of 0.495 to 0.505 are intentionally tight. A FAIL means that
a valid measured value missed the spec; simulation errors should be zero.
The exact passing count can depend on the ngspice version's random generator.

For small tolerances, gain has mean about 0.5 and standard deviation about
0.00354. A 64-run sample will not match those values exactly; increase the
seed range to improve the statistical estimate. The 1% input is a standard
deviation, not a bounded ±1% tolerance or a three-sigma interval.

## How the randomness works

[tolerance.yaml](datasheets/tolerance.yaml) sweeps positive seeds with
`range(1, 65)`. In [tolerance.spice](tb/tolerance.spice), `setseed` receives
`{{ seed | int }}`, then two separate `sgauss(0)` draws alter the resistors
before the operating-point analysis.

The seed is explicitly set for every case, so changing worker count or
completion order does not change the sample assigned to that seed. Repeating
the run with the same ngspice version should reproduce the measured values
when joined by `seed`; CSV row order can differ between runs.

## Explore in the GUI

Run `chipify` here and start `tolerance.yaml`:

1. Measurements shows the ranges, failures, Cpk, and sigma estimates.
2. Histogram shows `mc_gain` or `mc_offset`; try Gaussian and KDE fits.
3. Analytics includes **QQ Plot (Normality)**, **ECDF + Spec Limits**, and
   **Yield vs Spec Curve**. Select one measurement at a time.
4. Check how a different limit changes yield, then copy the datasheet to
   another filename and rerun it to keep the original experiment intact.

Cpk and Gaussian fits are descriptive estimates here, not guarantees about
rare failures. The gain and offset constraints describe the same physical
deviation, so their failure-chart counts overlap; do not add them to estimate
the number of failed runs.

## Exports

The report configuration produces PNG/SVG figures, PDF and Markdown reports.
For `gain_distribution`, it also writes `gain_distribution_plot.csv` and
`gain_distribution_plot.tex` for pgfplots. Include the TeX file from its
report directory in a document that loads `pgfplots` and `pgfplotstable`;
keep the CSV beside it. Chipify writes the files without requiring a TeX
installation.

Try widening the gain limits, or double `sigma_fraction` to `0.02`. Change the
offset limits consistently if you want the two constraints to remain equivalent.

For foundry-device mismatch, continue with the
[IHP source follower](../source_follower/README.md).
