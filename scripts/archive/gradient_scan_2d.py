from pathlib import Path
import subprocess
import csv
import re
import os
import math

ROOT = Path.home() / "Developer/gene-complete"
BASE = ROOT / "runs/pair_plasma_IV/parameters_baseline"
SCAN = ROOT / "runs/gradient_scan_2d"
GENE = ROOT / "bin/gene_mac_arm64"

GRADIENTS = [0, 0.5, 1, 2, 3, 4, 5]
SCAN.mkdir(parents=True, exist_ok=True)

template = BASE.read_text()
species_pattern = r"(?ims)^&species\b.*?^/\s*$"

if len(re.findall(species_pattern, template)) != 2:
    raise RuntimeError("Expected exactly two species.")

def build_parameters(omn, omt):
    def replace_species(match):
        block = match.group(0)
        for key, value in [("omn", omn), ("omt", omt)]:
            pattern = rf"(?im)^(\s*{key}\s*=\s*)[^\n!]+"
            block, count = re.subn(
                pattern,
                lambda m: m.group(1) + str(value),
                block,
            )
            if count != 1:
                raise RuntimeError(f"Missing {key} in species block.")
        return block

    result = re.sub(species_pattern, replace_species, template)

    # Reduce diagnostic storage.
    result, count = re.subn(
        r"(?im)^(\s*istep_vsp\s*=\s*)[^\n!]+",
        lambda m: m.group(1) + "0",
        result,
    )
    if count != 1:
        raise RuntimeError("Missing istep_vsp setting.")

    return result

def label(value):
    return f"{value:g}".replace(".", "p")

def get_result(folder):
    omega_file = folder / "out/omega.dat"
    log_file = folder / "run.log"

    if not omega_file.exists() or not log_file.exists():
        return None

    log = log_file.read_text(errors="replace")
    converged = "Linear growth rate is converged" in log

    lines = [
        line.strip()
        for line in omega_file.read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if not lines:
        return None

    try:
        fields = lines[-1].split()
        gamma = float(fields[1].replace("D", "E"))
        omega = float(fields[2].replace("D", "E"))
    except (ValueError, IndexError):
        return None

    if not (math.isfinite(gamma) and math.isfinite(omega)):
        return None

    return gamma, omega, converged

results = []

env = os.environ.copy()
env["MACHINE"] = "mac_arm64"
env["OMP_NUM_THREADS"] = "1"

for omt in GRADIENTS:
    for omn in GRADIENTS:
        folder = SCAN / f"omn_{label(omn)}_omt_{label(omt)}"
        folder.mkdir(exist_ok=True)
        (folder / "out").mkdir(exist_ok=True)

        parameters = build_parameters(omn, omt)
        parameter_file = folder / "parameters"

        previous = (
            parameter_file.read_text()
            if parameter_file.exists() else None
        )

        # Never reuse diagnostics from different parameters.
        if previous != parameters:
            for old in (folder / "out/omega.dat", folder / "run.log"):
                old.unlink(missing_ok=True)
            parameter_file.write_text(parameters)

        result = get_result(folder) if previous == parameters else None

        if result is None:
            print(f"Running omn={omn:g}, omt={omt:g}", flush=True)

            # Remove old omega to prevent stale results.
            (folder / "out/omega.dat").unlink(missing_ok=True)

            with (folder / "run.log").open("w") as log:
                run = subprocess.run(
                    [str(GENE)],
                    cwd=folder,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    env=env,
                )

            result = get_result(folder)
            if run.returncode != 0:
                print(f"  GENE exit code: {run.returncode}")

        if result is None:
            gamma, omega, status = None, None, "FAILED"
        else:
            gamma, omega, converged = result
            status = "CONVERGED" if converged else "CHECK"

        results.append([omn, omt, gamma, omega, status])
        print(
            f"  omn={omn:g}, omt={omt:g}, "
            f"gamma={gamma}, omega={omega}, {status}",
            flush=True,
        )

        # Save incrementally in case the scan is interrupted.
        with (SCAN / "results.csv").open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["omn", "omt", "gamma", "omega", "status"])
            writer.writerows(results)

print("\nScan finished.")
print("Results:", SCAN / "results.csv")
