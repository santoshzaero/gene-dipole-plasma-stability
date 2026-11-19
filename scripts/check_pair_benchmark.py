#!/usr/bin/env python3
"""Check the archived electron–positron IV mode and regenerate its figures."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from compare_parallel_resolution import ROOT, capture, plt, read_fields

INPUT = ROOT / "benchmarks/classmate/parameters.txt"
DATA = ROOT / "results/pair/classmate_iv"
FIGURES = ROOT / "figures/pair"
PRINT_HALF_STEP = 0.0005
COLUMN_NAMES = (
    "time,projection_real,projection_imag,peak_real,peak_imag,relative_spatial_residual"
)


def extract(run, original, data):
    if (run / "parameters").read_bytes() != INPUT.read_bytes():
        raise ValueError("The verification run must use the cleaned class input")
    log = (run / "run.log").read_text()
    metadata = (run / "out/parameters.dat").read_text()
    if "Linear growth rate is converged" not in log or "rescaled amplitudes" in log:
        raise ValueError("Expected clean IV convergence")
    capture(r"We have\s+(1) MPI tasks", log)
    for key, expected in (("comp_type", "'IV'"), ("PRECISION", "DOUBLE"), ("ENDIANNESS", "LITTLE"),
                          ("OMP_NUM_THREADS", "1"), ("nx0", "1"), ("nky0", "1"), ("nz0", "24"),
                          ("nv0", "48"), ("nw0", "24"), ("n_fields", "1")):
        if capture(rf"^{key}\s*=\s*(\S+)", metadata) != expected:
            raise ValueError(f"Unexpected GENE metadata: {key}")
    out = run / "out"
    digests = {}
    for name in ("field.dat", "omega.dat", "omega_Ef_species.dat"):
        content = (out / name).read_bytes()
        if content != (original / "out" / name).read_bytes():
            raise ValueError(f"Benchmark diagnostics differ after cleanup: {name}")
        digests[name] = hashlib.sha256(content).hexdigest()

    t, phi, saved = read_fields(out / "field.dat", 24)
    nonzero = np.any(phi != 0, axis=1)  # The initial all-zero field has undefined phase.
    final = phi[-1]
    peak = np.argmax(np.abs(final))
    profile = final / final[peak]
    projection = phi @ profile.conj() / np.vdot(profile, profile).real
    residual = np.zeros(len(t))
    residual[nonzero] = (np.linalg.norm(phi[nonzero] - projection[nonzero, None] * profile, axis=1)
                         / np.linalg.norm(phi[nonzero], axis=1))
    amplitude_energy = np.loadtxt(out / "energy.dat", usecols=(0, 1))
    good_energy = np.isfinite(amplitude_energy).all(axis=1) & (amplitude_energy[:, 1] > 0)
    amplitude_energy = amplitude_energy[good_energy]
    increasing = np.r_[np.diff(amplitude_energy[:, 0]) > 0, True]
    energy = amplitude_energy[increasing]
    raw_ky, raw_gamma, raw_omega = np.loadtxt(out / "omega.dat")
    consecutive_steps = int(capture(r"^istep_omega\s*=\s*(\d+)", metadata))
    previous = phi[-1 - consecutive_steps]
    log_ratio = np.log(final / previous) / (t[-1] - t[-1 - consecutive_steps])
    native = np.average(log_ratio, weights=np.abs(previous))
    verify = {
        "release": capture(r"^RELEASE\s*=\s*(.+?)\s*$", metadata),
        "source_revision": capture(r"^GIT_BRANCH\s*=\s*(\w+)", metadata),
        "input_sha256": hashlib.sha256(INPUT.read_bytes()).hexdigest(),
        "common_raw_diagnostic_sha256": digests,
        "gene_converged": True,
        "kymin": raw_ky,
        "gene_growth": raw_gamma,
        "gene_signed_frequency": raw_omega,
        "species_energy_diagnostic": np.loadtxt(out / "omega_Ef_species.dat").tolist(),
        "wallclock_s": float(capture(r"Total wallclock time for GENE:\s+([\d.]+)", log)),
        "steps_reported": int(capture(r"Computed\s+(\d+) time steps", log)),
        "raw_field_records": saved,
        "applied_dt": float(np.median(np.diff(t))),
        "peak_z_index_zero_based": int(peak),
        "max_abs_raw_field_real_component": float(np.max(np.abs(phi.real))),
        "late_spatial_log_ratio_growth": native.real,
        "late_spatial_log_ratio_signed_frequency": native.imag,
    }
    data.mkdir(parents=True, exist_ok=True)
    np.savetxt(data / "field_history.csv", np.column_stack((t[nonzero], projection[nonzero].real,
               projection[nonzero].imag, phi[nonzero, peak].real, phi[nonzero, peak].imag,
               residual[nonzero])), delimiter=",", header=COLUMN_NAMES, comments="", fmt="%.17g")
    np.savetxt(data / "energy_history.csv", energy, delimiter=",", header="time,free_energy",
               comments="", fmt="%.17g")
    (data / "verification.json").write_text(json.dumps(verify, indent=2) + "\n")


def relative_phase(field):
    return np.unwrap(np.angle(field / field[-1]))


def fit(time, values):
    centered = time - np.mean(time)
    slope = np.dot(centered, values - np.mean(values)) / np.dot(centered, centered)
    line = slope * centered + np.mean(values)
    return slope, line


def analyze(data, figures):
    t, ar, ai, pr, pi, residual = np.loadtxt(data / "field_history.csv", skiprows=1, delimiter=",").T
    amplitude = ar + 1j * ai
    log_amp = np.log(np.abs(amplitude))
    projected_phase = relative_phase(amplitude)
    peak_phase = relative_phase(pr + 1j * pi)
    energy_t, energy = np.loadtxt(data / "energy_history.csv", skiprows=1, delimiter=",").T
    fits = []
    for width in (1.5, 1.0, 0.75, 0.5):
        use = t >= t[-1] - width
        ts = t[use]
        energy_use = (energy_t >= ts[0]) & (energy_t <= ts[-1])
        growth, line = fit(ts, log_amp[use])
        omega, _ = fit(ts, projected_phase[use])
        peak_omega, _ = fit(ts, peak_phase[use])
        energy_growth, _ = fit(energy_t[energy_use], 0.5 * np.log(energy[energy_use]))
        rms = np.sqrt(np.mean((log_amp[use] - line)**2))
        fits.append((ts[0], ts[-1], ts.size, growth, energy_growth, omega, peak_omega,
                     np.ptp(projected_phase[use]), np.ptp(peak_phase[use]), rms, max(residual[use])))
    np.savetxt(data / "late_fits.csv", fits, delimiter=",", comments="", fmt="%.17g", header=(
        "start,end,samples,growth,energy_growth,signed_frequency,peak_signed_frequency,"
        "phase_span_rad,peak_phase_span_rad,log_amplitude_rms,max_relative_spatial_residual"
    ))

    late = t >= fits[0][0]
    ts = t[late]
    for injected in (-PRINT_HALF_STEP, -1e-8, 1e-8, PRINT_HALF_STEP):
        rotated = amplitude[late] * np.exp(1j * injected * (ts - ts[-1]))
        recovered, _ = fit(ts, relative_phase(rotated))
        if not np.isclose(recovered, injected, rtol=1e-7, atol=0):
            raise ValueError("Phase extraction failed to recover injected signed drift")
    figures.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7.2, 4.3), layout="constrained")
    _, line = fit(ts, log_amp[late])
    ax.semilogy(t, np.abs(amplitude), color="#176d81", label=r"Projected $|\phi|$")
    ax.semilogy(ts, np.exp(line), color="#ba4829", ls="--", label="Late exponential fit")
    ax.axvspan(ts[0], ts[-1], alpha=0.10, color="#176d81")
    ax.set(title="Electron–positron IV benchmark · amplitude", xlabel="Normalized GENE time",
           ylabel="Projected potential amplitude (GENE units)")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False)
    fig.savefig(figures / "classmate_iv_amplitude.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.2, 4.3), layout="constrained")
    ax.plot(ts, 1e3 * projected_phase[late], color="#176d81", label="Projection and peak node (coincident)")
    for sign in (-1, 1):
        ax.plot(ts, sign * 1e3 * PRINT_HALF_STEP * (ts - ts[-1]), color="#a44e31", ls="--",
                label=r"Drift for $\omega=\pm0.0005$" if sign == -1 else None)
    ax.set(title="Electron–positron IV benchmark · unwrapped phase", xlabel="Normalized GENE time",
           ylabel="Phase relative to final sample (mrad)")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False)
    fig.savefig(figures / "classmate_iv_phase.png", dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", nargs=2, type=Path, metavar=("CLEANED", "ORIGINAL"))
    parser.add_argument("--data", type=Path, default=DATA)
    parser.add_argument("--figures", type=Path, default=FIGURES)
    args = parser.parse_args()
    if args.runs:
        extract(*args.runs, args.data)
    analyze(args.data, args.figures)
