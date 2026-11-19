# Completed research

The entries follow the order of the work. Run counts refer to the individual studies. The seven-point density pilot and five extended pair cases have their own input records.

## 1. Installation and validation

The immediate question was whether the Apple Silicon build could reproduce upstream regression outputs before its dipole calculations were used for research. The executable inspected locally is Mach-O ARM64. Run metadata records GENE **3.1 patch 5**, source revision `a0d2f213c5e22eed3b9f1bf4e40530c6292a9143`, GNU Fortran 16.2.0, double precision, FFTW, and no SLEPc.

The early build log stopped at RegStorage because CMake was unavailable. The later build linked successfully with the working `bin/mac_arm64.mk` configuration (GNU, MPI wrappers, FFTW and OpenBLAS). The checkout has two tracked downstream changes. The GNU compiler flags omit the GNU linker option `--warn-once`, and the C memory diagnostics use macOS Mach/malloc interfaces with compatibility wrappers. The build log also notes that the effective machine file differs from the original template. These changes and machine configuration should be disclosed when sharing results, with upstream source and patches obtained through GENE's authorized channels.

The regression log records 11 standard tests (IDs 1, 2, 3, 4, 12, 13, 14, 16, 17, 20, 23), 126 matching diagnostic comparisons, and completion. The opening `gmake` lookup failure was followed by the suite's fallback to `make`. The summary covers the executed subset. Basic linear dipole runs then established that the configuration produced potential, growth, and energy diagnostics. A grid refinement and shared case are the next checks for this specific model. [Regression results](../results/installation/regression_summary.csv) · [Build and execution notes](reproducibility.md)

## 2. Electron–positron gradient scan

**Question.** How do changes in common density and temperature gradients affect linear growth in a charge-symmetric pair plasma? A density-only pilot at `omt = 2` examined the growth rate at seven density gradients. The full factorial scan uses the same seven levels for `omn` and `omt`, including zero drive on each axis and enough intermediate cases to resolve trends within the sampled grid.

**Method.** The initial-value launcher generated 49 inputs from one pair template and varied the two gradient values in both species blocks. Both species had mass, density, and temperature of 1 in code units and opposite charges. The scan fixed `kymin = 0.7`, the ring geometry, numerical grid, Landau operator, and timestep-selection settings. Each case used its own directory and a 1,000-step cap. The analysis read the log and final omega diagnostic into a CSV.

**Evidence and next test.** GENE flagged 44 cases converged, with growth rates from 0.184 to 7.922, and printed zero real frequency for those cases at recorded precision. The five `CHECK` rows have zero diagnostic placeholders. All five were extended to a maximum of 5,000 steps. Two then terminated at GENE's underflow limit and three reached the step cap without converging. The map shows stronger growth toward larger common gradients in the sampled converged region. Joint inputs leave the response to gradients on each species unresolved. A matched kinetic isotope comparison tests whether the result changes with composition, while low-gradient cases need time-history and mode checks. [Pair grid](../results/pair/gradient_scan.csv) · [GENE-converged map](../figures/regenerated/pair_gene_only.png) · [Original map](../figures/pair/stability_map_original.png) · [Extended energy histories](../figures/pair/extended_energy_original.png)

## 3. Hydrogen versus deuterium

**Question.** At fixed gradients, geometry and nominal normalized scales, does changing the positive-ion mass change linear growth? A matching grid at `kymin = 0.7` makes a direct comparison at each sampled location. The hydrogen and deuterium series used the same numerical and species settings except for ion mass (1 versus 2). Each series used a 5,000-step cap and common electron–ion gradients. An original Python launcher ran one worker per isotope and recorded the GENE exit status and the converged omega values.

**Evidence and next test.** The formal counts are 44 of 49 hydrogen and 41 of 49 deuterium. Every one of the 41 paired GENE-converged differences was positive, from 0.811 to 3.404 in code units. At `omn = omt = 2` the hydrogen rate/frequency were 6.096/0.959 and the deuterium rate/frequency were 4.172/0.946. At that point the deuterium rate is about 31.6% lower. The original maps preserve the archived data-quality labels and the regenerated paired map uses only the 41 solver-converged pairs. The ordering describes the modeled linear modes with a shared code normalization. The [limitations](limitations.md) explain the meaning of the comparison. Follow with energy checks for unresolved runs, a wavelength scan to test the range of the ordering, and grid refinement to test numerical reliability. [Hydrogen table](../results/isotope/hydrogen.csv) · [Deuterium table](../results/isotope/deuterium.csv) · [Original H map](../figures/isotope/primary_validated_hydrogen.png) · [Original D map](../figures/isotope/primary_validated_deuterium.png) · [Original difference map](../figures/isotope/primary_validated_difference.png)

## 4. Free-energy diagnostics

**Question.** Do the 13 unresolved isotope time histories show sufficiently persistent exponential growth or decay to estimate its rate? The diagnostic reused the original runs and selected late windows to reduce transient influence. The analysis fit the log of total quadratic perturbation energy over the last 50%, 30%, and 15% of retained samples, with half the latest slope used for the rate. The automatic screen checked linearity and cross-window agreement. The final curation included one documented override at the uniform deuterium point.

**Evidence and next test.** The final isotope archive comprises 85 GENE-converged, six qualified estimates, and seven uncertain estimates. Curvature and changing slopes in the figure show why several histories remain inconclusive. The six estimates add context, including evidence for energy decay over the observed interval at zero gradients, while real frequencies and formal mode convergence remain unresolved there. The next experiment should test late-time persistence and eigenfunction stability for selected low-gradient inputs. [Fit methods and override](technical/convergence.md) · [Original fit panels](../figures/energy/all_13_energy_fits.png) · [Uniform-gradient comparison](../figures/energy/uniform_gradient_comparison.png)

## 5. Perpendicular wavenumber scan

**Question.** Does the isotope ordering persist across the tested perpendicular scales? The scan fixed both gradients at 2 for electrons and ions, using the reference cases, and changed only `kymin` within each isotope. A Python launcher ran eight cases per isotope at 0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 1.5, and 2.0. It read the solver message and final omega output, keeping unresolved rows and recorded return codes.

**Evidence and next test.** Eleven of sixteen cases carry the solver convergence flag and five are unresolved. Ten support five paired comparisons from 0.5 through 2.0. In those five pairs the hydrogen growth rate is higher, growth falls with increasing sampled wavenumber, and the real frequency rises for each isotope. At deuterium `kymin = 0.3`, GENE reported **378.519 growth and 220.647 real frequency**, with the convergence flag. This is an anomalous, unvalidated point. It remains in the original table and is excluded from the plotted comparisons. Neither isotope has a validated comparison below 0.5. Before interpreting that region, inspect phase evolution and field envelopes from the saved output, then test timestep, resolution, and mode identity. [All 16 outcomes](../results/ky/original.csv) · [Growth plot](../figures/regenerated/ky_growth.png) · [Frequency plot](../figures/regenerated/ky_frequency.png)

## 6. Deuterium parallel-grid comparison

At fixed deuterium reference inputs ($\texttt{omn}=\texttt{omt}=2$ for each species, `kymin = 0.7`, `nv0 = 48`, `nw0 = 32`), reused the completed `nz0 = 32` archive and ran one new case with `nz0 = 64`. Both passed GENE temporal convergence. Growth changed from 4.172 to 4.163 (0.216% relative to 64), and both printed a real frequency of 0.946. Common-window phase fits differed by 0.021%, and the final complex field shapes had overlap 0.99999997. GENE wall time rose from 232.111 s to 600.245 s. The next proposed checks are a timestep control at 32 points and, if that agrees, one run at 24 points. [Full study and reproduction instructions](studies/deuterium_parallel_grid.md)

## 7. Timestep sensitivity and 24-point trial

The matched-timestep 32-point run preserved the archived 4.172 growth and 0.946 frequency. Comparing 24 and 32 points with that same smaller timestep gave 0.152% growth-rate difference from the field fits, nearly identical phase slopes, and complex overlap 0.99999996. The new runs took 311.778 s at 32 points and 265.285 s at 24 points. The 32-point automatic run remains the fastest measured baseline at 232.111 s. A single 24-point automatic run is the next timing check. [Follow-up study](studies/deuterium_timestep_nz24.md)

## 8. Automatic timestep on 24 parallel points

Changed only `nz0` in the archived 32-point automatic input. GENE converged at 24 points with growth 4.179 and real frequency 0.946 in 134.056 s, versus 232.111 s for the 32-point automatic case. The matched-time field growth differed by 0.152%, the phase slope by about 0.00048%, and profile overlap was 0.99999996. The 24-point automatic configuration is the working grid for this reference point. The next check changes `nv0` from 48 to 64 with the other grids held fixed. [Automatic timestep results](studies/deuterium_timestep_nz24.md#automatic-timestep-result-and-working-grid)

## 9. Parallel-velocity refinement from 48 to 64 points

At `nz0 = 24` and `nw0 = 32`, refined only `nv0` from 48 to 64 at fixed velocity extents. Both cases converged. The common-window field-growth and phase fits differed by 0.00415% and 0.00952%, and the complex field overlap was 0.9999999991. GENE wall time rose from 134.056 s to 295.881 s. Retain 48 parallel-velocity points for the reference case and test 32 before choosing the least expensive grid. [Velocity-grid study](studies/deuterium_parallel_velocity.md)

## 10. Coarsening to 32 parallel-velocity points

At `nz0 = 24` and `nw0 = 32`, changed only `nv0` from 48 to 32 in the automatic-timestep reference input. GENE accepted a larger step, the energy ran away, and the solver rescaled amplitudes 20 times. A controlled stop ended the run without convergence after 899 steps and 48.225 s. The 32-point automatic configuration is unsuitable at the tested operating point. Keep 48 points. A separate smaller-timestep test is needed to distinguish timestep sensitivity from a coarse-grid problem. [32-point results](studies/deuterium_parallel_velocity.md#32-point-automatic-run)

## 11. Fixed-timestep control at 32 parallel-velocity points

Kept the 32-point velocity grid, all other grids, extents, and the deuterium physics fixed. Imposed a normalized step of 0.00057848. The controlled case converged with zero rescalings and matched the 48-point reference's printed rates (4.179 and 0.946). The common-window fit differences were 0.00882% in growth and 0.00963% in frequency. Final complex-profile overlap was 0.9999999890. This supports sensitivity to the automatic timestep configuration at 32 points. The controlled run took 191.614 s versus 134.056 s for the 48-point automatic case, so keep 48 as the working reference. [Fixed-timestep results](studies/deuterium_parallel_velocity.md#32-point-fixed-timestep-control)

## 12. Magnetic-moment refinement from 32 to 48 points

Reused the validated `nz0 = 24`, `nv0 = 48`, `nw0 = 32` case and ran one case changing only `nw0` to 48. Both converged without amplitude rescaling. The common-window fitted growth and frequency changed by 0.0147% and 0.0564%, and the final complex profiles had overlap 0.9999999989. GENE wall time rose from 134.056 s to 333.194 s as the automatic timestep decreased from 0.00107908 to 0.000906. Keep 32 as the working grid at this operating point and test one 24-point case if pursuing further cost reduction. [Magnetic-moment study](studies/deuterium_magnetic_moment.md)

## 13. Magnetic-moment cost check at 24 points

Changed only `nw0` from 32 to 24 using the 24/48 spatial and parallel-velocity reference grids with automatic stepping. GENE converged without rescaling in 111.678 s, saving 16.7% versus 32 points. The common-window fitted growth and frequency differed by 0.0174% and 0.0648% relative to 32. Final complex-profile overlap was 0.9999999991. The 24-point case also passed the comparison to 48 points. Adopt 24 magnetic-moment points at this reference point before testing the velocity extents and combined-grid sensitivity. [24-point cost check](studies/deuterium_magnetic_moment.md#24-point-cost-check)

## 14. Combined-grid validation and first velocity-domain check

The reduced `24 × 48 × 24` case passed the 1% screen against all five saved comparison grids. Relative to the original, fitted growth and frequency differed by 0.1698% and 0.0647%, and wall time was 51.9% lower. The new trial changed only `lw` to 16.25 and was stopped for runaway after 499 steps and one amplitude rescaling. It supplies no usable rate. The next test fixes the timestep at the wider domain. The exact archived input and new common-window analysis provide a four-student replication benchmark with numerical accuracy still unresolved. [Combined validation and domain study](studies/deuterium_combined_validation.md)

## 15. Wider magnetic-moment domain with fixed timestep

Kept the wider `lw = 16.25` grid and physics fixed and imposed timestep 0.00057848. The run converged without rescaling in 211.236 s. Relative to the nominal-domain automatic baseline, common-window fitted growth and signed frequency differed by 0.860% and 4.93%, with complex potential overlap 0.999997886. The same wider mesh remained stable under the fixed-step configuration, but its frequency fails the preliminary comparison to the nominal domain. Match the timestep at `lw = 12.25` before interpreting the source of the frequency shift. [Controlled timestep results](studies/deuterium_combined_validation.md#wider-domain-with-a-controlled-timestep)
