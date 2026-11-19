# MAE 190 shared GENE benchmark · electron–positron IV

Start with [parameters](parameters). All four students should run this exact input before changing composition or gradients. It uses an electron and a positron with equal code mass 1 and opposite charges, equal density and temperature of 1, both gradients set to 2, and dipole geometry. The grid is `24 × 48 × 24` at `kymin = 0.7`, with `lv = 3.5`, `lw = 12.25`, and automatic timestep selection. The common test measures how a small plasma disturbance grows and whether it oscillates.

| Input | Use |
| --- | --- |
| [parameters](parameters) | Tested electron–positron initial-value (IV) benchmark. Use this for the class comparison. |
| [parameters_deuterium_iv](parameters_deuterium_iv) | Exact economical electron–deuterium reference. Use for the separate deuterium project, with its proton-reference units and physical masses. |

Both inputs use IV only (`comp_type = 'IV'`) and are directly editable GENE inputs. They use the active physics and namelist structure of the course example while omitting its generated `&info` block, machine settings and checkpoint output. The shared IV version enables the omega diagnostic and disables the high-volume velocity-space output. The professor's original file and historical build metadata were consulted locally.

## Build and run

Obtain GENE independently through the GENE development team. The recorded build used **GENE 3.1 patch 5**, revision `a0d2f213c5e22eed3b9f1bf4e40530c6292a9143`, double precision, GNU Fortran 16.2.0, Open MPI, FFTW, and OpenBLAS on Apple Silicon. It used one MPI rank and one OpenMP thread. On macOS or Linux, follow GENE's build instructions with the matching site or machine configuration and record the compiler, libraries, ranks and precision. On other systems use a GENE-supported environment and its documented launcher. The executable is platform-specific. [Obtain GENE](https://www.genecode.org/license.html) · [Local build notes](../../docs/research_log.md#1-installation-and-validation)

Download this folder with its inputs and scripts or obtain the pinned repository snapshot. From this folder, verify the [checksums](SHA256SUMS) with `shasum -a 256 -c SHA256SUMS` on macOS or `sha256sum -c SHA256SUMS` on Linux. Set the machine name for your build if required. For the recorded Mac build:

```sh
MACHINE=mac_arm64 sh run.sh /absolute/path/to/gene_mac_arm64
```

The launcher creates a fresh run directory and prints its location. To run manually, create a new directory with an `out` subdirectory, copy in the exact file named `parameters`, and launch GENE there with one rank and one thread, saving stdout to `run.log`. Use a one-rank MPI launch if your installation requires it. Then call `sh read_rates.sh /absolute/path/to/run`. No Python installation is needed.

## Expected output and agreement

The local IV run met GENE's temporal convergence check in **7.011 s**. Its `out/omega.dat` row was **0.700, 4.314, +0.000**, in normalized GENE units. The log-ratio diagnostic uses the real part for growth and the imaginary part for signed frequency in the convention `exp[(gamma + i omega)t]`. Read the printed sign, even for a negative frequency in another case. Late-time fits to the saved complex potential yielded growth about 4.3145–4.3152 and zero phase slope on the windows checked. GENE found a growing mode with no resolved rotation. The IV calculation identifies the mode reached from its specified initialization.

Use [comparison.csv](comparison.csv) to record all four results. Aim to match the four displayed significant digits of growth, using **absolute differences of 0.002 in growth and 0.001 in signed frequency** as provisional investigation thresholds. The growth threshold accommodates the printing step and observed fit-window sensitivity. A relative tolerance is undefined around zero frequency. These thresholds are for identical-input reproducibility and have not yet been tested across class computers. They do not establish grid or velocity-domain convergence. Runtime will vary by machine.


If results differ, confirm the hash, compiler/build, rank/thread counts, diagnostic path and convergence line. A zero or missing omega file without clean convergence is not a measurement. Check `run.log` and `run.stderr` before trying a repeat. Compare the sign and complex potential when diagnosing a different mode. After class replication, use the [editing guide](editing.md).
