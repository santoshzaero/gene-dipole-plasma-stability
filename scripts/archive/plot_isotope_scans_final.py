from pathlib import Path
import csv
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

BASE = Path("runs/isotope_scan")
OUT = BASE / "plots"
OUT.mkdir(parents=True, exist_ok=True)

VALUES = [0, 0.5, 1, 2, 3, 4, 5]
N = len(VALUES)

# Manually reviewed energy fit:
# Deuterium, omn=0, omt=0
# Negative free-energy slope observed in diagnostic plots.
APPROVED_EXTRA = {("deuterium", 0.0, 0.0)}

def load(isotope):
    matrix = np.full((N, N), np.nan)
    estimated = np.zeros((N, N), dtype=bool)

    # Load formally converged GENE results
    with (BASE / f"{isotope}_results.csv").open() as f:
        for row in csv.DictReader(f):
            if row["status"] != "CONVERGED" or not row["gamma"]:
                continue

            i = VALUES.index(float(row["omn"]))
            j = VALUES.index(float(row["omt"]))
            matrix[j, i] = float(row["gamma"])

    # Supplement with qualified energy-derived estimates
    with (BASE / "energy_fit_results.csv").open() as f:
        for row in csv.DictReader(f):
            if row["isotope"] != isotope:
                continue

            omn = float(row["omn"])
            omt = float(row["omt"])

            approved = (
                row["fit_status"] == "CONSISTENT"
                or (isotope, omn, omt) in APPROVED_EXTRA
            )

            if not approved:
                continue

            i = VALUES.index(omn)
            j = VALUES.index(omt)

            if np.isnan(matrix[j, i]):
                matrix[j, i] = float(row["gamma_last15"])
                estimated[j, i] = True

    return matrix, estimated


H, HE = load("hydrogen")
D, DE = load("deuterium")

DIFF = H - D
DIFFE = HE | DE


def plot_heatmap(
    matrix, estimated, title, filename,
    cmap="viridis", vmin=None, vmax=None,
    norm=None, colorbar_label="Normalized growth rate"
):
    fig, ax = plt.subplots(figsize=(9, 7.5))

    cm = plt.get_cmap(cmap).copy()
    cm.set_bad("#dddddd")

    im = ax.imshow(
        matrix,
        origin="lower",
        cmap=cm,
        vmin=vmin,
        vmax=vmax,
        norm=norm
    )

    ax.set_xticks(range(N), VALUES)
    ax.set_yticks(range(N), VALUES)
    ax.set_xlabel("Density gradient (omn)")
    ax.set_ylabel("Temperature gradient (omt)")
    ax.set_title(title, fontsize=14)

    for j in range(N):
        for i in range(N):
            value = matrix[j, i]

            if np.isfinite(value):
                label = f"{value:.2f}"

                if estimated[j, i]:
                    label += "*"

                color = (
                    "white"
                    if im.norm(value) > 0.55
                    else "black"
                )
            else:
                label = "N/C"
                color = "black"

            ax.text(
                i, j, label,
                ha="center",
                va="center",
                fontsize=9,
                color=color
            )

    fig.colorbar(
        im, ax=ax,
        label=colorbar_label
    )

    fig.text(
        0.5, 0.025,
        "* = total-free-energy estimate; "
        "N/C = no reliable growth-rate estimate",
        ha="center",
        fontsize=9
    )

    fig.tight_layout(rect=[0, 0.045, 1, 1])
    fig.savefig(OUT / filename, dpi=300)
    plt.close(fig)


# Shared color scale for both isotope heatmaps
common_min = min(np.nanmin(H), np.nanmin(D))
common_max = max(np.nanmax(H), np.nanmax(D))

plot_heatmap(
    H, HE,
    "Electron–Hydrogen Plasma: Linear Growth Rate",
    "hydrogen_heatmap_final.png",
    vmin=common_min,
    vmax=common_max
)

plot_heatmap(
    D, DE,
    "Electron–Deuterium Plasma: Linear Growth Rate",
    "deuterium_heatmap_final.png",
    vmin=common_min,
    vmax=common_max
)

# Isotope difference: H minus D
limit = np.nanmax(np.abs(DIFF))

plot_heatmap(
    DIFF, DIFFE,
    "Isotope Effect: Hydrogen − Deuterium",
    "isotope_difference_final.png",
    cmap="coolwarm",
    norm=TwoSlopeNorm(
        vmin=-limit,
        vcenter=0,
        vmax=limit
    ),
    colorbar_label="Difference in normalized growth rate"
)

# Save a combined numerical results table
with (OUT / "final_growth_rate_table.csv").open(
    "w", newline=""
) as f:
    writer = csv.writer(f)
    writer.writerow([
        "omn", "omt",
        "hydrogen_gamma", "hydrogen_method",
        "deuterium_gamma", "deuterium_method",
        "difference_H_minus_D"
    ])

    for j, omt in enumerate(VALUES):
        for i, omn in enumerate(VALUES):
            h = H[j, i]
            d = D[j, i]

            h_method = (
                "ENERGY_ESTIMATE" if HE[j, i]
                else "GENE_CONVERGED" if np.isfinite(h)
                else "UNRESOLVED"
            )

            d_method = (
                "ENERGY_ESTIMATE" if DE[j, i]
                else "GENE_CONVERGED" if np.isfinite(d)
                else "UNRESOLVED"
            )

            writer.writerow([
                omn, omt,
                h if np.isfinite(h) else "",
                h_method,
                d if np.isfinite(d) else "",
                d_method,
                h-d if np.isfinite(h) and np.isfinite(d) else ""
            ])

print("\n=== FINAL RESULTS ===")
print("Hydrogen numerical values:", np.isfinite(H).sum(), "/49")
print("Deuterium numerical values:", np.isfinite(D).sum(), "/49")
print("Paired comparisons:", np.isfinite(DIFF).sum(), "/49")
print("Energy-derived estimates:", HE.sum() + DE.sum())
print("Remaining unresolved:", np.isnan(H).sum() + np.isnan(D).sum())

print("\nFigures and table saved to:")
print(OUT.resolve())
