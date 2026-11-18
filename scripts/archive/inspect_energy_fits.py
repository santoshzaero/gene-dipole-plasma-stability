from pathlib import Path
import csv
import numpy as np
import matplotlib.pyplot as plt

BASE = Path("runs/isotope_scan")
OUT = BASE / "plots" / "energy_diagnostics"
OUT.mkdir(parents=True, exist_ok=True)

with (BASE / "energy_fit_results.csv").open() as f:
    cases = list(csv.DictReader(f))

fig, axes = plt.subplots(4, 4, figsize=(17, 15))
axes = axes.ravel()

for k, case in enumerate(cases):
    ax = axes[k]

    isotope = case["isotope"]
    omn = float(case["omn"])
    omt = float(case["omt"])

    folder = (
        f"omn_{omn:g}_omt_{omt:g}"
        .replace(".", "p")
    )

    path = BASE / isotope / folder / "out/energy.dat"
    data = np.loadtxt(path, comments="#")

    t = data[:, 0]
    energy = data[:, 1]

    valid = (
        np.isfinite(t) &
        np.isfinite(energy) &
        (energy > 0)
    )

    t = t[valid]
    energy = energy[valid]
    log_energy = np.log(energy)

    ax.plot(t, log_energy, linewidth=1.2,
            label="ln(total free energy)")

    for fraction, color, label in [
        (0.50, "orange", "50%"),
        (0.30, "green", "30%"),
        (0.15, "red", "15%"),
    ]:
        start = int(len(t) * (1 - fraction))
        x = t[start:]
        y = log_energy[start:]

        slope, intercept = np.polyfit(x, y, 1)

        ax.plot(
            x, slope * x + intercept,
            color=color, linestyle="--",
            linewidth=1.4, label=label
        )

    ax.set_title(
        f"{isotope.capitalize()} | "
        f"omn={omn:g}, omt={omt:g}\n"
        f"{case['fit_status']}"
    )
    ax.set_xlabel("Normalized time")
    ax.set_ylabel("ln(W)")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=7)

for ax in axes[len(cases):]:
    ax.axis("off")

fig.suptitle(
    "Unresolved GENE Cases: Total Free-Energy Evolution",
    fontsize=16
)
fig.tight_layout()
fig.savefig(OUT / "all_13_energy_fits.png", dpi=200)
plt.close(fig)

# Detailed comparison for both uniform-gradient cases
fig, axes = plt.subplots(1, 2, figsize=(13, 5))

for ax, isotope in zip(axes, ["hydrogen", "deuterium"]):
    path = (
        BASE / isotope / "omn_0_omt_0"
        / "out/energy.dat"
    )

    data = np.loadtxt(path, comments="#")
    t = data[:, 0]
    energy = data[:, 1]

    valid = np.isfinite(energy) & (energy > 0)
    t = t[valid]
    energy = energy[valid]

    ax.plot(t, np.log(energy), label="ln(W)")

    for fraction in [0.50, 0.30, 0.15]:
        start = int(len(t) * (1 - fraction))
        x = t[start:]
        y = np.log(energy[start:])

        slope, intercept = np.polyfit(x, y, 1)

        ax.plot(
            x, slope*x + intercept,
            "--",
            label=f"Last {fraction:.0%}: γ={slope/2:.4f}"
        )

    ax.set_title(f"{isotope.capitalize()} — Uniform Gradients")
    ax.set_xlabel("Normalized time")
    ax.set_ylabel("ln(total free energy)")
    ax.legend()
    ax.grid(alpha=0.25)

fig.tight_layout()
fig.savefig(OUT / "uniform_gradient_comparison.png", dpi=250)
plt.close(fig)

print("Saved:")
print(OUT / "all_13_energy_fits.png")
print(OUT / "uniform_gradient_comparison.png")
