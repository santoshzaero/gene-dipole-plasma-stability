import csv
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

folder = Path.home() / "Developer/gene-complete/runs/gradient_scan_2d"

with (folder / "results.csv").open() as f:
    rows = list(csv.DictReader(f))

xs = sorted({float(r["omn"]) for r in rows})
ys = sorted({float(r["omt"]) for r in rows})

grid = np.full((len(ys), len(xs)), np.nan)

for r in rows:
    if r["status"] != "CONVERGED":
        continue
    if not r["gamma"]:
        continue
    i = ys.index(float(r["omt"]))
    j = xs.index(float(r["omn"]))
    grid[i, j] = float(r["gamma"])

fig, ax = plt.subplots(figsize=(8, 6))

finite = grid[np.isfinite(grid)]
if finite.size == 0:
    raise RuntimeError("No converged growth rates available.")

if finite.min() < 0 < finite.max():
    norm = TwoSlopeNorm(
        vmin=float(finite.min()),
        vcenter=0,
        vmax=float(finite.max()),
    )
    im = ax.imshow(grid, origin="lower", cmap="coolwarm",
                   norm=norm, aspect="auto")
else:
    im = ax.imshow(grid, origin="lower", cmap="viridis",
                   aspect="auto")

ax.set_xticks(range(len(xs)), labels=[f"{v:g}" for v in xs])
ax.set_yticks(range(len(ys)), labels=[f"{v:g}" for v in ys])
ax.set_xlabel("Density gradient (omn)")
ax.set_ylabel("Temperature gradient (omt)")
ax.set_title("GENE: Electron–positron dipole plasma stability scan")

for i in range(len(ys)):
    for j in range(len(xs)):
        if np.isfinite(grid[i, j]):
            ax.text(j, i, f"{grid[i,j]:.2f}",
                    ha="center", va="center", fontsize=8)

fig.colorbar(im, ax=ax, label="Growth rate γ (normalized)")
fig.tight_layout()
fig.savefig(folder / "stability_map.png", dpi=300)

print("Saved:", folder / "stability_map.png")
