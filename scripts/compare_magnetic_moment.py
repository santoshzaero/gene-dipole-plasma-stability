#!/usr/bin/env python3
"""Analyze the deuterium magnetic-moment grid comparison without running GENE."""
import argparse
import hashlib
import re
from pathlib import Path

from compare_parallel_followup import archive, compare, draw
from compare_parallel_resolution import read_case, write_series
from compare_parallel_velocity import draw_energy

ROOT = Path(__file__).resolve().parents[1]
CONFIGS = ROOT / "configs/convergence"
LABELS = {"nw32": "32 magnetic-moment points", "nw48": "48 magnetic-moment points"}


def extract(paths, dest):
    baseline = (CONFIGS / "deuterium_nz24_auto/parameters").read_bytes()
    refined, count = re.subn(rb"(?m)^(nw0[ \t]*=[ \t]*)32$", rb"\g<1>48", baseline)
    if count != 1 or refined != (CONFIGS / "deuterium_nz24_nw48_auto/parameters").read_bytes():
        raise ValueError("Published inputs must differ only in nw0")
    cases = {}
    for directory, nw, expected in zip(paths, (32, 48), (baseline, refined)):
        if (directory / "parameters").read_bytes() != expected:
            raise ValueError(f"Run input differs from the archived nw0 = {nw} input")
        case = read_case(directory, 24, nw=nw)
        log = (directory / "run.log").read_text()
        case[0]["input_sha256"] = hashlib.sha256(expected).hexdigest()
        case[0]["rescalings"] = log.count("rescaled amplitudes")
        case[0]["controlled_stop"] = "Exit due to GENE.stop file." in log
        cases[f"nw{nw}"] = case
    metadata = {(case[0]["release"], case[0]["source_revision"]) for case in cases.values()}
    if len(metadata) != 1:
        raise ValueError("The runs report different GENE versions")
    both_converged = all(stats["gene_converged"] for stats, *_ in cases.values())
    if both_converged:
        comparison = compare("magnetic_moment_32_48", "nw32", "nw48", cases)
        comparison["passes_screen"] &= all(stats["rescalings"] == 0 for stats, *_ in cases.values())
    else:
        comparison = {"comparison": "magnetic_moment_32_48", "case": "nw32", "reference": "nw48",
                      "both_gene_converged": False, "passes_screen": False}
    archive(cases, [comparison], paths, dest)
    for label, (_, _, _, energy) in cases.items():
        write_series(dest / f"{label}_energy.csv.gz", energy, "time,total_energy")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", nargs=2, type=Path, metavar=("NW32_DIR", "NW48_DIR"))
    parser.add_argument("--data", type=Path, default=ROOT / "results/convergence/deuterium_nw32_nw48")
    parser.add_argument("--figure", type=Path, default=ROOT / "figures/convergence/deuterium_nw32_nw48.png")
    parser.add_argument("--energy-figure", type=Path,
                        default=ROOT / "figures/convergence/deuterium_nw32_nw48_energy.png")
    args = parser.parse_args()
    if args.runs:
        extract(args.runs, args.data)
    draw(args.data, args.figure, labels=LABELS, converged_only=True,
         title="GENE deuterium reference · magnetic-moment resolution")
    draw_energy(args.data, args.energy_figure, labels=LABELS,
                title="GENE deuterium reference · magnetic-moment energy histories",
                colors=("#4c545b", "#b34d2a"))


if __name__ == "__main__":
    main()
