from pathlib import Path
import csv
import re
import subprocess
import os

ROOT = Path.home() / "Developer/gene-complete"
BASE = ROOT / "runs/pair_plasma_IV"
SCAN = ROOT / "runs/density_scan"
EXECUTABLE = ROOT / "bin/gene_mac_arm64"

GRADIENTS = [0, 0.5, 1, 2, 3, 4, 5]

SCAN.mkdir(parents=True, exist_ok=True)
original = (BASE / "parameters").read_text()

# Require exactly two species, each with one omn parameter.
species = re.findall(
    r"(?ims)^&species\b.*?^/\s*$", original
)
assert len(species) == 2, "Expected exactly two species blocks"

def make_parameters(gradient):
    def change_species(match):
        block = match.group(0)
        block, count = re.subn(
            r"(?im)^(\s*omn\s*=\s*)[^\n!]+",
            lambda m: m.group(1) + str(gradient),
            block,
        )
        if count != 1:
            raise ValueError("Expected one omn per species")
        return block

    text, count = re.subn(
        r"(?ims)^&species\b.*?^/\s*$",
        change_species,
        original,
    )
    if count != 2:
        raise ValueError("Species replacement failed")

    # Disable large velocity-space diagnostics.
    text, count = re.subn(
        r"(?im)^(\s*istep_vsp\s*=\s*)[^\n!]+",
        lambda m: m.group(1) + "0",
        text,
    )
    if count != 1:
        raise ValueError("Could not configure istep_vsp")
    return text

results = []

for gradient in GRADIENTS:
    label = f"omn_{gradient:g}".replace(".", "p")
    folder = SCAN / label
    folder.mkdir(exist_ok=True)
    (folder / "out").mkdir(exist_ok=True)

    parameters = make_parameters(gradient)
    (folder / "parameters").write_text(parameters)

    print(f"\nRunning omn = {gradient:g}", flush=True)

    env = os.environ.copy()
    env["MACHINE"] = "mac_arm64"
    env["OMP_NUM_THREADS"] = "1"

    with (folder / "run.log").open("w") as log:
        run = subprocess.run(
            [str(EXECUTABLE)],
            cwd=folder,
            stdout=log,
            stderr=subprocess.STDOUT,
            env=env,
        )

    omega_file = folder / "out/omega.dat"
    gamma = omega = None
    status = "FAILED"

    if omega_file.exists():
        lines = [
            line.strip()
            for line in omega_file.read_text().splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        if lines:
            try:
                values = lines[-1].split()
                gamma = float(values[1].replace("D", "E"))
                omega = float(values[2].replace("D", "E"))
                status = "OK" if run.returncode == 0 else "CHECK_LOG"
            except (ValueError, IndexError):
                status = "BAD_DIAGNOSTIC"

    results.append([gradient, gamma, omega, status])

    print(
        f"omn={gradient:g}, gamma={gamma}, "
        f"omega={omega}, status={status}",
        flush=True,
    )

csv_path = SCAN / "density_scan_results.csv"
with csv_path.open("w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["omn", "gamma", "omega", "status"])
    writer.writerows(results)

print(f"\nResults saved to {csv_path}")

try:
    import matplotlib.pyplot as plt

    valid = [
        r for r in results
        if r[3] == "OK" and r[1] is not None
    ]

    if valid:
        x = [r[0] for r in valid]

        for column, ylabel, filename in [
            (1, "Growth rate (normalized)", "gamma_vs_omn.png"),
            (2, "Real frequency (normalized)", "omega_vs_omn.png"),
        ]:
            plt.figure(figsize=(7, 4.5))
            plt.plot(x, [r[column] for r in valid], "o-")
            plt.xlabel("Density gradient (omn)")
            plt.ylabel(ylabel)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(SCAN / filename, dpi=180)
            plt.close()

        print("Plots generated successfully.")
except ImportError:
    print("Matplotlib unavailable; CSV was still generated.")
