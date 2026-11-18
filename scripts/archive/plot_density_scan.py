import csv
from pathlib import Path
import matplotlib.pyplot as plt

folder = Path.home() / "Developer/gene-complete/runs/density_scan"

with (folder / "density_scan_results.csv").open() as f:
    data = list(csv.DictReader(f))

omn = [float(row["omn"]) for row in data]
gamma = [float(row["gamma"]) for row in data]
omega = [float(row["omega"]) for row in data]

for values, ylabel, filename in [
    (gamma, "Growth rate γ (normalized)", "gamma_vs_omn.png"),
    (omega, "Real frequency ω (normalized)", "omega_vs_omn.png"),
]:
    plt.figure(figsize=(8, 5))
    plt.plot(omn, values, "o-", linewidth=2, markersize=7)
    plt.axhline(0, linestyle="--", color="gray", linewidth=1)
    plt.xlabel("Normalized density gradient (omn)")
    plt.ylabel(ylabel)
    plt.title("Electron–positron plasma | Dipole geometry | ky = 0.7")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(folder / filename, dpi=300)
    plt.close()

print("Both figures generated successfully.")
