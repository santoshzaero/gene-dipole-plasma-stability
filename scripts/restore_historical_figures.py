#!/usr/bin/env python3
"""Regenerate selected historical figures using disposable inputs and archived plotters."""
import argparse
import gzip
import os
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "scripts/archive"
DATA = ROOT / "results"


def restore_energy(source, dest):
    for trace in source.glob("**/time_energy.tsv.gz"):
        folder = dest / trace.parent.relative_to(source) / "out"
        folder.mkdir(parents=True, exist_ok=True)
        with gzip.open(trace, "rb") as payload, (folder / "energy.dat").open("wb") as energy:
            payload.readline()
            shutil.copyfileobj(payload, energy)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out", type=Path, help="Directory for regenerated historical PNGs.")
    args = parser.parse_args()
    with TemporaryDirectory(prefix="gene-history-") as home:
        project = Path(home) / "Developer/gene-complete"
        density = project / "runs/density_scan"
        gradient = project / "runs/gradient_scan_2d"
        isotope = project / "runs/isotope_scan"
        for folder in (density, gradient, isotope):
            folder.mkdir(parents=True)
        for source, dest in (
            ("pair/density_scan.csv", density / "density_scan_results.csv"),
            ("pair/gradient_scan.csv", gradient / "results.csv"),
            ("isotope/hydrogen.csv", isotope / "hydrogen_results.csv"),
            ("isotope/deuterium.csv", isotope / "deuterium_results.csv"),
            ("isotope/energy_fit_original.csv", isotope / "energy_fit_results.csv"),
        ):
            shutil.copyfile(DATA / source, dest)

        restore_energy(DATA / "isotope/energy_histories", isotope)
        restore_energy(DATA / "pair/energy_histories/original", gradient)

        # The historical scripts use both script-relative and working-directory paths.
        env = dict(os.environ, HOME=home, USERPROFILE=home, MPLBACKEND="Agg")
        for name in (
            "plot_density_scan", "plot_gradient_scan_2d", "plot_unresolved_energy",
            "create_final_isotope_heatmaps", "inspect_energy_fits",
        ):
            script = project / f"{name}.py"
            shutil.copyfile(ARCHIVE / script.name, script)
            subprocess.run([sys.executable, str(script)], cwd=project, env=env, check=True)
        args.out.mkdir(parents=True, exist_ok=True)
        for figure in sorted((project / "runs").glob("**/*.png")):
            shutil.copyfile(figure, args.out / figure.name)


if __name__ == "__main__":
    main()
