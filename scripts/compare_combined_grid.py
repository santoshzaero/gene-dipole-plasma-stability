#!/usr/bin/env python3
"""Recompute the deuterium combined-grid and extent study from completed runs."""
import argparse
import csv
import hashlib
from pathlib import Path

import numpy as np

from compare_parallel_followup import archive, compare
from compare_parallel_resolution import read_case, write_series

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
CONFIGS = ROOT / "configs/convergence"
RUNS = (
    ("original", 32, 48, 32, ROOT / "benchmarks/parameters", "Original 32 × 48 × 32"),
    ("z64", 64, 48, 32, CONFIGS / "deuterium_nz64/parameters", "Finer 64 × 48 × 32"),
    ("w32", 24, 48, 32, CONFIGS / "deuterium_nz24_auto/parameters", "24 × 48 × 32"),
    ("v64", 24, 64, 32, CONFIGS / "deuterium_nz24_nv64_auto/parameters", "Finer 24 × 64 × 32"),
    ("w48", 24, 48, 48, CONFIGS / "deuterium_nz24_nw48_auto/parameters", "Finer 24 × 48 × 48"),
    ("reduced", 24, 48, 24, CONFIGS / "deuterium_nz24_nw24_auto/parameters", "Reduced 24 × 48 × 24"),
    ("extent", 24, 48, 24, CONFIGS / "deuterium_nz24_nv48_nw24_lw1625_auto/parameters", "Wider magnetic-moment domain"),
)


FIXED_DT = b"0.00057848"
FIXED_RUN = (
    "extent_fixed", 24, 48, 24,
    CONFIGS / "deuterium_nz24_nv48_nw24_lw1625_fixed_dt/parameters",
    "Wider magnetic-moment domain, fixed timestep",
)


def extract(paths, dest):
    reduced = RUNS[-2][4].read_bytes()
    expected = reduced.replace(b"lw    =   12.2500", b"lw    =   16.2500")
    if expected == reduced or expected != RUNS[-1][4].read_bytes():
        raise ValueError("Extent input must change only lw")
    cases = {}
    for directory, (label, nz, nv, nw, config, _) in zip(paths, RUNS + (FIXED_RUN,)):
        contents = config.read_bytes()
        if (directory / "parameters").read_bytes() != contents:
            raise ValueError(f"Unexpected input in {label}")
        case = read_case(directory, nz, nv=nv, nw=nw)
        if label == "extent_fixed":
            controlled = expected.replace(
                b"calc_dt = T",
                b"calc_dt = F\ndt_vlasov = " + FIXED_DT + b"\nev_coll = 9300.0",
            )
            if controlled != contents or not np.isclose(case[0]["dt"], float(FIXED_DT), rtol=1e-8, atol=0):
                raise ValueError("Fixed-step run must match the extent input apart from timestep controls")
        log = (directory / "run.log").read_text()
        case[0].update(
            input_sha256=hashlib.sha256(contents).hexdigest(),
            rescalings=log.count("rescaled amplitudes"),
            controlled_stop="Exit due to GENE.stop file." in log,
            lw=16.25 if label.startswith("extent") else 12.25,
        )
        cases[label] = case
    metadata = {(case[0]["release"], case[0]["source_revision"]) for case in cases.values()}
    if len(metadata) != 1:
        raise ValueError("The runs report different GENE versions")

    grid_labels = [spec[0] for spec in RUNS[:-1]]
    common_end = min(cases[label][0]["final_time"] for label in grid_labels)
    if not all(cases[label][0]["gene_converged"] for label in grid_labels):
        raise ValueError("Common grid comparison requires converged grid cases")
    comparisons = [
        compare(f"reduced_vs_{ref}", "reduced", ref, cases, common_end=common_end)
        for ref in grid_labels[:-1]
    ]
    energy_labels = ["reduced", "extent"]
    if "extent_fixed" in cases:
        energy_labels.append("extent_fixed")
    for label in energy_labels[1:]:
        if cases[label][0]["gene_converged"] and cases[label][0]["rescalings"] == 0:
            comparisons.append(compare(f"{label}_vs_reduced", label, "reduced", cases))
    archive(cases, comparisons, paths, dest)
    for label in energy_labels:
        write_series(dest / f"{label}_energy.csv.gz", cases[label][3], "time,total_energy")


def draw(dest, figure):
    names = {run[0]: run[-1] for run in RUNS}
    with (dest / "runs.csv").open() as stream:
        runs = {row["case"]: row for row in csv.DictReader(stream)}
    with (dest / "comparison.csv").open() as stream:
        comparisons = [row for row in csv.DictReader(stream) if row["case"] == "reduced"]

    fig, (error_ax, time_ax, energy_ax) = plt.subplots(1, 3, figsize=(15, 4.6), layout="constrained")
    positions = np.arange(len(comparisons))
    for quantity, label, marker, color in (
        ("field_gamma", "Growth fit", "o", "#176d81"),
        ("phase_omega", "Frequency fit", "s", "#b34d2a"),
    ):
        errors = [100 * float(row[f"{quantity}_relative_difference"]) for row in comparisons]
        error_ax.scatter(errors, positions, label=label, marker=marker, color=color)
    error_ax.axvline(1, linestyle=":", color="#444444")
    error_ax.set(yticks=positions, yticklabels=[names[row["reference"]] for row in comparisons],
                 xlabel="Difference from comparison grid (%)", title="Reduced-grid rate differences", xlim=(0, 1.1))
    error_ax.invert_yaxis()
    error_ax.legend(frameon=False, loc="lower right")

    grid_labels = [row[0] for row in RUNS[:-1]]
    y = np.arange(len(grid_labels))
    time_ax.barh(y, [float(runs[key]["wallclock_s"]) for key in grid_labels],
                 color=["#919aa0"] * (len(y) - 1) + ["#176d81"])
    time_ax.set(yticks=y, yticklabels=[names[key] for key in grid_labels],
                xlabel="GENE wall time (s)", title="Converged grid timings")
    time_ax.invert_yaxis()

    for key, text, color in (
        ("reduced", "12.25 · automatic", "#176d81"),
        ("extent", "16.25 · automatic", "#b34d2a"),
        ("extent_fixed", "16.25 · fixed step", "#0e7646"),
    ):
        if key not in runs:
            continue
        time, energy = np.loadtxt(dest / f"{key}_energy.csv.gz", delimiter=",", skiprows=1).T
        energy_ax.semilogy(time, energy, label=text, color=color, linestyle="--" if key == "extent_fixed" else "-")
    energy_ax.set(xlabel="Normalized time", ylabel="Total perturbation energy", title="Magnetic-moment domain (lw)")
    energy_ax.legend(frameon=False)
    for axis in (error_ax, time_ax, energy_ax):
        axis.grid(alpha=0.2)
    fig.suptitle("GENE deuterium reference · grid, runtime, and domain checks", fontweight="bold")
    figure.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(figure, dpi=175)
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", nargs="+", type=Path, metavar="DIR",
                        help="Completed directories in the order given in the study.")
    parser.add_argument("--data", type=Path, default=ROOT / "results/convergence/deuterium_combined")
    parser.add_argument("--figure", type=Path, default=ROOT / "figures/convergence/deuterium_combined.png")
    args = parser.parse_args()
    if args.runs:
        if len(args.runs) not in (len(RUNS), len(RUNS) + 1):
            parser.error("--runs requires seven or eight directories.")
        extract(args.runs, args.data)
    draw(args.data, args.figure)
