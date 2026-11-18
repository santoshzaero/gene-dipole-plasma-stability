# Parallel-velocity resolution at the deuterium reference point

## In plain language

Using 64 instead of 48 points to sample motion along the magnetic field gave nearly the same disturbance and took more than twice as long. The 32-point trial grew out of control with automatic timestep selection, but converged when we imposed a smaller step. That configuration still took longer than the 48-point reference, so keep 48 points for routine runs at this reference setting.

## Measured results

| Parallel-velocity grid | GENE growth rate | GENE real frequency | GENE converged | Applied timestep | Steps | GENE wall time |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| `nv0 = 48` · archived | 4.179 | 0.946 | Yes | 0.00107908 | 1,959 | 134.056 s |
| `nv0 = 64` | 4.178 | 0.946 | Yes | 0.00078100 | 2,859 | 295.881 s |
| `nv0 = 32` · automatic | — | — | No · stopped | 0.00128879 | 899 | 48.225 s to stop |
| `nv0 = 32` · fixed step, new | 4.179 | 0.946 | Yes | 0.00057848 | 3,619 | 191.614 s |

The reported growth rates differ by 0.001 (**0.0239%** relative to 64 points). Both frequencies print as 0.946. The finer grid took **2.21×** as long, adding 161.825 s. Its automatically selected step was 27.6% smaller and it took 900 more steps. The archived and new cases ended at normalized times of 2.11500 and 2.23366. These are single-run timings.

![Late fitted phase slopes and final potential envelopes for the converged velocity-grid cases](../../figures/convergence/deuterium_nv48_nv64.png)

## Technical interpretation

On the common time interval 1.61500–2.11500, the field growth fits were 4.178372 and 4.178199 (**0.00415%** relative difference), and the signed phase slopes were 0.946369 and 0.946279 (**0.00952%**). The energy-growth estimates were 4.177849 and 4.177677. The final complex potential profiles overlap at **0.9999999991** on the same parallel spatial grid. The diagnostic rates and the common-time fits pass the 1% screen and support the same dominant mode. The terminal-window fit variation limits how many digits can be compared reliably.

Only `nv0` changed in the input, and the timestep selected by GENE changed as a consequence. This compares the two practical configurations with automatic timestep selection. It leaves a same-timestep velocity-grid comparison and long-time recurrence untested. Retain `nv0 = 48` as the working reference. The 32-point trial below tests whether sampling velocity more coarsely could reduce cost.

## 32-point automatic run

The [32-point input](../../configs/convergence/deuterium_nz24_nv32_auto/parameters) differs from the 48-point input only in `nv0`. GENE chose a normalized timestep of 0.0012887872, about 19.4% larger than the 48-point step. The recorded energy exhibited runaway growth and the solver logged 20 amplitude rescalings. Near normalized time 0.25 the 32-point diagnostic recorded about $1.1\times10^{33}$ in total perturbation energy, compared with about 0.096 in the two converged cases. Discontinuities in the plot reflect rescaling, so amplitudes across a rescaling event cannot be compared as physical growth.

A run-local `GENE.stop` requested a controlled exit once this behavior was observed. GENE stopped without its linear-growth convergence flag after 899 reported steps, at normalized time 1.15991. The all-zero growth and frequency entries in the raw omega output are placeholders. The study retains the energy history and stop metadata without fitting a physical growth rate or comparing a final mode for the stopped case. The 48.225 s time records an incomplete trial.

![Runaway and rescaling with 32 points and automatic stepping, alongside the converged energy histories including the fixed-step control](../../figures/convergence/deuterium_nv32_auto_energy.png)

## 32-point fixed-timestep control

The [controlled input](../../configs/convergence/deuterium_nz24_nv32_fixed_dt/parameters) retains the automatic 32-point spatial and velocity grids, the physics, and the velocity extents. It changes only timestep selection via `calc_dt = F`, `dt_vlasov = 0.00057848`, and `ev_coll = 9300.0`. The last setting supplies the collision stability estimate required by this GENE build for manual step selection. It leaves the Landau collision operator and physical collision input unchanged. Field timestamps provide a check of the applied step.

During the run a monitor polled the energy diagnostic and run log every two seconds. It was configured to request a run-local `GENE.stop` if the recorded energy became nonfinite, exceeded $10^{12}$ in magnitude, or the solver logged an amplitude rescaling. This threshold is comfortably above the converged reference energy over the matching time range.

The run completed without triggering the monitor or logging any amplitude rescalings. GENE reported convergence at 3,619 steps and normalized time 2.09410. It printed growth rate **4.179** and real frequency **0.946**, matching the 48-point reference at output precision. The 32-point run with automatic stepping stopped at normalized time 1.15991, so its wall time is excluded from the comparison of completed cases.

| Common-window metric | 32 points, fixed step | 48 points, automatic step | Relative difference vs 48 |
| --- | ---: | ---: | ---: |
| Fitted growth from potential | 4.178724 | 4.178355 | 0.00882% |
| Fitted signed frequency | 0.946432 | 0.946340 | 0.00963% |
| Growth estimated from total energy | 4.178194 | 4.177809 | 0.00920% |

The common interval was normalized time 1.59410–2.09410. The final complex field profiles had overlap **0.9999999890**. The field and energy estimates support the same dominant mode. The fixed-step run took **191.614 s**, or **42.9% longer** than the 48-point automatic run (134.056 s). It needed 3,619 steps versus 1,959 to reach similar normalized times.

**Decision:** Keep `nz0 = 24`, `nv0 = 48`, and `nw0 = 32` with automatic timestep selection for this reference case. The controlled run shows that 32 velocity points can reproduce the reference mode at the tested smaller step. The contrast at fixed grid implicates the automatic timestep configuration in the runaway. It leaves the exact stability limit and the contribution of individual integrator settings unresolved. Keep the 32-point fixed-step case as a cross-check. If the goal is to reduce routine cost, continue with the magnetic-moment grid at the working baseline. Investigating a faster stable timestep for 32 velocity points would be a separate test. No additional simulations were started.

## Experimental controls

The trial reused the [24-point automatic-timestep reference](../../configs/convergence/deuterium_nz24_auto/parameters). The [64-velocity-point input](../../configs/convergence/deuterium_nz24_nv64_auto/parameters) changes only `nv0` from 48 to 64. All runs use `nz0 = 24`, `nw0 = 32`, the parallel-velocity and magnetic-moment extent parameters `lv = 3.5` and `lw = 12.25`, and the same electron–deuterium composition, gradients, `kymin = 0.7`, geometry, and diagnostics. Increasing the number of velocity points at fixed extent improves sampling over the same velocity domain. The original three cases retain `calc_dt = T`, so GENE estimates the timestep independently for each grid. The 32-point control fixes the timestep as described above.

GENE 3.1 patch 5 was run in double precision with one MPI rank and one OpenMP thread. The analysis uses a common 0.50-unit interval ending at the earlier final field time. It fits the log amplitude and signed unwrapped phase of each complex potential projected onto its final mode shape, and checks growth against half the slope of log total perturbation energy. The overlap compares the final complex profiles, allowing for overall amplitude and phase. The preliminary screen requires both solver convergence flags, rates with matching signs and less than 1% relative difference, and complex overlap of at least 0.999.

## Reproduce the comparison

From the research repository root, copy the exact input into a fresh simulation directory. This command requires a separately installed GENE executable.

```sh
repo_dir="$PWD"
gene_bin="$HOME/Developer/gene-complete/bin/gene_mac_arm64"
case_dir="$(mktemp -d)"
mkdir "$case_dir/out"
cp "$repo_dir/configs/convergence/deuterium_nz24_nv32_fixed_dt/parameters" "$case_dir/parameters"
(
  cd "$case_dir" &&
  export MACHINE=mac_arm64 OMP_NUM_THREADS=1 &&
  /usr/bin/time -p "$gene_bin" > run.log 2> run.stderr
)
```

Monitor the energy diagnostic when reproducing the 32-point trial. The original run used `touch GENE.stop` in its fresh run directory to request a controlled exit. The [offline analysis](../../scripts/compare_parallel_velocity.py) accepts the 48-point automatic, 64-point automatic, 32-point automatic, and 32-point fixed run directories in that order through `--runs`. Both figures can also be regenerated directly from the published data.

```sh
python scripts/compare_parallel_velocity.py \
  --figure generated/deuterium_nv48_nv64.png \
  --energy-figure generated/deuterium_nv32_auto_energy.png
```

- [Run results, timing, and input hashes](../../results/convergence/deuterium_nv48_nv64/runs.csv)
- [Pairwise rates and mode overlap](../../results/convergence/deuterium_nv48_nv64/comparison.csv)
- [Terminal-window fit checks](../../results/convergence/deuterium_nv48_nv64/late_fits.csv)
- [Raw diagnostic checksums](../../results/convergence/deuterium_nv48_nv64/source_sha256.csv)
