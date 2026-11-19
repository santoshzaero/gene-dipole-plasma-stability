#!/usr/bin/env python3
"""Extract reproducible common-window rates and mode overlap from a class run."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from compare_parallel_resolution import fit, read_case

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "results/convergence/deuterium_combined/original_profile.csv"
WINDOWS = ((1.50, 2.00), (1.40, 1.90), (1.55, 2.05))


def measure(directory):
    supplied = (directory / "parameters").read_bytes()
    benchmark = (ROOT / "benchmarks/parameters").read_bytes()
    archived = (ROOT / "configs/isotope/deuterium/omn_2_omt_2/parameters").read_bytes()
    if supplied not in (benchmark, archived):
        raise ValueError("Input must match the cleaned deuterium benchmark or its archived original")
    stats, profile, history, energy = read_case(directory, 32)
    if not stats["gene_converged"] or "rescaled amplitudes" in (directory / "run.log").read_text():
        raise ValueError("Benchmark requires GENE convergence without amplitude rescaling")
    if (stats["release"], stats["source_revision"]) != (
        "3.1 - patch 5", "a0d2f213c5e22eed3b9f1bf4e40530c6292a9143"
    ):
        raise ValueError("Unexpected GENE release or source revision")
    t, log_amp, phase = history[:, :3].T
    ref = np.loadtxt(REFERENCE, delimiter=",", skiprows=1)
    if not np.allclose(profile[:, 0], ref[:, 0], rtol=0, atol=1e-12):
        raise ValueError("Unexpected parallel coordinate layout")
    a, b = (values[:, 1] + 1j * values[:, 2] for values in (profile, ref))
    overlap = float(abs(np.vdot(a, b)) / (np.linalg.norm(a) * np.linalg.norm(b)))

    windows = []
    for i, (start, end) in enumerate(WINDOWS):
        if min(t[-1], energy[-1, 0]) < end:
            if i == 0:
                raise ValueError("Run ended before the primary comparison window")
            continue
        gamma, amp_rms = fit(t, log_amp, start, end)
        omega, phase_rms = fit(t, phase, start, end)
        gamma_energy, _ = fit(energy[:, 0], 0.5 * np.log(energy[:, 1]), start, end)
        windows.append(dict(start=start, end=end, gamma=gamma, omega=omega,
                            gamma_energy=gamma_energy, amplitude_fit_rms=amp_rms,
                            phase_fit_rms_rad=phase_rms))
    return {**stats, "input_sha256": hashlib.sha256(supplied).hexdigest(),
            "complex_profile_overlap": overlap, "fit_windows": windows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path, help="Completed benchmark run directory")
    args = parser.parse_args()
    print(json.dumps(measure(args.run), indent=2))
