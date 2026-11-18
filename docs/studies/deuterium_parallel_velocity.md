# Parallel-velocity resolution at the deuterium reference point

## In plain language

Using 64 instead of 48 points to sample motion along the magnetic field gave nearly the same disturbance and took more than twice as long. Keep 48 parallel-velocity points for this reference case. The next cost check is one run at 32 points.

## Measured results

| Parallel-velocity grid | GENE growth rate | GENE real frequency | GENE converged | Applied timestep | Steps | GENE wall time |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| `nv0 = 48` · archived | 4.179 | 0.946 | Yes | 0.00107908 | 1,959 | 134.056 s |
| `nv0 = 64` · new | 4.178 | 0.946 | Yes | 0.00078100 | 2,859 | 295.881 s |

The reported growth rates differ by 0.001 (**0.0239%** relative to 64 points). Both frequencies print as 0.946. The finer grid took **2.21×** as long, adding 161.825 s. Its automatically selected step was 27.6% smaller and it took 900 more steps. The archived and new cases ended at normalized times of 2.11500 and 2.23366. These are single-run timings.

![Late fitted phase slopes and final potential envelopes for 48 and 64 parallel-velocity points](../../figures/convergence/deuterium_nv48_nv64.png)

## Technical interpretation

On the common time interval 1.61500–2.11500, the field growth fits were 4.178372 and 4.178199 (**0.00415%** relative difference), and the signed phase slopes were 0.946369 and 0.946279 (**0.00952%**). The energy-growth estimates were 4.177849 and 4.177677. The final complex potential profiles overlap at **0.9999999991** on the same parallel spatial grid. The diagnostic rates and the common-time fits pass the 1% screen and support the same dominant mode. The terminal-window fit variation limits how many digits can be compared reliably.

Only `nv0` changed in the input, and the timestep selected by GENE changed as a consequence. This compares the two practical configurations with automatic timestep selection. It leaves a same-timestep velocity-grid comparison and long-time recurrence untested. Retain `nv0 = 48` as the working reference. A single `nv0 = 32` run at fixed `nz0 = 24`, `nw0 = 32`, and velocity extents is the next candidate for reducing cost. No additional cases were launched.

## Experimental controls

The trial reused the [24-point automatic-timestep reference](../../configs/convergence/deuterium_nz24_auto/parameters). The [64-velocity-point input](../../configs/convergence/deuterium_nz24_nv64_auto/parameters) changes only `nv0` from 48 to 64. Both runs use `nz0 = 24`, `nw0 = 32`, the parallel-velocity and magnetic-moment extent parameters `lv = 3.5` and `lw = 12.25`, and the same electron–deuterium composition, gradients, `kymin = 0.7`, geometry, and diagnostics. Increasing the number of velocity points at fixed extent improves sampling over the same velocity domain. Both cases retain `calc_dt = T`, so GENE can apply a different stable timestep when the velocity grid changes.

GENE 3.1 patch 5 was run in double precision with one MPI rank and one OpenMP thread. The analysis uses a common 0.50-unit interval ending at the earlier final field time. It fits the log amplitude and signed unwrapped phase of each complex potential projected onto its final mode shape, and checks growth against half the slope of log total perturbation energy. The overlap compares the final complex profiles, allowing for overall amplitude and phase. The preliminary screen requires both solver convergence flags, rates with matching signs and less than 1% relative difference, and complex overlap of at least 0.999.

## Reproduce the comparison

From the research repository root, copy the exact input into a fresh simulation directory. This command requires a separately installed GENE executable.

```sh
repo_dir="$PWD"
gene_bin="$HOME/Developer/gene-complete/bin/gene_mac_arm64"
case_dir="$(mktemp -d)"
mkdir "$case_dir/out"
cp "$repo_dir/configs/convergence/deuterium_nz24_nv64_auto/parameters" "$case_dir/parameters"
(
  cd "$case_dir" &&
  export MACHINE=mac_arm64 OMP_NUM_THREADS=1 &&
  /usr/bin/time -p "$gene_bin" > run.log 2> run.stderr
)
```

The [offline analysis](../../scripts/compare_parallel_velocity.py) accepts the completed 48- and 64-point run directories through `--runs` to regenerate the tables. The figure can also be regenerated directly from the published data.

```sh
python scripts/compare_parallel_velocity.py --figure generated/deuterium_nv48_nv64.png
```

- [Run results, timing, and input hashes](../../results/convergence/deuterium_nv48_nv64/runs.csv)
- [Pairwise rates and mode overlap](../../results/convergence/deuterium_nv48_nv64/comparison.csv)
- [Terminal-window fit checks](../../results/convergence/deuterium_nv48_nv64/late_fits.csv)
- [Raw diagnostic checksums](../../results/convergence/deuterium_nv48_nv64/source_sha256.csv)
