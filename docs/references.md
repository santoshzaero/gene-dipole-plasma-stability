# Sources and verification points

- F. Jenko, W. Dorland, M. Kotschenreuther, and B. N. Rogers, *Electron temperature gradient driven turbulence*, Phys. Plasmas 7, 1904 (2000). [GENE publication list](https://genecode.org/publications.html)
- T. Görler et al., *The global version of the gyrokinetic turbulence code GENE*, J. Comput. Phys. 230, 7053–7071 (2011). See the gyrokinetic formulation and reference scales. [Author-hosted paper](https://www.genecode.org/PAPERS_2/YJCPH3630.pdf)
- D. Kennedy, A. Mishchenko, P. Xanthopoulos, P. Helander, A. Bañón Navarro, and T. Görler, *Linear gyrokinetics of electron–positron plasmas in closed field-line systems* (2020). See the ring-dipole implementation and Appendix B on coordinates. [Journal article](https://www.cambridge.org/core/journals/journal-of-plasma-physics/article/linear-gyrokinetics-of-electronpositron-plasmas-in-closed-fieldline-systems/DDDA441F5C292F9AC735E6BF4579B088)
- A. Mishchenko, G. G. Plunk, and P. Helander, *Electrostatic stability of electron–positron plasmas in dipole geometry* (2018). This concerns a kinetic pair plasma, with limits that must be matched before benchmarking. [Authors' preprint](https://arxiv.org/abs/1711.08021)
- G. G. Plunk, P. Helander, P. Xanthopoulos, and J. W. Connor, *Collisionless microinstabilities in stellarators. III. The ion-temperature-gradient mode*, Phys. Plasmas 21, 032112 (2014). Equations 2–5 provide the starting kinetic-ion/Boltzmann-electron relation and definitions for the planned analytical benchmark. [Paper via UKAEA](https://scientific-publications.ukaea.uk/wp-content/uploads/Published/POPvol20p122506.pdf)

## Local primary evidence

These paths refer to an independently obtained GENE tree at revision `a0d2f213c5e22eed3b9f1bf4e40530c6292a9143`. The tree and manual are obtained with GENE. [GENE access](https://www.genecode.org/license.html)

| File or section | Verification |
| --- | --- |
| `doc/gene.tex`, box, species, units, notation and omega output | Grid and input semantics, reference scales, diagnostic columns and zero placeholders |
| `src/*dipole*.F90` | Ring inputs, surface selection, field-line tracing |
| `src/convergence_monitoring.F90`, `src/initial_value_comp.F90` | Complex log-ratio, tolerance, final stored output and solver message |
| `src/diag_energy.F90` | Total-energy column |
| `src/profiles.F90`, `src/adiabatic_response.F90`, `src/fieldsolver*.F90` | Quasineutral equilibrium checks and adiabatic response |
| `python-diag/pydiag/data/fieldlib.py` and the manual field output section | Binary record format and potential component |

- GENE 3.1 patch 5, `src/coordinates.F90` and `src/gauss.quadrature.F90`. The magnetic-moment coordinate initialization, default quadrature choice, and rescaling of the quadrature nodes and weights were checked in the local source tree.
