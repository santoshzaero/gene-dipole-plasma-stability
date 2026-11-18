# How to read the results

On a gradient heatmap, pick a density-gradient column and a temperature-gradient row. The number and color show the growth rate for that simulation. On the [isotope difference map](../../figures/regenerated/isotope_gene_only.png), each colored cell instead shows hydrogen minus deuterium. At `omn = omt = 2` it is $6.096 - 4.172 = 1.924$. A blank cell indicates that a comparable solver-converged result was unavailable. In the historical maps, an asterisk marks a qualified estimate from energy, a dagger marks an uncertain estimate, and N/C indicates that the map has no usable comparison at that cell.

On [wavenumber plots](../research_log.md#5-perpendicular-wavenumber-scan), each dot is a sampled wavenumber. The curves connect sampled results and the shaded low-wavenumber interval needs follow-up. The frequency figure uses the same samples as the growth-rate figure.

Convergence has two parts. First, GENE checks whether the evolving potential is consistent with a mode that can be summarized by a growth rate and a frequency. Then we check whether those numbers hold up when we refine the computational grid and timestep. A run that reaches its step limit can leave an unresolved result. A zero stored in an unresolved run cannot establish stability.

| Kind of statement | Example from this project |
| --- | --- |
| Simulation result | The reported normalized growth rate at the reference deuterium point was 4.172. |
| Physical interpretation | Under the tested conditions, the deuterium perturbation grew more slowly than the hydrogen perturbation. |
| Hypothesis | Changing ion mass may alter the dominant mode or its spatial structure. Field-line profiles and converged comparisons can test this. |

The scans support statements about sampled, modeled linear disturbances. Stronger claims about transport, confinement time, or a whole device would require additional modeling or experimental evidence.
