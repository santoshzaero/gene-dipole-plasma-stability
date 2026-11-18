#!/usr/bin/env python3
"""Analyze the deuterium nv0 = 48/64 comparison without launching GENE."""
import argparse
import hashlib
import re
from pathlib import Path

from compare_parallel_followup import archive, compare, draw
from compare_parallel_resolution import read_case

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "configs/convergence/deuterium_nz24_auto/parameters"
INPUT_64 = ROOT / "configs/convergence/deuterium_nz24_nv64_auto/parameters"
LABELS = {"nv48": "48 parallel-velocity points", "nv64": "64 parallel-velocity points"}


def extract(paths, dest):
    baseline = BASELINE.read_bytes()
    refined, count = re.subn(rb"(?m)^(nv0[ \t]*=[ \t]*)48$", rb"\g<1>64", baseline)
    if count != 1 or refined != INPUT_64.read_bytes():
        raise ValueError("Archived inputs must differ only in nv0")
    cases = {}
    for directory, nv, expected in zip(paths, (48, 64), (baseline, refined)):
        if (directory / "parameters").read_bytes() != expected:
            raise ValueError(f"Input differs from archived nv0 = {nv} case")
        case = read_case(directory, 24, nv=nv)
        case[0]["input_sha256"] = hashlib.sha256(expected).hexdigest()
        cases[f"nv{nv}"] = case
    metadata = {(case[0]["release"], case[0]["source_revision"]) for case in cases.values()}
    if len(metadata) != 1:
        raise ValueError("The two runs report different GENE versions")
    comparison = compare("parallel_velocity_48_64", "nv48", "nv64", cases)
    archive(cases, [comparison], paths, dest)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", nargs=2, type=Path, metavar=("NV48_DIR", "NV64_DIR"),
                        help="Recompute the tables from the completed baseline and refined run.")
    parser.add_argument("--data", type=Path, default=ROOT / "results/convergence/deuterium_nv48_nv64")
    parser.add_argument("--figure", type=Path, default=ROOT / "figures/convergence/deuterium_nv48_nv64.png")
    args = parser.parse_args()
    if args.runs:
        extract(args.runs, args.data)
    draw(args.data, args.figure, labels=LABELS,
         title="GENE deuterium reference · parallel-velocity resolution")


if __name__ == "__main__":
    main()
