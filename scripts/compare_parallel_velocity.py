#!/usr/bin/env python3
"""Analyze the deuterium parallel-velocity grid comparisons without launching GENE."""
import argparse
import csv
import hashlib
import re
from pathlib import Path

from compare_parallel_followup import archive, compare, draw
from compare_parallel_resolution import read_case, write_series

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "configs/convergence/deuterium_nz24_auto/parameters"
CONTROL_STEP = 0.00057848
CASES = (
    ("nv48", 48, BASELINE),
    ("nv64", 64, ROOT / "configs/convergence/deuterium_nz24_nv64_auto/parameters"),
    ("nv32", 32, ROOT / "configs/convergence/deuterium_nz24_nv32_auto/parameters"),
    ("nv32_fixed", 32, ROOT / "configs/convergence/deuterium_nz24_nv32_fixed_dt/parameters"),
)
LABELS = {"nv48": "48 points · automatic", "nv64": "64 points · automatic",
          "nv32": "32 points · automatic", "nv32_fixed": "32 points · fixed timestep"}


def extract(paths, dest):
    baseline = BASELINE.read_bytes()
    cases = {}
    for directory, (label, nv, input_file) in zip(paths, CASES):
        expected, count = re.subn(rb"(?m)^(nv0[ \t]*=[ \t]*)48$",
                                  rb"\g<1>" + str(nv).encode("ascii"), baseline)
        if label == "nv32_fixed":
            expected = expected.replace(
                b"calc_dt = T", b"calc_dt = F\ndt_vlasov = 0.00057848\nev_coll = 9300.0"
            )
        if count != 1 or expected != input_file.read_bytes():
            raise ValueError(f"Archived {label} input changes other settings")
        if (directory / "parameters").read_bytes() != expected:
            raise ValueError(f"Input differs from archived {label} case")
        case = read_case(directory, 24, nv=nv)
        stats = case[0]
        if label == "nv32_fixed" and not np.isclose(stats["dt"], CONTROL_STEP, rtol=1e-8, atol=0):
            raise ValueError("Applied timestep differs from the fixed-step input")
        stats["input_sha256"] = hashlib.sha256(expected).hexdigest()
        log = (directory / "run.log").read_text()
        stats["rescalings"] = log.count("rescaled amplitudes")
        if stats["gene_converged"]:
            stats["termination"] = "GENE convergence"
        elif "Exit due to GENE.stop file." in log:
            stats["termination"] = "Controlled stop before convergence"
        else:
            stats["termination"] = "No GENE convergence flag"

        cases[label] = case
    metadata = {(case[0]["release"], case[0]["source_revision"]) for case in cases.values()}
    if len(metadata) != 1:
        raise ValueError("The runs report different GENE versions")
    comparisons = [compare("parallel_velocity_48_64", "nv48", "nv64", cases)]
    if "nv32" in cases and cases["nv32"][0]["gene_converged"]:
        comparisons.extend(
            compare(f"parallel_velocity_32_{ref[2:]}", "nv32", ref, cases)
            for ref in ("nv48", "nv64")
        )
    if "nv32_fixed" in cases and cases["nv32_fixed"][0]["gene_converged"]:
        comparisons.append(compare("parallel_velocity_32_fixed_48", "nv32_fixed", "nv48", cases))
    archive(cases, comparisons, paths, dest)
    for label, (_, _, _, energy) in cases.items():
        write_series(dest / f"{label}_energy.csv.gz", energy, "time,total_energy")


def draw_energy(dest, figure, *, labels=LABELS,
                title="GENE deuterium reference · velocity-grid energy histories",
                colors=("#4c545b", "#176d81", "#b34d2a", "#0e7646")):
    fig, ax = plt.subplots(figsize=(8.6, 4.4), layout="constrained")
    with (dest / "runs.csv").open() as stream:
        runs = list(csv.DictReader(stream))
    for run, color in zip(runs, colors):
        name = run["case"]
        time, energy = np.loadtxt(dest / f"{name}_energy.csv.gz", delimiter=",", skiprows=1).T
        valid = run["gene_converged"] == "True"
        suffix = "" if valid else " · stopped"
        ax.plot(time, energy, color=color, linestyle="-" if valid else "--",
                linewidth=1.7, label=labels[name] + suffix)
    ax.set(title=title,
           xlabel="Normalized time", ylabel="Total perturbation energy (code units)", yscale="log")
    ax.legend(frameon=False, loc="upper right")
    ax.grid(alpha=0.22)
    figure.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(figure, dpi=175)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", nargs="+", type=Path, metavar="DIR",
                        help="Run directories in order: 48 auto, 64 auto, 32 auto, 32 fixed. The final two are optional.")
    parser.add_argument("--data", type=Path, default=ROOT / "results/convergence/deuterium_nv48_nv64")
    parser.add_argument("--figure", type=Path, default=ROOT / "figures/convergence/deuterium_nv48_nv64.png")
    parser.add_argument("--energy-figure", type=Path,
                        default=ROOT / "figures/convergence/deuterium_nv32_auto_energy.png")
    args = parser.parse_args()
    if args.runs:
        if len(args.runs) not in (2, 3, 4):
            parser.error("--runs takes two to four recorded run directories.")
        extract(args.runs, args.data)
    draw(args.data, args.figure, labels=LABELS,
         title="GENE deuterium reference · parallel-velocity resolution", converged_only=True)
    if (args.data / "nv32_energy.csv.gz").exists():
        draw_energy(args.data, args.energy_figure)


if __name__ == "__main__":
    main()
