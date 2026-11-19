# Research roadmap

The deuterium reference is the starting point. Preserve one exact copy for class replication, use separate inputs for numerical refinements, and postpone production scans until the grid and equilibrium checks below are complete. Record each decision in the [research log](research_log.md) and [session workflow](research_workflow.md).

## 1. Find a reliable, inexpensive grid

Begin with the [existing deuterium input](../benchmarks/parameters). Its historical result was $\gamma=4.172$, $\omega=0.946$, and a run wallclock of 232.111 s. Reuse the historical record as the initial comparison. If the local executable or platform changes, rerun the baseline once for a fair timing comparison.

**Reference-point status.** The reduced `24 × 48 × 24` grid passed the 1% rate and mode screen against the original and all saved one-axis refinements at the nominal velocity extents. The first `lw = 16.25` domain trial was stopped after runaway growth. At matched timestep the wider-domain frequency remained 4.93% above the nominal case and 4.90% above it after the wider grid was refined. A further matched-step domain expansion is the next domain check. [Matched controls](studies/deuterium_moment_controls.md) Use the exact historical `32 × 48 × 32` input for class replication. Hold production scans pending velocity-domain and representative off-reference checks. [Combined validation](studies/deuterium_combined_validation.md) · [Class benchmark](../benchmarks/README.md)

| Stage | Candidate settings | Decision |
| --- | --- | --- |
| Parallel resolution | The 24-point automatic case passed with `nv0 = 48`, `nw0 = 32`. | Use 24 at the reference point. Check a representative weaker-gradient or smaller-`kymin` case before extending this choice to a scan. |
| Parallel-velocity resolution | The 48 and 64 grids agreed. At 32 points, only the fixed-step run converged. | Keep 48 with automatic stepping. The 32-point fixed-step run is a cross-check. Long-time recurrence remains open. |
| Magnetic-moment resolution | 24, 32, and 48 agreed at fixed `lw`. | Use 24 at this reference point. Recheck if the velocity-extent study changes the working domain. |
| Velocity domain and timestep | At step 0.00057848 the nominal and wider domains differ in frequency even after refining the wider grid. Test one further moment-domain expansion at comparable sampling density. Check `lv` separately. | Isolate sensitivity to timestep, mesh spacing, and the velocity bounds. |
| Joint confirmation | The reduced grid passed comparisons against the original grid and one-axis refinements. Compare against a jointly finer grid and check a representative weaker-gradient or smaller-`kymin` point once the domain is settled. | Adopt the cheapest grid that passes for the intended scan range. Retain a separate fine-grid policy for difficult cases. |

Use the [grid comparison sheet](../benchmarks/grid_comparison.csv). Record GENE status, signed frequency, growth, wallclock, input hash, final time, timestep, and steps. Compute absolute differences and relative differences $|Q-Q_{\rm fine}|/|Q_{\rm fine}|$ for $Q=\gamma,\omega$. Use absolute error when the fine value is near zero and record sign changes. A proposed initial screen is 1% relative agreement for each nonzero rate, consistent mode envelopes, and no failure on timestep refinement. This threshold is for scan design and needs professor agreement. It does not imply four-digit numerical accuracy. Compare timing with the same build, ranks, threads, and diagnostic cadence. If performance is close, repeat selected timings under comparable load. Allow enough simulated time before deciding a run is unresolved. Inspect the anomalous historical case first with existing data, then verify its sensitivity only after selecting a stable reference grid.

## 2. Replicate the same case in class

Each student runs the [candidate parameter file](../benchmarks/parameters) unchanged and records details in the [four-student template](../benchmarks/comparison.csv). Compare the same plasma composition, exact input hash, GENE revision, and output convention. Analyze any mismatch before changing composition. Four-significant-digit agreement requires a common diagnostic with sufficient precision. A repeated exact case measures reproducibility, while grid refinement measures discretization error. [Benchmark instructions](../benchmarks/README.md)

## 3. Isolate density-gradient effects within a valid equilibrium

Fix electron/deuterium temperature gradients at 2, wavenumber at 0.7, and other settings at the validated baseline. Use the existing equal-gradient baseline where its numerical settings match the new requirements.

| Study | Planned inputs | Equilibrium gate |
| --- | --- | --- |
| A. Electron variation | Vary `omn_e`, keep `omn_D = 2`. Start with candidate levels 1, 2, 3. | Blocked in the present two-species quasineutral equilibrium except at the common point. |
| B. Deuterium variation | Vary `omn_D`, keep `omn_e = 2`. Start with candidate levels 1, 2, 3. | Same gate as A. |
| C. Joint variation | Set `omn_e = omn_D`. Start at 1, 2, 3 and then sample weaker or stronger gradients if reliable. | Compatible with the present equal-density, equal-and-opposite charge equilibrium. |

Charge neutrality requires $\sum_s q_s n_s=0$. Differentiating with respect to the same profile coordinate gives $\sum_s q_s n_s\texttt{omn}_s=0$, where $q_s$, $n_s$ and $\texttt{omn}_s$ are each species' charge, density and normalized density gradient. GENE's `check_quasineutrality` accumulates both sums for the active and dilution populations and defaults to checking gradient balance. For unit-density electrons and singly charged deuterium this forces equal normalized density gradients. Numerical acceptance alone would not justify an equilibrium. If the professor wants A or B, derive a charge-balanced multi-species alternative or establish an explicitly supported non-neutral model. Include the compensating species and its response in the study design because it changes the physical problem. An equilibrium with modified physics should get its own reference and interpretation. [Source verification points](references.md)

Generate a growth-rate figure and a real-frequency figure separately for each approved study. Record raw solver values, diagnosis, and uncertainty and omit unresolved values from validated curves.

## 4. Compare wavenumber dependence

After the gradient study selects stable cases, start with `kymin = 0.5, 0.7, 1.0` at a few gradient levels. Use 0.7 as the anchor from step 3. Add 1.5 and 2.0 if they help resolve the trend. Add smaller wavenumbers after the anomaly review and independent numerical spot checks. For an approved species-specific equilibrium, hold the other target species' density gradient and both temperature gradients fixed and document any required third-population adjustment. With the current two-species composition, use a joint-gradient family. Plot growth rate and signed real frequency versus normalized wavenumber in separate figures, one curve per gradient value. Update both figures after each batch and keep gaps for unresolved samples. Inspect envelopes near abrupt changes rather than joining across probable branch transitions.

## 5. Consider additional physical changes

| Parameter | Proposed initial comparison | Physical status |
| --- | --- | --- |
| Electron-to-ion temperature ratio | Change one temperature while documenting how the reference temperature and fixed code inputs map to physical quantities. | Compatible with two-species charge neutrality. Review collisions and pressure gradients when defining the comparison. |
| Collision strength | Start with the archival value `coll = 0.01`, a nearby smaller value, and the collisionless limit when appropriate. | Controlled model comparison. Verify operator and timestep regime at each setting. |
| Relative species density | Calculate charge and gradient balance before constructing inputs. | Unequal densities in the electron/singly charged deuterium model require a modified equilibrium or a compensating population. |
| Surface selection or numerical dissipation | Change one surface factor to test geometry sensitivity, or vary `hyp_z` in a numerical control. | Treat surface changes as a different physical operating point. Treat hyperdiffusion changes as discretization checks. |

Label any prototype outside a confirmed physical equilibrium as exploratory. Record why it was run and what it can test.

## 6. Identify mode structure from existing output

Start with the reference deuterium case, deuterium at 0.3, and the H/D pair at 0.7. The original files contain enough saved potential data for normalized envelopes. Plot $|\phi|/\max|\phi|$ across field-line position for several late times. Compare parity, phase, and spatial overlaps before attributing the low-`kymin` point to a physical branch. [Field output inventory and procedure](technical/mode_structure.md)

## 7. Validate a kinetic-ion case with adiabatic electrons

Agree on the electron closure, dipole boundary conditions, collisionless assumptions, and the analytical eigenproblem before choosing a test point. Derive or solve the independent dispersion condition, normalize and sign-match frequencies, then compare a mode on one refined grid and a small controlled gradient series. A published pair-plasma dispersion relation does not directly describe this kinetic-ion/adiabatic-electron case. The proposed configuration and open theoretical checks are in the [validation plan](technical/adiabatic_validation.md).
