# Edit your own GENE input after the class benchmark

Copy `parameters.txt` into a new study directory under the name `parameters` before editing. Retain `comp_type = 'IV'` for every new study. Keep the shared benchmark exact.

| Setting | What it controls | Example input choice |
| --- | --- | --- |
| `mass`, `charge` in each `&species` | Species mass relative to the reference mass and signed charge in elementary-charge units | Pair example uses masses 1 and 1 and charges +1 and −1. The deuterium example uses masses 2 and 0.00054462 with `mref = 1.0` in proton-mass units. |
| `dens`, `temp` | Normalized equilibrium density and temperature | Both inputs start at 1 for both species. A temperature ratio can be changed through `temp`, with reference units and collision normalization checked. |
| `omn` | Normalized negative logarithmic density gradient | For a neutral equal-density pair or singly charged electron–ion plasma, try `omn = 1` for **both** species. |
| `omt` | Normalized negative logarithmic temperature gradient | Keep both at 2 for a density-only test. A temperature-gradient study can choose other values consistent with its intended equilibrium. |
| `kymin` in `&box` | Normalized binormal wavenumber when `nky0 = 1`, `ky0_ind = 1` | Change 0.7 to 0.5 in a separate run and leave the gradients fixed. |

For an electron–ion study, start from the deuterium input's explicit mass reference. Changing the positive species to hydrogen changes its mass from 2 to about 1 in those units. Do not compare physical frequencies across different reference normalizations without converting the units. See the [normalization guide](../../docs/technical/normalization.md).

**Equilibrium checks.** Charge neutrality requires the charge-weighted equilibrium densities to sum to zero. For a single electron and a single singly charged positive species, this fixes equal densities. Equilibrium gradient consistency also requires the charge-weighted quantity `dens × omn` to sum to zero, so the two `omn` values must agree. A density-ratio change or an independent density-gradient change needs a justified modified equilibrium, such as an additional species with charge and gradient balances worked out, or a separately justified approximation. GENE accepting an input does not establish that its equilibrium is physical.

For any new setting record the exact input, measured timestep, solver status, growth, signed frequency and runtime. Check important results using a suitable finer grid. The economical reference grid has not been validated for every composition or gradient.
