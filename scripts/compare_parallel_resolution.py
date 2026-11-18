#!/usr/bin/env python3
"""Reproduce the deuterium parallel-grid comparison without running GENE."""
import argparse
import csv
import gzip
import hashlib
import io
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "results/convergence/deuterium_nz32_nz64"
FIGURE = ROOT / "figures/convergence/deuterium_nz32_nz64.png"


def capture(pattern, text):
    match = re.search(pattern, text, flags=re.MULTILINE)
    if not match:
        raise ValueError(f"Missing diagnostic: {pattern}")
    return match[1]


def read_fields(path, nz):
    # This build writes paired 4-byte Fortran record markers around each
    # double timestamp and each (1, 1, nz) complex-double potential record.
    dtype = np.dtype([
        ("time_open", "<i4"), ("t", "<f8"), ("time_close", "<i4"),
        ("phi_open", "<i4"), ("phi", "<c16", (nz,)), ("phi_close", "<i4"),
    ])
    if path.stat().st_size % dtype.itemsize:
        raise ValueError(f"Incomplete field record: {path}")
    data = np.fromfile(path, dtype=dtype)
    if len(data) < 2 or not all(
        np.all(data[name] == size) for name, size in (
            ("time_open", 8), ("time_close", 8),
            ("phi_open", 16 * nz), ("phi_close", 16 * nz),
        )
    ):
        raise ValueError(f"Unexpected field record layout: {path}")
    t, phi = data["t"], data["phi"]
    if not np.all(np.isfinite(t)) or not np.all(np.isfinite(phi)) or np.any(np.diff(t) < 0):
        raise ValueError(f"Invalid field samples: {path}")
    # GENE can write a duplicate timestamp when it emits final diagnostics.
    keep = np.r_[np.diff(t) > 0, True]
    return t[keep], phi[keep], len(data)


def local_rate_spread(time, phi):
    """Post-process the spatial spread term on successive 10-sample windows."""
    previous, current = phi[:-10], phi[10:]
    weights = np.abs(previous)
    valid = weights > np.finfo(float).eps
    ratios = np.divide(current, previous, out=np.ones_like(previous), where=valid)
    elapsed = time[10:] - time[:-10]
    rate = np.log(ratios) / elapsed[:, None]
    mean = np.average(rate, axis=1, weights=weights)
    variance = np.average(np.abs(rate - mean[:, None])**2, axis=1, weights=weights)
    spread = np.sqrt(6.7 * variance / (phi.shape[1] - 1))
    return np.r_[np.full(10, np.nan), spread]


def read_case(directory, nz):
    out = directory / "out"
    log = (directory / "run.log").read_text()
    metadata = (out / "parameters.dat").read_text()
    for pattern in (
        rf"^nz0\s*=\s*({nz})\s*$", r"^nx0\s*=\s*(1)\s*$",
        r"^nky0\s*=\s*(1)\s*$", r"^nv0\s*=\s*(48)\s*$",
        r"^nw0\s*=\s*(32)\s*$", r"^n_fields\s*=\s*(1)\s*$",
        r"^PRECISION\s*=\s*(DOUBLE)\s*$", r"^ENDIANNESS\s*=\s*(LITTLE)\s*$",
        r"^OMP_NUM_THREADS\s*=\s*(1)\s*$", r"^timescheme\s*=\s*('RK4')",
    ):
        capture(pattern, metadata)
    capture(r"We have\s+(1) MPI tasks", log)
    ky, gamma, omega = np.loadtxt(out / "omega.dat")
    if ky != 0.7:
        raise ValueError("Unexpected wavenumber")
    t, phi, frames = read_fields(out / "field.dat", nz)

    # Trace samples in dipole.F90 are spaced by one tube length / (nz - 1)
    # and copied in order to the geometry indices used by this diagnostic.
    geometry = (out / "dipole.dat").read_text().split("/", 1)[1]
    geometry_rows = [line for line in geometry.splitlines() if len(line.split()) == 16][:nz]
    field_strength = np.loadtxt(geometry_rows)[:, 6]
    if len(field_strength) != nz or not np.all(np.isfinite(field_strength)):
        raise ValueError(f"Incomplete dipole geometry: {out}")

    # Normalize final profile by the peak complex value, fixing its phase
    # at the strongest sample. Project each snapshot onto this template.
    final = phi[-1]
    profile = final / final[np.argmax(np.abs(final))]
    projection = phi @ profile.conj() / np.vdot(profile, profile).real
    overlap = np.clip(np.abs(phi @ profile.conj()) /
                      (np.linalg.norm(profile) * np.linalg.norm(phi, axis=1)), 0, 1)
    field_history = np.column_stack(
        (t, np.log(np.abs(projection)), np.unwrap(np.angle(projection)), overlap, local_rate_spread(t, phi))
    )
    energy = np.loadtxt(out / "energy.dat", usecols=(0, 1))
    valid = np.isfinite(energy).all(axis=1) & (energy[:, 1] > 0)
    energy = energy[valid]
    energy = energy[np.r_[np.diff(energy[:, 0]) > 0, True]]
    stats = {
        "nz0": nz, "nv0": 48, "nw0": 32, "kymin": ky,
        "gene_converged": "Linear growth rate is converged, exiting time loop" in log,
        "gamma": gamma, "omega": omega,
        "wallclock_s": float(capture(r"Total wallclock time for GENE:\s+([\d.]+)", log)),
        "steps": int(capture(r"Computed\s+(\d+) time steps", log)),
        "final_time": t[-1], "dt": float(np.median(np.diff(t))),
        "dt_max": float(capture(r"^dt_max\s*=\s*([\d.Ee+-]+)", metadata)),
        "field_records": frames, "unique_field_times": len(t),
        "release": capture(r"^RELEASE\s*=\s*(.+?)\s*$", metadata),
        "source_revision": capture(r"^GIT_BRANCH\s*=\s*(\w+)", metadata),
    }
    return stats, np.column_stack((np.linspace(0, 1, nz), profile.real, profile.imag,
                                  field_strength)), field_history, energy


def fit(time, values, start, end):
    use = (time >= start) & (time <= end)
    x, y = time[use], values[use]
    if len(x) < 10:
        raise ValueError(f"Insufficient fit samples in {start:g}–{end:g}")
    slope, intercept = np.polyfit(x, y, 1)
    rms = np.sqrt(np.mean((y - (slope * x + intercept))**2))
    return slope, rms


def late_fits(case, common_end):
    stats, _, fields, energy = case
    t, log_amp, phase, overlap, spread = fields.T
    final = t[-1]
    windows = [(f"last_{width:g}", final - width, final) for width in (0.25, 0.5, 0.75)]
    windows.append(("common_last_0.5", common_end - 0.5, common_end))
    for window, start, end in windows:
        field_gamma, amp_rms = fit(t, log_amp, start, end)
        phase_omega, phase_rms = fit(t, phase, start, end)
        energy_gamma, energy_rms = fit(energy[:, 0], 0.5 * np.log(energy[:, 1]), start, end)
        window_mask = (t >= start) & (t <= end)
        yield {
            "nz0": stats["nz0"], "window": window, "start_t": start, "end_t": end,
            "field_gamma": field_gamma, "phase_omega": phase_omega, "energy_gamma": energy_gamma,
            "amp_rms": amp_rms, "phase_rms_rad": phase_rms, "energy_rms": energy_rms,
            "min_template_overlap": min(overlap[window_mask]),
            "median_spatial_rate_spread": np.nanmedian(spread[window_mask]),
        }


def write_records(path, records):
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)


def write_series(path, data, header):
    with path.open("wb") as sink, gzip.GzipFile(filename="", fileobj=sink, mode="wb", mtime=0) as zipped:
        with io.TextIOWrapper(zipped, encoding="ascii", newline="\n") as stream:
            np.savetxt(stream, data, header=header, comments="", delimiter=",", fmt="%.13e")


def extract(directories, dest):
    cases = [read_case(directory, nz) for directory, nz in zip(directories, (32, 64))]
    coarse, fine = [case[0] for case in cases]
    if (coarse["release"], coarse["source_revision"]) != (fine["release"], fine["source_revision"]):
        raise ValueError("Cases use different GENE source versions")
    inputs = [(directory / "parameters").read_bytes() for directory in directories]
    edited, count = re.subn(rb"(?m)^(nz0\s*=\s*)32(?=\s*$)", rb"\g<1>64", inputs[0])
    if count != 1 or edited != inputs[1]:
        raise ValueError("Input differences are not limited to nz0")
    dest.mkdir(parents=True, exist_ok=True)
    durations = [case[0]["final_time"] for case in cases]
    fits = []
    records = []
    for case, contents in zip(cases, inputs):
        stats, profile, fields, energy = case
        nz = stats["nz0"]
        records.append({**stats, "input_sha256": hashlib.sha256(contents).hexdigest()})
        fits.extend(late_fits(case, min(durations)))
        np.savetxt(dest / f"profile_nz{nz}.csv", profile, delimiter=",", comments="",
                   header="trace_fraction,phi_real_scaled,phi_imag_scaled,b_normalized", fmt="%.13e")
        write_series(dest / f"field_nz{nz}.csv.gz", fields,
                     "time,log_projected_amplitude,unwrapped_phase,template_overlap,spatial_rate_spread")
        write_series(dest / f"energy_nz{nz}.csv.gz", energy, "time,total_energy")
    write_records(dest / "runs.csv", records)
    write_records(dest / "late_fits.csv", fits)
    sources = ("parameters", "run.log", "out/parameters.dat", "out/omega.dat",
               "out/field.dat", "out/energy.dat", "out/dipole.dat")
    write_records(dest / "source_sha256.csv", [
        {"nz0": nz, "run_relative_path": name,
         "sha256": hashlib.sha256((directory / name).read_bytes()).hexdigest()}
        for nz, directory in zip((32, 64), directories)
        for name in sources
    ])

    x32, real32, imag32, b32 = cases[0][1].T
    x64, real64, imag64, b64 = cases[1][1].T
    p32 = real32 + 1j * imag32
    p64 = np.interp(x32, x64, real64 + 1j * imag64)
    overlap = abs(np.vdot(p64, p32)) / (np.linalg.norm(p64) * np.linalg.norm(p32))
    scale = np.vdot(p64, p32) / np.vdot(p64, p64)
    common = {fit["nz0"]: fit for fit in fits if fit["window"] == "common_last_0.5"}
    common_relative = {
        f"common_window_{quantity}_relative_difference_vs_nz64":
        abs(common[32][quantity] - common[64][quantity]) / abs(common[64][quantity])
        if common[64][quantity] != 0 else ""
        for quantity in ("field_gamma", "phase_omega", "energy_gamma")
    }
    both_converged = coarse["gene_converged"] and fine["gene_converged"]
    reported_differences = {}
    for quantity in ("gamma", "omega"):
        difference = abs(coarse[quantity] - fine[quantity])
        reported_differences[f"{quantity}_absolute_difference"] = difference if both_converged else ""
        reported_differences[f"{quantity}_relative_difference_vs_nz64"] = (
            difference / abs(fine[quantity]) if both_converged and fine[quantity] != 0 else ""
        )
    write_records(dest / "comparison.csv", [{
        **reported_differences,
        **common_relative,
        "wallclock_s_relative_difference_vs_nz64":
            abs(coarse["wallclock_s"] - fine["wallclock_s"]) / fine["wallclock_s"],
        "wallclock_absolute_difference_s": abs(coarse["wallclock_s"] - fine["wallclock_s"]),
        "wallclock_ratio_nz64_over_nz32": fine["wallclock_s"] / coarse["wallclock_s"],
        "complex_profile_overlap": overlap,
        "relative_profile_l2_residual": np.linalg.norm(p32 - scale * p64) / np.linalg.norm(p32),
        "max_abs_interp_b_difference": max(abs(b32 - np.interp(x32, x64, b64))),
    }])


def draw(dest, figure):
    fig, axes = plt.subplots(2, 2, figsize=(11.6, 7.5), layout="constrained")
    fig.suptitle("GENE electron–deuterium reference · parallel-grid comparison", fontweight="bold")
    energy_ax, omega_ax, mode_ax, overlap_ax = axes.flat
    with (dest / "runs.csv").open() as stream:
        records = {int(row["nz0"]): row for row in csv.DictReader(stream)}
    late_start = 0.6 * min(float(row["final_time"]) for row in records.values())
    for nz, color in ((32, "#176d81"), (64, "#b34d2a")):
        label = f"$n_z={nz}$"
        time, energy = np.loadtxt(dest / f"energy_nz{nz}.csv.gz", delimiter=",", skiprows=1).T
        energy_ax.plot(time, np.log(energy), color=color, label=label)
        t, _, phase, overlap, _ = np.loadtxt(dest / f"field_nz{nz}.csv.gz", delimiter=",", skiprows=1).T
        center = t[(t >= max(late_start, 0.05)) & (t <= t[-1] - 0.05)][::5]
        omega = (np.interp(center + 0.05, t, phase) - np.interp(center - 0.05, t, phase)) / 0.1
        omega_ax.plot(center, omega, color=color)
        reported_omega = float(records[nz]["omega"])
        if reported_omega != 0:
            omega_ax.axhline(reported_omega, color=color, linestyle=":", alpha=0.7)
        x, re_phi, im_phi, _ = np.loadtxt(dest / f"profile_nz{nz}.csv", delimiter=",", skiprows=1).T
        mode_ax.plot(x, np.abs(re_phi + 1j * im_phi), color=color, marker="o", markersize=2.5)
        overlap_ax.semilogy(t, np.maximum(1 - overlap, 1e-12), color=color)

    energy_ax.set(title="Total perturbation energy", ylabel=r"$\ln W$", xlabel="Normalized time")
    omega_ax.set(title="Late potential phase slope · dotted lines show GENE outputs",
                 ylabel=r"Normalized frequency $\omega$", xlabel="Normalized time")
    mode_ax.set(title="Final potential envelope", ylabel=r"$|\phi|/\max|\phi|$",
                xlabel="Fraction along traced field line")
    overlap_ax.set(title="Change in complex shape relative to final snapshot",
                   ylabel="1 − normalized overlap", xlabel="Normalized time")
    energy_ax.legend(frameon=False)
    for ax in axes.flat:
        ax.grid(alpha=0.22)
    figure.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(figure, dpi=175)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", nargs=2, type=Path, metavar=("NZ32_DIR", "NZ64_DIR"),
                        help="Regenerate the archived tables from the two complete GENE run directories.")
    parser.add_argument("--data", type=Path, default=DATA, help="Input or output data directory.")
    parser.add_argument("--figure", type=Path, default=FIGURE, help="Where to write the figure.")
    args = parser.parse_args()
    if args.runs:
        extract(args.runs, args.data)
    draw(args.data, args.figure)


if __name__ == "__main__":
    main()
