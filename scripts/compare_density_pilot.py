#!/usr/bin/env python3
"""Archive and plot the three-point quasineutral deuterium density pilot."""
import argparse
import csv
import hashlib
import re
from pathlib import Path

from compare_parallel_followup import archive, compare
from compare_parallel_resolution import read_case

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
GRADIENTS = (1, 2, 3)
BASE = ROOT / "benchmarks/classmate/parameters_deuterium_iv"


def extract(history, work, reference, dest):
    economical = BASE.read_bytes()
    historical = (ROOT / "benchmarks/parameters").read_bytes()
    expected_grid = economical.replace(b"nz0    =   24", b"nz0    =   32").replace(
        b"nw0    =   24", b"nw0    =   32")
    if expected_grid != historical:
        raise ValueError("Historical input must differ from economical input only in nz0 and nw0")
    cases, directories = {}, []
    for family, nz, start in (("historical", 32, historical), ("economical", 24, economical)):
        for g in GRADIENTS:
            if family == "historical":
                path = history / f"omn_{g}_omt_2"
                tracked = ROOT / "configs/isotope/deuterium" / f"omn_{g}_omt_2" / "parameters"
            elif g == 2:
                path, tracked = reference, BASE
            else:
                path = work / f"omn_{g}"
                tracked = ROOT / "configs/deuterium_density_pilot" / f"omn_{g}" / "parameters"
            expected, count = re.subn(rb"(?m)^(omn[ \t]*=[ \t]*)2$",
                                      rb"\g<1>" + str(g).encode("ascii"), start)
            if count != 2 or expected != tracked.read_bytes() or expected != (path / "parameters").read_bytes():
                raise ValueError(f"Unexpected inputs for {family} omn={g}")
            case = read_case(path, nz, nw=nz)
            log = (path / "run.log").read_text()
            case[0].update(omn=g, omt=2, grid=family,
                           rescalings=log.count("rescaled amplitudes"),
                           controlled_stop="Exit due to GENE.stop file." in log,
                           input_sha256=hashlib.sha256(expected).hexdigest())
            cases[f"{family}_{g}"] = case
            directories.append(path)

    good = {label for label, (stats, *_) in cases.items()
            if stats["gene_converged"] and stats["rescalings"] == 0}
    pairs = []
    for g in GRADIENTS:
        test, ref = f"economical_{g}", f"historical_{g}"
        if {test, ref} <= good:
            row = compare(f"omn_{g}", test, ref, cases)
            row["omn"] = g
        else:
            row = dict(comparison=f"omn_{g}", case=test, reference=ref, omn=g,
                       both_gene_converged=False, passes_screen=False)
        pairs.append(row)
    columns = dict.fromkeys(key for row in pairs for key in row)
    archive(cases, [columns | row for row in pairs], directories, dest)


def draw(data, figures):
    figures.mkdir(parents=True, exist_ok=True)
    with (data / "runs.csv").open() as stream:
        rows = list(csv.DictReader(stream))
    for quantity, ylabel, filename in (
        ("gamma", "Normalized growth rate", "deuterium_density_growth.png"),
        ("omega", "Signed normalized real frequency", "deuterium_density_frequency.png"),
    ):
        fig, ax = plt.subplots(figsize=(7, 4.4), layout="constrained")
        for grid, label, color, marker in (
            ("historical", "32 × 48 × 32 · archived", "#a44e31", "s"),
            ("economical", "24 × 48 × 24 · exploratory", "#176d81", "o"),
        ):
            subset = [row for row in rows if row["grid"] == grid]
            values = [float(row[quantity]) if row["gene_converged"] == "True" and row["rescalings"] == "0"
                      else np.nan for row in subset]
            ax.plot([float(row["omn"]) for row in subset], values, label=label,
                    color=color, marker=marker, linestyle="--" if grid == "historical" else "-",
                    markerfacecolor="white", linewidth=1.8)
        ax.set(title="GENE deuterium density-gradient pilot · IV",
               xlabel="Common density gradient (omn)", ylabel=ylabel, xticks=GRADIENTS)
        ax.grid(alpha=0.23)
        ax.legend(frameon=False, loc="upper left")
        fig.savefig(figures / filename, dpi=175)
        plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", nargs=3, type=Path, metavar=("HISTORICAL", "PILOT", "REFERENCE"))
    parser.add_argument("--data", type=Path, default=ROOT / "results/deuterium_density_pilot")
    parser.add_argument("--figures", type=Path, default=ROOT / "figures/deuterium_density_pilot")
    args = parser.parse_args()
    if args.runs:
        extract(*args.runs, args.data)
    draw(args.data, args.figures)
