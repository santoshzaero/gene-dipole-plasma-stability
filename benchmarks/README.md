# Four-student GENE benchmark

## Start here

Each student should run the same [deuterium input](parameters) and report how quickly the small plasma disturbance grows and oscillates. Use the [four-student table](comparison.csv). The goal is to compare how consistently different computers reproduce a common simulation. The class result is still pending.

## Exact input and build

Use `benchmarks/parameters` unchanged. Its SHA-256 is `d8e40c0f055746b882c0c7da8a8753dd3d536f3ef27e1dfbf02cdc6908616600`. This is the historical conservative grid at `nz0 = 32`, `nv0 = 48`, `nw0 = 32`, with `lv = 3.5`, `lw = 12.25`, and automatic RK4 timestep selection. Both species have `omn = omt = 2`, unit normalized density and temperature, and opposite unit charges. The kinetic electron and deuterium masses are 0.00054462 and 2 in proton-mass units. The input fixes `kymin = 0.7`, a 0.4 m ring radius and 750 A current. [Reference scales and conventions](../docs/technical/normalization.md)

The reference used GENE **3.1 patch 5**, source revision `a0d2f213c5e22eed3b9f1bf4e40530c6292a9143`, double precision on Apple Silicon, GNU Fortran 16.2.0, Homebrew Open MPI, FFTW, and OpenBLAS, with GPU, SLEPc, and ScaLAPACK disabled. Use one MPI task and one OpenMP thread and record the compiler, libraries, architecture, and any differences from the reference build. The existing [installation record](../docs/research_log.md#1-installation-and-validation) describes the local build and changes. Obtain GENE separately.

## Run and analyze

From the research repository root, set `GENE_BIN` to the absolute path of the verified GENE executable. Use the proper machine setting for your build. The archived machine setting was `mac_arm64`.

```sh
repo_dir="$PWD"
case_dir="$(mktemp -d)"
mkdir "$case_dir/out"
cp "$repo_dir/benchmarks/parameters" "$case_dir/parameters"
(
  cd "$case_dir" &&
  OMP_NUM_THREADS=1 "$GENE_BIN" >run.log 2>run.stderr
)
python scripts/measure_class_benchmark.py "$case_dir" > "$case_dir/benchmark.json"
```

The script checks the exact input hash, solver status, rescaling, and recorded release and revision. It reads the little-endian double-precision GENE potential diagnostic and fits both projected log-amplitude and signed unwrapped phase on **normalized time [1.50, 2.00]**. The returned slopes are growth and frequency in GENE units. On machines with another field format, extract the same complex potential and times using the matching GENE diagnostic reader and apply the same fit. In the comparison CSV, put the primary fitted slopes in `gamma_norm` and `omega_norm` and identify the fit window in `precision_method`. Use the separate columns for solver rates and the fit-window extrema. Keep the JSON with the applied timestep, final time, RMS residuals, and energy-growth cross-check. The script also evaluates [1.40, 1.90] and [1.55, 2.05] when available. If the exact input does not reach the primary window, record that outcome and investigate it before changing the shared benchmark.

Require both GENE convergence and no runaway or rescalings. Compare the final complex-potential profile to the archived reference at the same grid nodes. An absolute normalized inner product near unity after accounting for global phase and scale supports the same mode. Use **0.999** as a preliminary overlap screen and compare signed frequency and energy growth. Record solver convergence, diagnostic agreement, and numerical grid and domain validation separately.

## Accuracy and reporting

The archived solver printed growth 4.172 and real frequency 0.946. Its primary window fits were **4.171905** and **0.946181**. The [reference JSON](local_reference.json) includes every tested window. Across those windows, the fitted frequency ranges from 0.945919 to 0.946289, already changing the fourth significant digit. A second local archive with numerically identical input settings (decimal formatting of `kymin` differed) has byte-identical complex field output. This supports local repeatability for that build. Neither the two local files nor additional digits from a fit establish four-significant-digit numerical accuracy.

For class reproducibility, use the same primary window and compare the rounded four-significant-digit fits **and** the unrounded differences. A disagreement is a result to record. Compare alternative windows and field shapes before interpreting a fourth-digit mismatch. The 1% numerical screen is for exploratory convergence decisions. The combined-grid differences and unresolved velocity-domain sensitivity prevent a four-digit accuracy claim. [Combined-grid and domain study](../docs/studies/deuterium_combined_validation.md)
