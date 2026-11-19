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
INPUTS = {
    32: CONFIGS / "deuterium_nz24_auto/parameters",
    48: CONFIGS / "deuterium_nz24_nw48_auto/parameters",
    24: CONFIGS / "deuterium_nz24_nw24_auto/parameters",
}
LABELS = {f"nw{nw}": f"{nw} magnetic-moment points" for nw in INPUTS}


def extract(paths, dest):
    baseline = INPUTS[32].read_bytes()
    cases = {}
    for directory, nw in zip(paths, INPUTS):
        expected, count = re.subn(rb"(?m)^(nw0[ \t]*=[ \t]*)32$",
                                  rb"\g<1>" + str(nw).encode("ascii"), baseline)
        if count != 1 or expected != INPUTS[nw].read_bytes():
            raise ValueError(f"Archived nw0 = {nw} input changes other settings")
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
    pairs = [("nw32", "nw48")]
    if "nw24" in cases:
        pairs.extend([("nw24", "nw32"), ("nw24", "nw48")])
    comparisons = []
    for test, reference in pairs:
        name = f"magnetic_moment_{test[2:]}_{reference[2:]}"
        stats = [cases[label][0] for label in (test, reference)]
        both_converged = all(run["gene_converged"] for run in stats)
        if both_converged:
            comparison = compare(name, test, reference, cases)
            comparison["passes_screen"] &= all(run["rescalings"] == 0 for run in stats)
        else:
            comparison = {"comparison": name, "case": test, "reference": reference,
                          "both_gene_converged": False, "passes_screen": False}
        comparisons.append(comparison)
    archive(cases, comparisons, paths, dest)
    for label, (_, _, _, energy) in cases.items():
        write_series(dest / f"{label}_energy.csv.gz", energy, "time,total_energy")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", nargs="+", type=Path, metavar="DIR",
                        help="Run directories for nw0 = 32, 48, and optionally 24, in that order.")
    parser.add_argument("--data", type=Path, default=ROOT / "results/convergence/deuterium_nw32_nw48")
    parser.add_argument("--figure", type=Path, default=ROOT / "figures/convergence/deuterium_nw32_nw48.png")
    parser.add_argument("--energy-figure", type=Path,
                        default=ROOT / "figures/convergence/deuterium_nw32_nw48_energy.png")
    args = parser.parse_args()
    if args.runs:
        if len(args.runs) not in (2, 3):
            parser.error("--runs takes two or three run directories.")
        extract(args.runs, args.data)
    draw(args.data, args.figure, labels=LABELS, converged_only=True,
         title="GENE deuterium reference · magnetic-moment resolution")
    draw_energy(args.data, args.energy_figure, labels=LABELS,
                title="GENE deuterium reference · magnetic-moment energy histories",
                colors=("#4c545b", "#b34d2a", "#1a7186"))


if __name__ == "__main__":
    main()
