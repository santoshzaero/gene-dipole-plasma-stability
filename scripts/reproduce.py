#!/usr/bin/env python3
"""Audit and plot archived outputs. This program never invokes GENE."""
import argparse
import csv
import gzip
import hashlib
import re
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
VALUES = [0, 0.5, 1, 2, 3, 4, 5]
ISOTOPES = ("hydrogen", "deuterium")


def read_csv(path):
    with (ROOT / path).open(newline="") as stream:
        return list(csv.DictReader(stream))


def folder(omn, omt):
    return f"omn_{float(omn):g}_omt_{float(omt):g}".replace(".", "p")


def gradient_key(row):
    return float(row["omn"]), float(row["omt"])


def is_converged(row):
    return row["status"] == "CONVERGED"


def is_anomalous(row):
    return row["isotope"] == "deuterium" and float(row["kymin"]) == 0.3


def audit_omega(row, diagnostic):
    assert is_converged(row) == (diagnostic["log_converged"] == "True")
    for key in ("gamma", "omega"):
        if row[key]:
            assert float(row[key]) == float(diagnostic[f"omega_file_{key}"]), row


def fit_energy(row):
    case = folder(*gradient_key(row))
    path = ROOT / "results/isotope/energy_histories" / row["isotope"] / case / "time_energy.tsv.gz"
    with gzip.open(path, "rt") as stream:
        data = np.loadtxt(stream, skiprows=1)
    data = data[np.isfinite(data).all(axis=1) & (data[:, 1] > 0)]
    assert len(data) >= 100 and np.all(np.diff(data[:, 0]) >= 0), path
    fits = []
    for percent in (50, 30, 15):
        time, energy = data[int(len(data) * (1 - percent / 100)):].T
        log_energy = np.log(energy)
        slope, intercept = np.polyfit(time, log_energy, 1)
        residual = log_energy - (slope * time + intercept)
        r2 = 1 - np.sum(residual**2) / np.sum((log_energy - log_energy.mean())**2)
        gamma = slope / 2
        assert np.isclose(gamma, float(row[f"gamma_last{percent}"]), atol=1e-8)
        assert np.isclose(r2, float(row[f"r2_last{percent}"]), atol=1e-8)
        fits.append((gamma, r2))
    (g50, _), (g30, r30), (g15, r15) = fits
    consistent = min(r15, r30) > 0.99 and max(abs(g50 - g15), abs(g30 - g15)) < max(0.05, 0.1 * abs(g15))
    assert consistent == (row["fit_status"] == "CONSISTENT")
    override = row["isotope"] == "deuterium" and gradient_key(row) == (0, 0)
    return round(g15, 8), "qualified" if consistent or override else "uncertain"


def audit():
    for row in read_csv("results/provenance.csv"):
        path = ROOT / row["repository_path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"], path
    index = {(row["study"], row["case"]): row for row in read_csv("results/run_index.csv")}
    assert Counter(study for study, _ in index) == {
        "pair_density": 7, "pair": 49, "pair_extended": 5, "isotope": 98, "ky": 16
    }
    grid = {(omn, omt) for omn in VALUES for omt in VALUES}
    pair = read_csv("results/pair/gradient_scan.csv")
    assert len(pair) == 49 and {gradient_key(row) for row in pair} == grid
    assert Counter(row["status"] for row in pair) == {"CONVERGED": 44, "CHECK": 5}
    for row in pair:
        audit_omega(row, index["pair", folder(*gradient_key(row))])
    for row in read_csv("results/pair/density_scan.csv"):
        audit_omega({**row, "status": "CONVERGED"}, index["pair_density", f"omn_{float(row['omn']):g}".replace(".", "p")])
    assert all(row["log_converged"] == "False" for (study, _), row in index.items() if study == "pair_extended")

    rates = {}
    for isotope in ISOTOPES:
        data = read_csv(f"results/isotope/{isotope}.csv")
        assert len(data) == 49 and {gradient_key(row) for row in data} == grid
        for row in data:
            key = gradient_key(row)
            audit_omega(row, index["isotope", f"{isotope}/{folder(*key)}"])
            if is_converged(row):
                rates[isotope, *key] = (float(row["gamma"]), "gene")
    differences = [
        rates["hydrogen", *key][0] - rates["deuterium", *key][0] for key in grid
        if all((isotope, *key) in rates for isotope in ISOTOPES)
    ]
    assert len(differences) == 41 and min(differences) > 0
    for row in read_csv("results/isotope/energy_fit_original.csv"):
        key = (row["isotope"], *gradient_key(row))
        assert key not in rates
        rates[key] = fit_energy(row)
    assert Counter(kind for _, kind in rates.values()) == {"gene": 85, "qualified": 6, "uncertain": 7}
    for row in read_csv("results/isotope/growth_rates_with_quality_original.csv"):
        assert rates[row["isotope"], *gradient_key(row)] == (float(row["gamma"]), row["classification"])

    ky = read_csv("results/ky/original.csv")
    assert len(ky) == 16 and sum(is_converged(row) for row in ky) == 11
    for row in ky:
        case = f"ky_{float(row['kymin']):g}".replace(".", "p")
        audit_omega(row, index["ky", f"{row['isotope']}/{case}"])
    anomaly, = [row for row in ky if is_anomalous(row)]
    assert (float(anomaly["gamma"]), float(anomaly["omega"])) == (378.519, 220.647)
    for clean_path, archive_path in (
        ("benchmarks/parameters", "configs/isotope/deuterium/omn_2_omt_2/parameters"),
        ("benchmarks/classmate/parameters_deuterium_iv", "configs/convergence/deuterium_nz24_nw24_auto/parameters"),
    ):
        clean = (ROOT / clean_path).read_bytes()
        original = (ROOT / archive_path).read_bytes()
        expected = re.sub(rb"(?m)^(?:which_ev|ev_max_it|ev_n_test)[ \t]*=[^\n]*\n(?:\n(?=timelim))?", b"", original)
        assert clean == expected, clean_path
        assert re.findall(rb"(?m)^comp_type\s*=\s*'([^']+)'", clean) == [b"IV"], clean_path
    print("Verified 175 run records, 13 refits, archive hashes, and benchmark identity.")
    print(f"Paired H−D growth rates are positive in all 41 GENE-converged pairs ({min(differences):.3f} to {max(differences):.3f}).")
    return pair, rates, ky


def plot_heatmap(output, matrix, title, lower, upper, cmap_name):
    fig, ax = plt.subplots(figsize=(7.6, 6.1), layout="constrained")
    cmap = plt.get_cmap(cmap_name).with_extremes(bad="#e2e5e7")
    heat = ax.imshow(matrix, origin="lower", cmap=cmap, vmin=lower, vmax=upper)
    ax.set(xticks=range(7), xticklabels=VALUES, yticks=range(7), yticklabels=VALUES,
           xlabel="Normalized density gradient (omn)", ylabel="Normalized temperature gradient (omt)",
           title=title)
    for j, row in enumerate(matrix):
        for i, value in enumerate(row):
            rgb = cmap(heat.norm(value))[:3]
            color = "black" if np.dot(rgb, [0.213, 0.715, 0.072]) > 0.55 or np.isnan(value) else "white"
            label = f"{value:.2f}" if np.isfinite(value) else "—"
            ax.text(i, j, label, ha="center", va="center", color=color, fontsize=9)
    fig.colorbar(heat, ax=ax, label="Normalized growth rate")
    fig.savefig(output, dpi=180)
    plt.close(fig)


def plot_ky(output, rows, quantity, ylabel):
    fig, ax = plt.subplots(figsize=(7.8, 4.8), layout="constrained")
    for isotope, color, marker in zip(ISOTOPES, ("#197278", "#a44727"), ("o", "s")):
        subset = [row for row in rows if row["isotope"] == isotope]
        values = [float(row[quantity]) if is_converged(row) and not is_anomalous(row) else np.nan
                  for row in subset]
        ax.plot([float(row["kymin"]) for row in subset], values,
                label=isotope.capitalize(), marker=marker, color=color, linewidth=2)
    ax.axvspan(0.09, 0.32, color="#e3e7eb", label="Low-$k_y$ region under review")
    ax.set(xlabel=r"Normalized binormal wavenumber $k_y\rho_{\rm ref}$",
           ylabel=ylabel, title="GENE dipole scan · equal gradients of 2", xlim=(0.08, 2.05))
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False)
    fig.savefig(output, dpi=180)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="Write regenerated figures to this directory.")
    args = parser.parse_args()
    pair, rates, ky = audit()
    if args.out is None:
        return
    args.out.mkdir(parents=True, exist_ok=True)
    pair_rates = {gradient_key(row): float(row["gamma"]) for row in pair if is_converged(row)}
    pair_matrix = np.array([[pair_rates.get((omn, omt), np.nan) for omn in VALUES] for omt in VALUES])
    plot_heatmap(args.out / "pair_gene_only.png", pair_matrix, "GENE electron–positron gradient scan",
                 0, np.nanmax(pair_matrix), "viridis")
    delta = np.full((7, 7), np.nan)
    for j, omt in enumerate(VALUES):
        for i, omn in enumerate(VALUES):
            h, h_kind = rates["hydrogen", omn, omt]
            d, d_kind = rates["deuterium", omn, omt]
            if h_kind == d_kind == "gene":
                delta[j, i] = h - d
    plot_heatmap(args.out / "isotope_gene_only.png", delta, "GENE isotope difference · hydrogen minus deuterium",
                 0, np.nanmax(delta), "Blues")
    plot_ky(args.out / "ky_growth.png", ky, "gamma", "Normalized growth rate")
    plot_ky(args.out / "ky_frequency.png", ky, "omega", "Normalized real frequency")


if __name__ == "__main__":
    main()
