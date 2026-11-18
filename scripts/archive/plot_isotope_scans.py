from pathlib import Path
import csv
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "runs/isotope_scan"
PLOTS = DATA / "plots"
PLOTS.mkdir(parents=True, exist_ok=True)

VALUES = [0, 0.5, 1, 2, 3, 4, 5]

def load(isotope):
    matrix = np.full((7, 7), np.nan)
    with (DATA / f"{isotope}_results.csv").open() as f:
        for row in csv.DictReader(f):
            if row["status"] == "CONVERGED" and row["gamma"]:
                i = VALUES.index(float(row["omn"]))
                j = VALUES.index(float(row["omt"]))
                matrix[j, i] = float(row["gamma"])
    return matrix

H = load("hydrogen")
D = load("deuterium")
DIFF = H - D

def heatmap(matrix, title, filename, cmap="viridis",
            vmin=None, vmax=None, norm=None):
    fig, ax = plt.subplots(figsize=(8, 6.5))
    cm = plt.get_cmap(cmap).copy()
    cm.set_bad("#dddddd")

    im = ax.imshow(
        matrix, origin="lower", cmap=cm,
        vmin=vmin, vmax=vmax, norm=norm,
        aspect="equal"
    )

    ax.set_xticks(range(7), VALUES)
    ax.set_yticks(range(7), VALUES)
    ax.set_xlabel("Density gradient (omn)")
    ax.set_ylabel("Temperature gradient (omt)")
    ax.set_title(title)

    for j in range(7):
        for i in range(7):
            value = matrix[j, i]
            if np.isfinite(value):
                color = "white" if im.norm(value) > 0.55 else "black"
                ax.text(i, j, f"{value:.2f}",
                        ha="center", va="center",
                        fontsize=9, color=color)
            else:
                ax.text(i, j, "N/C", ha="center",
                        va="center", fontsize=9)

    fig.colorbar(im, ax=ax, label="Normalized growth rate")
    fig.tight_layout()
    fig.savefig(PLOTS / filename, dpi=250)
    plt.close(fig)

common_max = np.nanmax([np.nanmax(H), np.nanmax(D)])

heatmap(
    H, "Electron–Hydrogen: Linear Growth Rate",
    "hydrogen_heatmap.png", vmax=common_max, vmin=0
)

heatmap(
    D, "Electron–Deuterium: Linear Growth Rate",
    "deuterium_heatmap.png", vmax=common_max, vmin=0
)

difference_limit = np.nanmax(np.abs(DIFF))
heatmap(
    DIFF, "Isotope Effect: Hydrogen − Deuterium",
    "isotope_difference.png",
    cmap="coolwarm",
    norm=TwoSlopeNorm(
        vmin=-difference_limit,
        vcenter=0,
        vmax=difference_limit
    )
)

fig, ax = plt.subplots(figsize=(8, 5))
j = VALUES.index(2)

ax.plot(VALUES, H[j, :], "o-", label="Hydrogen")
ax.plot(VALUES, D[j, :], "s-", label="Deuterium")

ax.set_xlabel("Density gradient (omn)")
ax.set_ylabel("Normalized growth rate γ")
ax.set_title("Density-Gradient Scan at omt = 2")
ax.grid(alpha=0.3)
ax.legend()
fig.tight_layout()
fig.savefig(PLOTS / "density_gradient_comparison.png", dpi=250)
plt.close(fig)

print("Figures saved to:", PLOTS)
print("Hydrogen converged:", np.isfinite(H).sum(), "/49")
print("Deuterium converged:", np.isfinite(D).sum(), "/49")
print("Paired comparisons:", np.isfinite(DIFF).sum(), "/49")
