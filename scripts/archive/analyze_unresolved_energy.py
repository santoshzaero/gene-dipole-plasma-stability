from pathlib import Path
import csv
import numpy as np

ROOT = Path(__file__).resolve().parent
BASE = ROOT / "runs/isotope_scan"
OUTPUT = BASE / "energy_fit_results.csv"

def fit_window(t, energy, fraction):
    start = int(len(t) * (1 - fraction))
    x = t[start:]
    y = np.log(energy[start:])

    slope, intercept = np.polyfit(x, y, 1)
    predicted = slope * x + intercept

    ss_res = np.sum((y - predicted)**2)
    ss_tot = np.sum((y - np.mean(y))**2)

    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan

    return slope / 2, r2

results = []

for isotope in ("hydrogen", "deuterium"):
    csv_file = BASE / f"{isotope}_results.csv"

    with csv_file.open() as f:
        cases = list(csv.DictReader(f))

    for case in cases:
        if case["status"] != "UNRESOLVED":
            continue

        omn = float(case["omn"])
        omt = float(case["omt"])

        name = (
            f"omn_{f"{omn:g}".replace('.', 'p')}_"
            f"omt_{f"{omt:g}".replace('.', 'p')}"
        )

        path = BASE / isotope / name / "out/energy.dat"

        try:
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

            if len(t) < 100:
                raise ValueError("Insufficient valid energy samples")

            g50, r50 = fit_window(t, energy, 0.50)
            g30, r30 = fit_window(t, energy, 0.30)
            g15, r15 = fit_window(t, energy, 0.15)

            spread = max(abs(g50-g15), abs(g30-g15))
            tolerance = max(0.05, 0.1 * abs(g15))

            reliable = (
                r15 > 0.99 and
                r30 > 0.99 and
                spread < tolerance
            )

            status = "CONSISTENT" if reliable else "UNCERTAIN"

            results.append([
                isotope, omn, omt,
                g50, g30, g15,
                r50, r30, r15,
                status
            ])

            print(
                f"{isotope:9s} "
                f"omn={omn:3g} omt={omt:3g} "
                f"gamma50={g50:8.4f} "
                f"gamma30={g30:8.4f} "
                f"gamma15={g15:8.4f} "
                f"R2={r15:.5f} "
                f"{status}"
            )

        except Exception as e:
            print(isotope, omn, omt, "ERROR:", e)

with OUTPUT.open("w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "isotope", "omn", "omt",
        "gamma_last50", "gamma_last30", "gamma_last15",
        "r2_last50", "r2_last30", "r2_last15",
        "fit_status"
    ])
    writer.writerows(results)

print("\nSaved:", OUTPUT)
