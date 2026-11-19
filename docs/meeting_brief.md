# MAE 190 meeting brief · electron–deuterium in a magnetic dipole

**Question.** How do density gradient, binormal scale, and the electron response change the growth and propagation of a small electrostatic disturbance?

**Method.** Linear initial-value GENE runs in a ring dipole. The electron and deuterium equilibrium temperature gradients stayed at 2 throughout. Equal densities and opposite unit charges require a common equilibrium density gradient. New runs used the economical `24 × 48 × 24` grid. Two archived `32 × 48 × 32` points in the nine-cell matrix are marked in the plots. [Full methods and results](studies/deuterium_meeting.md)

- **Density gradient.** At `kymin = 0.7` the conservative-grid growth rose from 2.685 to 5.934 and signed frequency from +0.401 to +1.986 between `omn = 0.5` and 5. The economical points at 1, 2 and 3 follow the same trend. `omn = 0` remains unresolved. The trend does not identify which kinetic drive supplies the growth.
- **Wavenumber.** For each common gradient from 1 to 3, growth went down and signed frequency went up from `kymin = 0.5` to 1.0. The fastest sampled point was 0.5 at every gradient. Earlier `kymin = 0.3` remains unresolved, and the true peak could lie outside the tested interval.
- **Spatial structure.** Complex shape overlap with the reference was at least 0.99926 across the matrix. Aligned amplitude and phase show a similar dominant disturbance over the samples. That evidence does not settle whether the same branch dominates beyond this range.
- **Adiabatic electrons.** A Boltzmann density response follows the nonzonal potential without retaining electron orbit kinetics. In a matched collisionless IV control it reduced growth from 4.176 to 0.136 (**96.7% lower**) and changed signed frequency from +0.944 to −0.029. The weak growing mode was already present before the nominal ion recurrence time. Its small absolute rate and negative frequency warrant targeted grid and timestep checks before precision claims.

The earlier magnetic-moment domain test shifted the reference frequency by about 4.9%. Treat small frequency differences cautiously. The collisionless control shows sensitivity to the electron closure at one point. An independent dipole dispersion calculation and attribution to a specific trapped-electron or other kinetic mechanism are open.

## Figures

| Page | Figure | Reading guide |
| ---: | --- | --- |
| 1 | [Growth versus common density gradient](../figures/deuterium_meeting/01_density_growth.png) | Markers distinguish the archived and economical grids. |
| 2 | [Signed frequency versus common density gradient](../figures/deuterium_meeting/02_density_frequency.png) | All six converged archived points have positive signed frequency. |
| 3 | [Growth versus wavenumber](../figures/deuterium_meeting/03_wavenumber_growth.png) | One curve per common gradient. Squares are archived conservative-grid samples. |
| 4 | [Signed frequency versus wavenumber](../figures/deuterium_meeting/04_wavenumber_frequency.png) | The positive signed frequency increases with wavenumber at each gradient. |
| 5 | [Representative field-line modes](../figures/deuterium_meeting/05_mode_structure.png) | Profiles use peak normalization and a common phase alignment. The wavenumber legend gives `nz0` in parentheses. |
| 6 | [Kinetic versus adiabatic electrons](../figures/deuterium_meeting/06_adiabatic_comparison.png) | Profiles and signed GENE rates at one common collisionless point. |
| 7 | [Discrete stability map](../figures/deuterium_meeting/07_discrete_stability_map.png) | Each cell is a simulated sample. Asterisks mark the two conservative-grid cells. |

[All seven figures as one vector PDF](../figures/deuterium_meeting/meeting_figures.pdf) · [Exact inputs and run table](studies/deuterium_meeting.md#reproduction-and-limits) · [Raw-diagnostic provenance](../results/deuterium_meeting/raw_checksums.csv)
