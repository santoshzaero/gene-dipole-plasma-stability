# Findings

| Question | Evidence | Scope |
| --- | --- | --- |
| How does pair-plasma growth respond to common gradients? | At `kymin = 0.7`, 44 of 49 cases passed the solver criterion, and the largest recorded rate was 7.922 at (5, 5). | Five low-gradient cases remain unresolved even after extension. The record reports frequency to limited precision. |
| How does ion mass affect the kinetic isotope comparison? | H exceeds D at all 41 paired GENE-converged gradient points. At (2, 2), H − D is 1.924. | Shared normalized parameters and one sampled wavenumber. Grid and timestep sensitivity remain to be measured. |
| Can energy fits resolve missing rates? | Five automatic passes and one manual qualification add six exploratory estimates. Seven fits remain uncertain. | Estimates describe total-energy evolution and cannot provide a real frequency. |
| How does the ordering change with wavenumber? | H exceeds D at the five paired samples from 0.5 to 2.0. At the sampled points in this interval, both rates decrease and both frequencies increase with wavenumber. | The interval below 0.5 remains unresolved for comparison. The D result at 0.3 is flagged as anomalous and unvalidated. |

The [completed studies](research_log.md) record the rationale and evidence behind each entry. The [roadmap](research_roadmap.md) gives the checks needed to extend these findings.
