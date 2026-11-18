# Research report

## Start here

The [four-page isotope report](isotope_stability_report.pdf) explains how hydrogen and deuterium behaved in 98 computer runs. The color maps show how quickly small disturbances grew as the researchers changed the density and temperature gradients. The report also explains why some runs yielded only estimates.

## Source and reproduction

[Linear Stability of Electron–Hydrogen and Electron–Deuterium Plasmas in Dipole Geometry](isotope_stability_report.pdf) is the original MAE 190 report. Its [LaTeX source](isotope_stability_report.tex) was adapted only to locate the archived figures from the repository root. Build a local copy with

```sh
mkdir -p generated/report
latexmk -pdf -outdir=generated/report reports/isotope_stability_report.tex
```

The report credits **MAE 190 — Research Division**. Its paired growth-rate comparison covers the 41 gradient settings where both runs met GENE’s convergence criterion. The current [technical methods](../docs/technical/convergence.md) document the automated fit thresholds and explain the manual classification, and the [research log](../docs/research_log.md) adds the subsequent wavenumber scan.
