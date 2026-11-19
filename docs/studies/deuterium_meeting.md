# Electron–deuterium density, wavenumber, and electron response

## What we tested

We asked how quickly a disturbance in a magnetic dipole grows as the density gradient steepens, how that growth depends on its binormal wavelength, and what changes when electrons respond instantaneously to the local potential. All results use linear electrostatic GENE 3.1 patch 5 initial-value runs (`comp_type = 'IV'`). Both equilibrium temperature gradients remain 2. Singly charged deuterium and electrons have equal equilibrium densities, so quasineutrality and its equilibrium derivative require equal density gradients. Units, dipole geometry, masses, velocity extents `lv = 3.5` and `lw = 12.25`, and the automatic timestep policy were held fixed within the scan. [Normalization](../technical/normalization.md) · [Equilibrium constraint](../research_roadmap.md#3-isolate-density-gradient-effects-within-a-valid-equilibrium)

## Density gradient at fixed wavenumber

Steeper common density gradients yielded faster growth and a larger positive signed frequency across the converged range. The historical `32 × 48 × 32` series extends this trend from `omn = 0.5` to 5. The economical `24 × 48 × 24` points reproduce it at `omn = 1, 2, 3`. The archived case at zero density gradient reached its 5,000-step cap, so the low-gradient threshold is open. A fixed temperature gradient does not isolate an individual kinetic drive term. In particular, the relative weighting of the density and temperature parts of the diamagnetic response can change.

| Common `omn` | Archived growth | Archived signed frequency | Archived time (s) | Economical growth | Economical signed frequency | Economical time (s) |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | unresolved | unresolved | 493.688 | | | |
| 0.5 | 2.685 | +0.401 | 771.335 | | | |
| 1 | 3.286 | +0.590 | 254.372 | 3.294 | +0.591 | 127.690 |
| 2 | 4.172 | +0.946 | 232.111 | 4.179 | +0.947 | 111.678 |
| 3 | 4.860 | +1.295 | 1094.048 | 4.868 | +1.296 | 101.391 |
| 4 | 5.436 | +1.641 | 181.010 | | | |
| 5 | 5.934 | +1.986 | 149.837 | | | |

Every populated rate in this table is GENE-converged. No density-only reruns were required. [Growth](../../figures/deuterium_meeting/01_density_growth.png) · [Frequency](../../figures/deuterium_meeting/02_density_frequency.png)

## Wavenumber matrix

All nine cases converged without rescalings. At each common gradient, growth decreased as the sampled wavenumber increased from 0.5 to 1.0, while signed frequency increased. The largest **sampled** growth stayed at `kymin = 0.5` for all three gradients. Because 0.5 is a boundary of the tested interval, the location of the growth maximum is unresolved.

| Common `omn` | `kymin` | Growth | Signed frequency | GENE time (s) | Grid and origin |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 0.5 | 3.451 | +0.434 | 166.704 | 24 × 48 × 24, new |
| 1 | 0.7 | 3.294 | +0.591 | 127.690 | 24 × 48 × 24, reused |
| 1 | 1.0 | 2.974 | +0.795 | 144.245 | 24 × 48 × 24, new |
| 2 | 0.5 | 4.309 | +0.685 | 270.044 | 32 × 48 × 32, archived |
| 2 | 0.7 | 4.179 | +0.947 | 111.678 | 24 × 48 × 24, reused |
| 2 | 1.0 | 3.900 | +1.314 | 268.853 | 32 × 48 × 32, archived |
| 3 | 0.5 | 5.015 | +0.934 | 116.486 | 24 × 48 × 24, new |
| 3 | 0.7 | 4.868 | +1.296 | 101.391 | 24 × 48 × 24, reused |
| 3 | 1.0 | 4.570 | +1.819 | 111.089 | 24 × 48 × 24, new |

The archived `omn = 2`, `kymin = 0.5` and 1.0 inputs match the economical reference physics. Within each of these two comparisons the intended wavenumber and the two grid dimensions (`nz0`, `nw0`) are the only changes. They use automatic stepping, which is grid-dependent. The previous `kymin = 0.3` outlier remains unresolved and was omitted. The two finer-grid cells are marked in the figures. [Growth](../../figures/deuterium_meeting/03_wavenumber_growth.png) · [Frequency](../../figures/deuterium_meeting/04_wavenumber_frequency.png) · [Discrete map](../../figures/deuterium_meeting/07_discrete_stability_map.png)

## Mode structure

Across the nine matrix cases, final complex overlaps with the economical `omn = 2`, `kymin = 0.7` reference were at least **0.99926**. The earlier and later phase fits also stayed on the same signed trend. There is no resolved abrupt change in dominant mode shape or temporal phase behavior over these samples.

We read the complex potential at every parallel node, normalized each final profile to unit peak amplitude, and aligned global phase using the complex inner product with the reference, and set the reference phase to zero at the first node. For comparisons across grids, we linearly interpolate the *complex* profiles onto one uniform normalized coordinate for the overlap. We plot simulated node values, mask phase where the amplitude is below 5% of the peak, and compare both phase and the envelope. The periodic dipole trace follows one turn, with the same starting location and orientation for the two grids. The displayed phase is relative to the alignment, and frequency is the temporal slope of the unwrapped complex projection, in the GENE convention $\phi\propto e^{(\gamma+i\omega)t}$. High overlap and smoothly varying rates support continuity of the observed dominant mode, while mode competition and weakly excited branches remain possible. [Modes](../../figures/deuterium_meeting/05_mode_structure.png) · [Complex profiles](../../results/deuterium_meeting/profiles.csv) · [Overlaps](../../results/deuterium_meeting/spatial_overlaps.csv)

## What adiabatic electrons change

In the Boltzmann closure, parallel electron equilibration is fast relative to mode evolution and the perturbed electron temperature and independent kinetic response are neglected. Neglecting electron inertia and linearizing isothermal parallel force balance gives $T_e\nabla_\parallel(\delta n_e/n_e)=e\nabla_\parallel\phi_1$. The flux-surface average fixes the integration constant in the usual closure, $\delta n_e/n_e=e(\phi_1-\langle\phi_1\rangle_{\rm FS})/T_e$. The flux-surface-averaged term is zero for the nonzonal Fourier component here, so positive potential attracts electrons in phase. Fast transit is a motivation for passing electrons. In a dipole, rapid bounce motion of trapped electrons still leaves a bounce-averaged response and possible drift resonances, so small electron mass alone does not justify Boltzmann electrons. The full closure discards trapped-electron kinetics, electron magnetic and diamagnetic drift resonances, electron finite gyroradius, and electron phase mixing. It retains kinetic ions and their finite gyroradius. [GENE field equations](https://pure.mpg.de/rest/items/item_2139664_1/component/file_2139663/content) · [Dipole orbit and drift physics](https://arxiv.org/abs/1711.08021)

With $\varphi=e\phi_1/T_i$, the nonadiabatic ion response $h_i$ (called $g_i$ in the theoretical plan) obeys $\int J_0 h_i\,d^3v/n_i=(1+T_i/T_e)\varphi$ in the local, singly charged, equal-density quasineutral model. Equivalently, with gyrocenter distribution $g_i=h_i-J_0\varphi F_{0i}$, the coefficient is $1-\Gamma_0+T_i/T_e$, separating ion polarization from Boltzmann electron shielding. The closure replaces the complex kinetic electron density moment with a real algebraic term. Growth, propagation and localization can change, but there is no universal sign or growth prediction without the ion and electron dynamics of the particular branch. [Analytical eigenproblem](../technical/adiabatic_validation.md) · [Kinetic-ion formulation](https://doi.org/10.1063/1.4868412)

The installed release explicitly supports this path. `adiabatic_response.F90` recognizes one evolved positive ion species without a kinetic electron, requires `tau = 1`, and sets beta to zero. `adiabatic_response_base.F90` sets the implied electron density to the sum of ion charge densities and the electron temperature to the first ion temperature. `profiles.F90` bypasses the explicit electron-gradient balance check here, so we match the implied equilibrium ourselves by taking $n_e=n_D$ and $T_e=T_D$ locally. `fieldsolver_ff.F90` adds the unit normalized electron response to the nonzero-mode field operator. `adiabatic_response_base.F90` applies the surface-average correction only when the zero binormal mode exists. The scan and controls use the same periodic parallel boundary, $m_{\rm ref}$, normalization, and nominal `omt = 2` for the equilibrium. The closure has no independently evolving electron temperature gradient or electron kinetic distribution. The executable identified both closures in their startup banners. [Exact control inputs](../../configs/deuterium_meeting/) · [GENE source verification points](../references.md)

| Electron treatment | Evolved species | `coll` | Growth | Signed frequency | Steps | GENE wall time (s) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Kinetic | 2 | 0 | 4.176 | +0.944 | 2419 | 111.658 |
| Adiabatic | 1 | 0 | 0.136 | −0.029 | 849 | 19.765 |

Both controls converged with no amplitude rescaling. They used `omn = omt = 2`, `kymin = 0.7`, `24 × 48 × 24`, and the same ion parameters and geometry. `coll = 0` was applied to both models to separate electron closure from collision settings. Numerical parallel hyperdiffusion was retained. The kinetic control is close to the collisional reference (`4.179`, `+0.947`). With adiabatic electrons, growth fell by **96.7%** and rotation changed sign. A weak growing disturbance remained, and the two final spatial shapes have complex overlap **0.9905** after alignment. The kinetic envelope dips near the middle of the plotted turn, whereas the adiabatic envelope peaks there. The change demonstrates strong sensitivity to kinetic electrons at this point. It does not identify a unique kinetic mechanism or prove that the two closures selected the same branch. [Kinetic versus adiabatic](../../figures/deuterium_meeting/06_adiabatic_comparison.png)

GENE reached its estimator threshold at normalized time 48.052 in the adiabatic case, past its nominal ion recurrence estimate 42.187. The earlier projected fit over `[35, 40]` was approximately **0.13613**, **−0.02939**. Over the last five time units, the fit was **0.13595**, **−0.02942**. The sign and order of magnitude precede recurrence, so the main contrast does not rely on the final interval. The adiabatic automatic step is about 0.05653 versus 0.001087 in the kinetic case. The kinetic run also extends beyond its nominal electron recurrence time (0.696). Its late-time growth and phase slopes are steady and close to the collisional reference. Recurrence estimates are checks on interpretation, with a velocity-grid test needed for precise collisionless rates. The weak adiabatic rate and small negative frequency still warrant a targeted ion velocity-grid and timestep check before precision claims. The factors by which growth and frequency differ are much larger than the established grid differences on the collisional reference. [Fit windows](../../results/deuterium_meeting/fits.csv)

## Reproduction and limits

The [full run table](../../results/deuterium_meeting/runs.csv) records per case the exact tracked input and hash, source revision, grid, solver status, applied timestep, steps, and wall time. The [raw checksums](../../results/deuterium_meeting/raw_checksums.csv) identify local outputs. New GENE runs used one MPI rank and one OpenMP thread each, with at most two concurrent processes. They were launched from separate directories with `out/` using `MACHINE=mac_arm64 OMP_NUM_THREADS=1 /absolute/path/to/gene_mac_arm64 >run.log 2>run.stderr`. The six new runs totaled 669.947 s of GENE-reported wall time, summed over processes. The two-slot batch elapsed 360.167 s. The archived inventory contains 11 reused converged runs and one inspected unresolved run. Wall times vary with load. The source checkout and prior run directories were kept intact.

Regenerate the figures from the committed data using:

```sh
python3 scripts/analyze_deuterium_meeting.py
```

To rebuild the numerical tables locally, pass `--extract /absolute/path/to/gene-complete/runs /absolute/path/to/repository/work` after making the referenced run outputs available. The script does not execute GENE. [Analysis](../../scripts/analyze_deuterium_meeting.py)

The economical grid is an exploratory choice. Previous velocity-domain tests shifted signed frequency at the reference by approximately 4.9%, and those tests do not establish a transferable error bar. The nine samples establish trends within a limited wavenumber interval. No global maximum, independent species-gradient response, new temperature-gradient response, or analytical ion-mode eigenvalue has been established. The next useful numerical checks are an adiabatic velocity-resolution/timestep control for the weak branch if precision is needed and targeted validation below `kymin = 0.5` before interpreting a growth peak there. [Prior domain sensitivity](deuterium_moment_controls.md)
