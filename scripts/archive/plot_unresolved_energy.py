from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

root = Path.home() / "Developer/gene-complete/runs/gradient_scan_2d"

cases = [
    ("omn_0_omt_0", "omn=0, omt=0"),
    ("omn_0_omt_0p5", "omn=0, omt=0.5"),
    ("omn_0p5_omt_0p5", "omn=0.5, omt=0.5"),
    ("omn_0_omt_1", "omn=0, omt=1"),
    ("omn_0p5_omt_1", "omn=0.5, omt=1"),
]

fig, ax = plt.subplots(figsize=(9, 6))

for folder, label in cases:
    path = root / folder / "out/energy.dat"
    data = np.loadtxt(path, comments="#")

    time = data[:, 0]
    energy = data[:, 1]

    valid = np.isfinite(energy) & (energy > 0)
    ax.plot(time[valid], energy[valid], label=label)

ax.set_yscale("log")
ax.set_xlabel("Normalized simulation time")
ax.set_ylabel("Total energy (log scale)")
ax.set_title("GENE: Energy evolution near candidate stability boundary")
ax.legend()
ax.grid(True, which="both", alpha=0.25)

fig.tight_layout()
output = root / "unresolved_energy_evolution.png"
fig.savefig(output, dpi=300)

print("Saved:", output)
