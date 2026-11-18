# Numerical methodology

GENE evolved the linear initial-value problem (`comp_type = 'IV'`) with a single radial mode and a single binormal mode. For an isolated mode one can write $g_s(t)=\hat g_s e^{\lambda t}$, where $\hat g_s$ is the time-independent eigenfunction and $\lambda=\gamma+i\omega$ in the GENE logarithmic time-evolution convention. The complex-frequency convention $e^{-i\Omega t}$ instead uses $\Omega=i\lambda$ and reverses the sign of the real frequency. Tables here use the signed GENE output. A consistently dominant mode can agree with an eigenvalue calculation. The runs archived here used time evolution.

| Setting | Recorded choice |
| --- | --- |
| `nx0, nky0, nz0` | 1, 1, 32 |
| `nv0, nw0` | 48, 32 |
| `lv, lw` | 3.5, 12.25 |
| `lx, nexc, adapt_lx` | 1, 0, F |
| `ntimesteps` | 1000 for the pair gradient grid, 5000 for its five extensions and both isotope scans |
| `calc_dt, init_cond` | T, `alm` |
| `hyp_z, hyp_z_with_dz_prefactor` | 4, F |
| `istep_omega` | 10 steps |
| `istep_field, istep_energy` | 1 step in the full gradient and isotope scan inputs |
| `istep_vsp` | 0 for the main scans |

GENE uses field-aligned position $z$, parallel velocity $v_\parallel$, and magnetic moment $\mu$ (proportional to perpendicular kinetic energy divided by local field strength). `nz0` controls sampling along the field line, `nv0` samples the signed parallel velocity, and `nw0` samples the nonnegative magnetic moment. The velocity extents `lv` and `lw` matter along with the number of grid points. Increase resolution at fixed extent first, then test whether changing extent alters the result.

For the deuterium reference, the resolved parameter output gives RK4 and a calculated timestep cap of $8.350\times10^{-4}$ in code time. The run finished after 2,459 steps with wallclock 232.111 s. Larger grids can reduce the stable timestep, so a constant step limit can yield different final physical or normalized times. Track both ending time and steps when comparing grids. The reported solver result and wallclock can be compared in the [run index](../../results/run_index.csv).
