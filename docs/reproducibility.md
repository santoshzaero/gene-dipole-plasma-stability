# Reproduce the analysis and runs

## Offline analysis

From the repository root, install [the requirements](../requirements.txt) in an isolated Python environment and run

```sh
python scripts/reproduce.py --out generated/figures
```

Omit `--out` for audit-only mode. The archive was checked with Python 3.13.16, NumPy 2.5.4, and Matplotlib 3.11.2. The analysis verifies archive hashes and the run index, refits the 13 energy traces, checks the original classifications and baseline, and regenerates the four reviewed figures from archived numbers. It calls no GENE executable. The [data dictionary](../results/README.md) describes the columns and missing values.

The original plotting and launch scripts in [the source archive](../scripts/archive/) retain their paths and historical behavior. They are provenance. Some launchers execute runs or overwrite scratch outputs at import time. For historical plotting, follow [the offline staging directions](../scripts/README.md), which use only the plotting scripts and curated copies of the data.

## GENE build and regression notes

Obtain GENE separately through the [GENE Development Team](https://www.genecode.org/license.html) and follow its documentation for the recorded revision and platform. The archived build used GNU Fortran, MPI wrappers, FFTW, OpenBLAS, and the `mac_arm64` machine definition in double precision. CMake is needed by the recorded RegStorage dependency build. For an independently configured copy with the compatible machine definition and dependencies, the upstream target is invoked at the GENE root with `MACHINE=mac_arm64 make`. The local binary name is `bin/gene_mac_arm64`. The exact original build command history is unavailable, and these instructions have not been rerun against a fresh checkout. Consult [the install record](research_log.md#1-installation-and-validation) for local code differences and working configuration details.

The upstream regression entry point in a disposable GENE copy is `./testsuite` from inside `testsuite/`. Use `./testsuite -help` to check available options and select the standard subset, machine and process count. The local log reports two MPI processes for the executed subset. Single-case production runs used one rank and one thread.

## Reproduce one simulation

The commands below are for a future authorized reproduction. Start in the repository root. Set `GENE_EXECUTABLE` to the absolute path of your separately installed executable, then make the case in a fresh directory. Substitute any exact input from [configs](../configs/README.md) to repeat that case. Use your build's appropriate single-rank launcher if the binary requires MPI startup.

```sh
repo_root="$PWD"
case_dir="$(mktemp -d)"
mkdir "$case_dir/out"
cp "$repo_root/benchmarks/parameters" "$case_dir/parameters"
(
  cd "$case_dir" || exit 1
  OMP_NUM_THREADS=1 "$GENE_EXECUTABLE" > run.log 2>&1
)
run_status=$?
printf 'Case: %s\nExit status: %s\n' "$case_dir" "$run_status"
grep -E 'Linear growth rate is converged|Total wallclock time for GENE' "$case_dir/run.log"
cat "$case_dir/out/omega.dat"
```

For the historical ARM64 build, the original launcher additionally exported `MACHINE=mac_arm64`. Preserve the actual input and runtime metadata. A nonzero exit, a missing diagnostic, a zero placeholder, or a suspicious output requires review. Compare against [the run index](../results/run_index.csv) using the same input. To reproduce a whole study, repeat the single-case procedure in separate directories with each input under the corresponding configuration directory, then correlate each log and omega record by the case key. Use the [class benchmark](../benchmarks/README.md) before starting a production sweep.
