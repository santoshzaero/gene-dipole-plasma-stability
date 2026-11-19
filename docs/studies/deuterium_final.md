# Electron–deuterium density gradients and wavenumber

## Final figures

The figures use normalized linear growth rate and signed real frequency for an electrostatic electron–deuterium plasma in a ring dipole. All kinetic scan points use GENE’s initial-value solver and $\mathrm{omt}_e=\mathrm{omt}_D=2$. Each marker is one qualified simulation. Straight segments guide the eye between adjacent samples. [Combined vector PDF](../../figures/deuterium_final/final_figures.pdf)

| Figure | PNG | Vector PDF | What it shows |
| --- | --- | --- | --- |
| 1 | [Wavenumber](../../figures/deuterium_final/figure_1_wavenumber.png) | [Wavenumber](../../figures/deuterium_final/figure_1_wavenumber.pdf) | Growth and signed frequency versus $k_y\rho_{\rm ref}$ at three common density gradients. |
| 2 | [Common density gradient](../../figures/deuterium_final/figure_2_density.png) | [Common density gradient](../../figures/deuterium_final/figure_2_density.pdf) | Growth and signed frequency versus the common gradient at four fixed wavenumbers. |
| 5 | [Electron response](../../figures/deuterium_final/figure_5_electron_response.png) | [Electron response](../../figures/deuterium_final/figure_5_electron_response.pdf) | Paired kinetic and adiabatic rates and the change in spatial amplitude at one collisionless point. |

Figures 3 and 4 would require the independent-gradient equilibria described below. They were omitted.

## Common-gradient results

At each common density gradient 1, 2, and 3, growth decreased and positive signed frequency increased across the four matched wavenumbers from `kymin = 0.5` to 1.5. The `omn = 2` curve continues that trend through the qualified 2.0 point (2.799, +2.275). The highest sampled growth remains at 0.5 for each gradient. A global maximum remains unresolved. At the four shared wavenumbers, increasing the common density gradient from 1 to 3 increases both rates. At `kymin = 0.7`, the wider density range covers 0.5 to 5. `omn = 0` was unresolved in the prior study and remains outside the plotted series.

The two new simulations complete the shared interval through `kymin = 1.5`. Both were GENE-converged without amplitude rescaling and their late-time log-amplitude and phase fits agree with the native rates. The four qualified high-wavenumber profiles have normalized complex overlaps of 0.9946 to 0.9984 with the `omn = 2`, `kymin = 0.7` reference. The near-unity overlaps and smooth rate trends support continuity of the sampled dominant mode family, with some change in shape. They do not uniquely identify the branch or drive mechanism.

| Common `omn` | `kymin` | Growth | Signed frequency | GENE wall time (s) |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 1.5 | 2.273 | +1.044 | 282.593 |
| 3 | 1.5 | 3.933 | +2.625 | 143.490 |

The pair totaled 426.083 s in summed GENE wall time and ran concurrently in 282.945 s elapsed. The `omn = 2` high-wavenumber samples came from qualified existing runs.

The low-wavenumber archive was checked directly against GENE’s logs and complex potential. At `kymin = 0.1` and 0.2, GENE reached the step cap without convergence after 727 and 356 amplitude rescalings respectively. At 0.3, the solver flagged convergence and printed growth 378.519 and signed frequency +220.647 after 29 rescalings. The final complex field has overlap **0.00156** with the `kymin = 0.5` profile on the same grid. This is far outside the profile variation across the qualified family. The combination of rescaling and departure from the regular mode makes the 0.3 value unsuitable for a physical trend or branch identification. It remains unresolved. The exclusion is recorded with the native output in the supplementary run table. [Run table and exclusions](../../results/deuterium_final/runs.csv) · [Spatial overlap comparison](../../results/deuterium_final/spatial_overlaps.csv)

## Why neither species-only scan is valid here

The equilibrium requires $n_e(x)=n_D(x)$ because electrons and singly charged deuterons are the only populations. Equality holds on neighboring surfaces of the local reference equilibrium. Differentiating it and using $g_s=\mathrm{omn}_s=-L_{\rm ref}\partial_x\ln n_s$ gives both $\sum_s Z_s n_s=0$ and $\sum_s Z_s n_s g_s=0$. With $Z_D=+1$, $Z_e=-1$ and equal nonzero densities this reduces to $g_D=g_e$. Setting two equal densities at the center with different derivatives makes the equilibrium non-neutral off that surface.

In the local kinetic solver, GENE 3.1 patch 5 calls `check_quasineutrality` from `init_physical.F90`. `profiles.F90` accumulates the density and charge-weighted gradient sums over nonpassive kinetic and dilution species. `check_qn_gradients` defaults to true and the local gradient violation triggers a stop. Disabling the guard would leave the proposed equilibrium inconsistent. A finite perturbation Debye term alone would also leave the background profiles unspecified. Both proposed species-only scans contain just the shared `g_e=g_D=2` point within the present model. The common-gradient curves measure variation along the equilibrium constraint and cannot identify either species’ independent gradient sensitivity. [GENE verification points](../references.md) · [Normalization](../technical/normalization.md)

The minimal model extension is one specified compensating charged population. For example, with an added positive species $C$, choose its charge fraction $f=Z_C n_C/n_e$ at the reference surface, with $0<f<1$. Then $n_D/n_e=1-f$ and an equilibrium requires

$$
g_e=(1-f)g_D+fg_C, \qquad g_C=\frac{g_e-(1-f)g_D}{f}.
$$

The fraction, charge, temperature, and kinetic or prescribed response of that population need physical justification. For small $f$, a large difference in the target gradients implies a large compensating gradient. This alternative changes composition and can change drive, polarization, dilution, collisions, or geometry. It would be a new equilibrium study with its own reference. No such input was generated or run. The adiabatic model below ties the implied electron density and temperature profiles to the ion and does not provide a species-only gradient control.

## Matched electron response

At common `omn = omt = 2`, `kymin = 0.7` and `coll = 0`, the kinetic model gave $(\gamma,\omega)=(4.176,+0.944)$ and the adiabatic model gave $(0.136,-0.029)$ in normalized GENE units. Growth fell by **96.7%**. Both IV runs converged, and the kinetic and adiabatic final profiles have complex overlap 0.9905. The change is visible in the amplitude envelope. The kinetic disturbance has a dip at the middle of the plotted turn, where the adiabatic disturbance peaks.

In the supported one-ion GENE path, the nonzonal adiabatic response is $\delta n_e/n_e=e\phi_1/T_e$. The equilibrium electron density is set by ion charge density and its temperature matches the first ion temperature. GENE requires `tau = 1` for this configuration. The algebraic response preserves quasineutral field coupling while omitting the electron orbit dynamics and independent electron kinetic response. The test demonstrates strong closure sensitivity at one matched point. The specific instability mechanism and whether both closures select the same branch remain open.

Before the nominal ion recurrence time (42.187), the adiabatic fit on $t=35$ to 40 already gave growth 0.13613 and signed frequency −0.02939. The run terminated at $t=48.052$. The measured negative frequency is a sign change between the two electron models. No frequency changed sign in the qualified kinetic density or wavenumber curves. Absolute accuracy of the weak adiabatic rates still needs a targeted velocity-grid and timestep check. [Exact closure inputs, fit windows, and field equation](deuterium_meeting.md#what-adiabatic-electrons-change)

## Methods and reproducibility

The collisional kinetic scans use GENE **3.1 patch 5** at source revision `a0d2f213c5e22eed3b9f1bf4e40530c6292a9143`, an electrostatic local ring dipole (`beta = debye2 = 0`), singly charged equal-density populations at equal temperature, deuterium and electron code masses 2 and 0.00054462, `mref = 1`, Landau `coll = 0.01`, automatic stepping, `lv = 3.5` and `lw = 12.25`. Each new run used `24 × 48 × 24`, one MPI rank and one OpenMP thread. The reference model retains its original ring radius, current, geometry, diagnostics, and numerical dissipation. The two new inputs change only `kymin` relative to the earlier same-gradient economical `kymin = 1.0` inputs. The full-precision fit estimates and the complete namelists are available through the linked records.

The curves keep one value per coordinate. At `kymin = 0.7`, the density plot uses economical `omn = 1, 2, 3` values and conservative `omn = 0.5, 4, 5` values. The earlier two-grid comparison found maximum fitted differences of 0.227% in growth and 0.075% in frequency at the three shared points. The `omn = 2` wavenumber curve uses the conservative grid at `kymin = 0.5, 1.0, 1.5, 2.0` and the economical grid at 0.7. The two new runs and the previously computed outer-gradient wavenumber points use the economical grid. The overlap across sampled wavenumbers is a diagnostic, and the grid comparison at 0.7 does not establish accuracy at all wavenumbers. The prior magnetic-moment extent change shifted reference frequency by approximately 4.9%, so small frequency differences need care. [Two-grid checks](deuterium_density_pilot.md) · [Domain sensitivity](deuterium_moment_controls.md)

The plot values are the signed rates from `omega.dat` for eligible cases. Qualification requires the convergence flag, a usable nonzero diagnostic row, and no amplitude rescaling. The fit table independently estimates growth and signed frequency from the slopes of log magnitude and unwrapped phase of the final-profile projection. The sign convention is $\phi\propto e^{(\gamma+i\omega)t}$. Outputs remain in their original run directories. The exact new input files and run metadata are tracked alongside the analysis and raw-output checksums. From a fresh run directory containing `parameters` and `out/`, the executable was called with `MACHINE=mac_arm64 OMP_NUM_THREADS=1 /absolute/path/to/gene_mac_arm64 >run.log 2>run.stderr`.

- [New input files](../../configs/deuterium_final/) · [Original complete run table and exact input paths](../../results/deuterium_meeting/runs.csv) · [Supplementary run table and input paths](../../results/deuterium_final/runs.csv)
- [Original fit windows](../../results/deuterium_meeting/fits.csv) · [Extension fit windows](../../results/deuterium_final/fits.csv) · [Extension complex profiles](../../results/deuterium_final/profiles.csv)
- [Original raw-output checksums](../../results/deuterium_meeting/raw_checksums.csv) · [Extension raw-output checksums](../../results/deuterium_final/raw_checksums.csv)

Run `python3 scripts/plot_deuterium_final.py` from the repository root to regenerate the three figures offline. Add `--extract /absolute/path/to/gene-complete/runs /absolute/path/to/repository/work/deuterium_final` to verify the supplemental diagnostics against the saved raw outputs and rebuild the extension tables. [Plot and extraction script](../../scripts/plot_deuterium_final.py)
