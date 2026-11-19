# Historical deuterium replication benchmark

The [shared MAE 190 benchmark](classmate/README.md) uses the tested electron–positron IV input. This page preserves the separate electron–deuterium comparison.

## Start here

Use the [deuterium input](parameters) for an optional deuterium comparison. For the four-student exercise, share the [electron–positron text file](classmate/parameters.txt).

## Exact input and build

Use `benchmarks/parameters` unchanged. Its SHA-256 is `7cc11cad2928ea38e4669eddde06036aac10bab26305927f5ba67ff9150de881`. The original IV input remains in the [research archive](../configs/isotope/deuterium/omn_2_omt_2/parameters). Only its inactive eigenvalue-solver keys were omitted from the current copy. This is the historical conservative grid at `nz0 = 32`, `nv0 = 48`, `nw0 = 32`, with `lv = 3.5`, `lw = 12.25`, and automatic RK4 timestep selection. Both species have `omn = omt = 2`, unit normalized density and temperature, and opposite unit charges. The kinetic electron and deuterium masses are 0.00054462 and 2 in proton-mass units. The input fixes `kymin = 0.7`, a 0.4 m ring radius and 750 A current. [Reference scales and conventions](../docs/technical/normalization.md)

The reference used GENE **3.1 patch 5**, source revision `a0d2f213c5e22eed3b9f1bf4e40530c6292a9143`, double precision on Apple Silicon, GNU Fortran 16.2.0, Homebrew Open MPI, FFTW, and OpenBLAS, with GPU, SLEPc, and ScaLAPACK disabled. Use one MPI task and one OpenMP thread and record the compiler, libraries, architecture, and any differences from the reference build. The existing [installation record](../docs/research_log.md#1-installation-and-validation) describes the local build and changes. Obtain GENE separately.

## Run and analyze

Download the full GitHub source archive for the revision your class agrees to use, or clone and check out that revision. The whole checkout includes the script dependencies and the archived complex mode profile. Keep `benchmarks/parameters` byte-for-byte unchanged. GENE itself must be obtained and built separately.

From the checkout root, create a Python environment, install the analysis requirements, and run the launcher with the **absolute** path to your GENE executable. Use the machine setting for your build. For the archived Apple Silicon build, the commands are:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
MACHINE=mac_arm64 sh benchmarks/run_class_benchmark.sh /absolute/path/to/gene_mac_arm64
```

The launcher verifies the input hash before starting GENE, creates a fresh directory, sets one OpenMP thread, and writes the solver log, outputs, and `benchmark.json` there. It assumes that your GENE executable supports direct single-rank launch. If your installation requires an MPI launcher, run it with exactly one rank from a fresh directory containing the exact `parameters` and an `out/` directory, capture stdout to `run.log`, and use the analysis-only path:

```sh
sh benchmarks/run_class_benchmark.sh --analyze /absolute/path/to/completed-run
```

The script checks the exact input hash, solver status, rescaling, and recorded release and revision. It reads the little-endian double-precision GENE potential diagnostic and fits both projected log-amplitude and signed unwrapped phase on **normalized time [1.50, 2.00]**. The returned slopes are growth and frequency in GENE units. On machines with another field format, extract the same complex potential and times using the matching GENE diagnostic reader and apply the same fit. In the comparison CSV, put the primary fitted slopes in `gamma_norm` and `omega_norm` and identify the fit window in `precision_method`. Use the separate columns for solver rates and the fit-window extrema. Keep the JSON with the applied timestep, final time, RMS residuals, and energy-growth cross-check. The script also evaluates [1.40, 1.90] and [1.55, 2.05] when available. If the exact input does not reach the primary window, record that outcome and investigate it before changing the shared benchmark.

Require both GENE convergence and no runaway or rescalings. Compare the final complex-potential profile to the archived reference at the same grid nodes. An absolute normalized inner product near unity after accounting for global phase and scale supports the same mode. Use **0.999** as a preliminary overlap screen and compare signed frequency and energy growth. Record solver convergence, diagnostic agreement, and numerical grid and domain validation separately.

## Accuracy and reporting

The archived solver printed growth 4.172 and real frequency 0.946. Its primary window fits were **4.171905** and **0.946181**. The [reference JSON](local_reference.json) includes every tested window. Across those windows, the fitted frequency ranges from 0.945919 to 0.946289. Rounded to four significant digits, the primary, earlier, and later fits give 0.9462, 0.9459, and 0.9463 respectively. Growth rounds to 4.172 on all three windows, but the grid comparisons move growth beyond that digit. A second local archive with numerically identical input settings (decimal formatting of `kymin` differed) has byte-identical complex field output. This supports local repeatability for that build. Neither the two local files nor additional digits from a fit establish four-significant-digit numerical accuracy.

For class reproducibility, use the same primary window and compare the rounded four-significant-digit fits **and** the unrounded differences. A disagreement is a result to record. Compare alternative windows and field shapes before interpreting a fourth-digit mismatch. The 1% numerical screen is for exploratory convergence decisions. The combined-grid differences and unresolved velocity-domain sensitivity prevent a four-digit accuracy claim. [Combined-grid and domain study](../docs/studies/deuterium_combined_validation.md)

## Agreement and troubleshooting

- **Expected local result:** about **4.17** for growth and **+0.946** for signed frequency. Preserve the unrounded primary-window estimates in the results sheet so differences can be diagnosed. The additional digits describe the fit, and their reproducibility across machines must be measured.
- **Local diagnostic scale:** across the three windows the spreads are about 0.00019 in growth and 0.00037 in frequency. Use absolute differences of **0.0002** in fitted growth and **0.0004** in fitted frequency as provisional investigation flags for the class. These thresholds reflect the observed fit-window sensitivity, rather than a certified cross-platform tolerance or a bound on grid/domain error. Compare results on the same primary window and report any four-digit disagreement.
- **Checksum mismatch:** copy the exact input again from the agreed archive. Editing even just displayed decimal formatting changes the checksum.
- **Missing convergence, runaway, or early stop:** retain `run.log`, `run.stderr`, and `out/parameters.dat`. Check that the case used one rank, one thread, the expected build, and reached normalized time 2.00. Preserve the original attempt before retrying. Ask the class to agree on any input change.
- **Missing or unreadable potential output:** check the GENE release, `istep_field`, and output format. The extractor expects four-byte record markers and little-endian complex doubles. For a different valid format, read the complex field using that build's diagnostic reader and repeat the same normalization and fit.
- **Rates differ or the frequency sign flips:** verify the signed phase convention, the applied timestep from timestamps, mode overlap, and fixed fitting window before comparing significant digits. Similar amplitude envelopes alone can conceal different complex mode shapes.

The input, launcher syntax, and analysis-only path were checked locally against existing records. The two historical local runs reproduced the same field and printed rates, and the extractor reproduces the historical reference JSON. The current input was checked against its archived original after removal of inactive keys.
