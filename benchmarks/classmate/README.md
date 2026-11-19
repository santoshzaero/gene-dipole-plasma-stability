# MAE 190 shared GENE benchmark · electron–positron IV

Share **[parameters.txt](parameters.txt)** as the single benchmark attachment. All four students use that exact file before changing composition or gradients. It contains only the GENE namelist. Save it in the run directory under the name `parameters` with no extension. The file is plain ASCII with Unix line endings. Its SHA-256 is `0841cf83c3c3ce9928fa891ef1392914e20de3328b9c47d6872cbf21daff2bab`.

The IV case uses equal electron and positron masses, densities and temperatures, opposite unit charges, `omn = omt = 2` for both species, and dipole geometry. The grid is `24 × 48 × 24` with `kymin = 0.7`, `lv = 3.5`, `lw = 12.25`, and automatic timestep selection. The separate [electron–deuterium IV reference](parameters_deuterium_iv) uses physical masses in proton-reference units. Use the electron–positron input for the class comparison.

## Run on Windows using WSL2 Ubuntu

1. On Windows 11 or Windows 10 version 2004 or later, open PowerShell as Administrator and run `wsl --install -d Ubuntu`. Restart if prompted. Open Ubuntu and create a Linux user. In PowerShell, `wsl -l -v` should list Ubuntu with version `2`. If needed, use `wsl --set-version Ubuntu 2` with the distribution’s listed name. [Microsoft WSL installation guide](https://learn.microsoft.com/en-us/windows/wsl/install)
2. Obtain GENE independently through the GENE Development Team. For comparison with the reference, use **GENE 3.1 patch 5**, revision `a0d2f213c5e22eed3b9f1bf4e40530c6292a9143` when available. Keep the source and run directories in the Ubuntu home filesystem. Build a **double-precision CPU Linux** executable using your release’s `INSTALL` and machine configuration. The macOS executable targets Apple Silicon and cannot run in WSL2. [Obtain GENE](https://www.genecode.org/license.html)
3. For a GNU/Open MPI build with FFTW and system BLAS/LAPACK, the Ubuntu starting packages are:

   ```sh
   sudo apt update
   sudo apt install build-essential gfortran cmake git pkg-config \
     openmpi-bin libopenmpi-dev libfftw3-dev libopenblas-dev liblapack-dev
   ```

   The recorded GENE tree ships an `ubuntu_gfortran` Make profile for older x86-64 Ubuntu. Review compiler wrappers, precision and library paths before using it. If that profile matches after configuration, its build entry point is `MACHINE=ubuntu_gfortran make` from the GENE source root. The expected executable for that profile is `bin/gene_ubuntu_gfortran`. Adapt the machine profile and executable name if needed, especially on Windows ARM. The shipped profile enables ScaLAPACK and HDF5 support through FUTILS. If you retain these options, install `libscalapack-openmpi-dev` and `libhdf5-openmpi-dev` and configure their link paths. They can be disabled in a suitable Make profile for this local electrostatic IV case. Leave SLEPc disabled. Build requirements vary with the revision and optional features, and this procedure has yet to be tested on a classmate’s WSL machine.
4. Save `parameters.txt` to Windows Downloads, then run the following in Ubuntu. Substitute your Windows username and your Ubuntu GENE executable’s absolute path.

   ```sh
   run_dir=$(mktemp -d "$HOME/gene-pair.XXXXXX")
   cd "$run_dir"
   mkdir out
   cp '/mnt/c/Users/YOUR_WINDOWS_NAME/Downloads/parameters.txt' parameters
   printf '%s  parameters\n' 0841cf83c3c3ce9928fa891ef1392914e20de3328b9c47d6872cbf21daff2bab | sha256sum -c - &&
     OMP_NUM_THREADS=1 mpirun -np 1 /absolute/path/to/gene_ubuntu_gfortran >run.log 2>&1
   grep -F 'Linear growth rate is converged' run.log
   cat out/omega.dat
   ```

   Confirm the hash before running GENE. A matching build can optionally launch directly with one rank if its GENE documentation recommends that. Use a fresh directory for each attempt. When saving manually in a Windows editor, keep plain text, use LF line endings without a BOM, and ensure the filename inside Ubuntu is exactly `parameters`.
5. A converged `out/omega.dat` has columns **`kymin`, normalized growth, signed normalized real frequency**. The local reference row is `0.700  4.314  0.000`. Check the convergence line and the absence of amplitude rescaling before recording it. A zero row from a run that failed to converge can be a placeholder. Record the GENE version, compiler, MPI ranks, thread count and runtime along with the rates.

## Expected result and comparison

The cleaned input converged locally in 69 reported steps with growth **4.314**, signed real frequency **0.000**, and wall time **5.203 s**. It reproduced the original run’s complex field and frequency files byte for byte. The original local runtime was **7.011 s**. The field grew exponentially with constant phase. Independent fits at the peak node and across the field recovered zero phase slope, consistent with a purely growing dominant mode. Treat the three-decimal display conservatively as **$|\omega| \lesssim 0.0005$** for this run. [Frequency check and plots](../../docs/studies/pair_benchmark_frequency.md)

For identical-input class replication use provisional investigation thresholds of **0.002 absolute growth** and **0.001 absolute signed frequency**. These account for printed precision and local fitting variability and remain provisional pending cross-computer runs. Relative error is ill-conditioned near zero. The [comparison sheet](comparison.csv) is for recording results. The local build was GNU Fortran 16.2.0, Open MPI, FFTW and OpenBLAS on Apple Silicon, with one MPI rank and one OpenMP thread. [Local build record](../../docs/research_log.md#1-installation-and-validation)

If rates differ, compare the checksum, build and convergence log first. If the run exits early, keep `run.log` and `out/parameters.dat`. After the benchmark, follow the [editing guide](editing.md) for new IV cases.
