#!/usr/bin/env python3
"""Compare deuterium magnetic-moment controls at one fixed timestep."""
import argparse
import csv
import hashlib
import re
from pathlib import Path

import numpy as np

from compare_parallel_followup import archive, compare, draw
from compare_parallel_resolution import read_case, write_series
from compare_parallel_velocity import draw_energy

ROOT = Path(__file__).resolve().parents[1]
CONFIGS = ROOT / "configs/convergence"
SPECS = (
    ("nominal", 24, 12.25, "deuterium_nz24_nv48_nw24_lw1225_fixed_dt"),
    ("wide24", 24, 16.25, "deuterium_nz24_nv48_nw24_lw1625_fixed_dt"),
    ("wide32", 32, 16.25, "deuterium_nz24_nv48_nw32_lw1625_fixed_dt"),
)
LABELS = {"nominal": "lw 12.25 · 24 points", "wide24": "lw 16.25 · 24 points",
          "wide32": "lw 16.25 · 32 points"}
DT = 0.00057848


def load_cases(paths):
    nominal = (CONFIGS / SPECS[0][3] / "parameters").read_bytes()
    wide = nominal.replace(b"lw    =   12.2500", b"lw    =   16.2500")
    spacing, edits = re.subn(rb"(?m)^(nw0[ \t]*=[ \t]*)24$", rb"\g<1>32", wide)
    if wide == nominal or edits != 1:
        raise ValueError("Unable to construct the domain and spacing input controls")

    cases = {}
    for directory, (name, nw, lw, config), expected in zip(paths, SPECS, (nominal, wide, spacing)):
        if expected != (CONFIGS / config / "parameters").read_bytes():
            raise ValueError(f"Unexpected settings in published input {name}")
        if expected != (directory / "parameters").read_bytes():
            raise ValueError(f"Unexpected settings in recorded input {name}")
        case = read_case(directory, 24, nw=nw)
        stats = case[0]
        if not np.isclose(stats["dt"], DT, rtol=1e-8, atol=0):
            raise ValueError(f"Applied timestep does not match {DT}: {name}")
        log = (directory / "run.log").read_text()
        stats.update(lw=lw, input_sha256=hashlib.sha256(expected).hexdigest(),
                     rescalings=log.count("rescaled amplitudes"),
                     controlled_stop="Exit due to GENE.stop file." in log)
        cases[name] = case
    if len({(c[0]["release"], c[0]["source_revision"]) for c in cases.values()}) != 1:
        raise ValueError("Controls report different GENE versions")
    return cases


def compare_controls(cases):
    usable = {label for label, (stats, *_) in cases.items()
              if stats["gene_converged"] and stats["rescalings"] == 0}
    end = min((cases[label][0]["final_time"] for label in usable), default=0.0)
    pairs = [("domain", "wide24", "nominal")]
    if "wide32" in cases:
        pairs += [("spacing", "wide32", "wide24"), ("wide_refined_vs_nominal", "wide32", "nominal")]
    for label, test, ref in pairs:
        if {test, ref} <= usable:
            yield compare(label, test, ref, cases, common_end=end)
        else:
            yield {"comparison": label, "case": test, "reference": ref,
                   "both_gene_converged": False, "passes_screen": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", nargs="+", type=Path, metavar="DIR",
                        help="Nominal fixed, wide fixed at 24 points, and optionally wide fixed at 32 points.")
    parser.add_argument("--gate", action="store_true",
                        help="Exit successfully only if the two-run frequency difference reaches 1%.")
    parser.add_argument("--data", type=Path, default=ROOT / "results/convergence/deuterium_moment_controls")
    parser.add_argument("--figure", type=Path, default=ROOT / "figures/convergence/deuterium_moment_controls.png")
    parser.add_argument("--energy-figure", type=Path,
                        default=ROOT / "figures/convergence/deuterium_moment_controls_energy.png")
    args = parser.parse_args()
    if args.runs:
        if len(args.runs) not in ((2,) if args.gate else (2, 3)):
            parser.error("Supply two run directories for the gate, or two or three for analysis.")
        cases = load_cases(args.runs)
        comparisons = list(compare_controls(cases))
        if args.gate:
            comparison = comparisons[0]
            print(comparison)
            delta = comparison.get("phase_omega_relative_difference")
            raise SystemExit(0 if delta is not None and delta >= 0.01 else 1)
        # Use a consistent schema even if one comparison involves a stopped run.
        columns = dict.fromkeys(key for row in comparisons for key in row)
        archive(cases, [columns | row for row in comparisons], args.runs, args.data)
        for label, (_, _, _, energy) in cases.items():
            write_series(args.data / f"{label}_energy.csv.gz", energy, "time,total_energy")
    elif args.gate:
        parser.error("--gate requires run directories")
    with (args.data / "runs.csv").open() as stream:
        has_mode = any(row["gene_converged"] == "True" for row in csv.DictReader(stream))
    if has_mode:
        draw(args.data, args.figure, labels=LABELS, converged_only=True,
             title="GENE deuterium reference · fixed-timestep moment controls")
    draw_energy(args.data, args.energy_figure, labels=LABELS,
                title="GENE deuterium reference · fixed-timestep energy histories",
                colors=("#4c545b", "#b34d2a", "#1a7186"))


if __name__ == "__main__":
    main()
