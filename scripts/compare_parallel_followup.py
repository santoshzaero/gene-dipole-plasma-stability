#!/usr/bin/env python3
"""Check the timestep control and 24-point trial using completed GENE runs."""
import argparse
import csv
import hashlib
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from compare_parallel_resolution import late_fits, read_case, write_records

ROOT = Path(__file__).resolve().parents[1]
DT = "0.0005784803539135"
CONTROLS = f"calc_dt = F\ndt_vlasov = {DT}\nev_coll = 9300.0"
SPECS = (("nz32_auto", 32), ("nz64_auto", 64), ("nz32_matched", 32),
         ("nz24_matched", 24), ("nz24_auto", 24))
PAIRS = (("timestep", "nz32_auto", "nz32_matched"),
         ("matched_32_64", "nz32_matched", "nz64_auto"),
         ("coarsen_24_32", "nz24_matched", "nz32_matched"),
         ("production_24_32", "nz24_matched", "nz32_auto"),
         ("automatic_24_32", "nz24_auto", "nz32_auto"),
         ("timestep_24", "nz24_auto", "nz24_matched"))


def relative(value, reference):
    return abs(value - reference) / abs(reference) if reference != 0 else None


def load_cases(paths):
    baseline = (paths[0] / "parameters").read_text()
    if baseline != (ROOT / "configs/isotope/deuterium/omn_2_omt_2/parameters").read_text():
        raise ValueError("Baseline does not match archived benchmark")
    cases = {}
    for (label, nz), path in zip(SPECS, paths):
        expected = re.sub(r"(?m)^(nz0\s*=\s*)32$", rf"\g<1>{nz}", baseline)
        if label.endswith("matched"):
            expected = expected.replace("calc_dt = T", CONTROLS)
        if (path / "parameters").read_text() != expected:
            raise ValueError(f"Unexpected input changes: {label}")
        case = read_case(path, nz)
        stats = case[0]
        stats["input_sha256"] = hashlib.sha256((path / "parameters").read_bytes()).hexdigest()
        if label != "nz32_auto" and (stats["release"], stats["source_revision"]) != (
            cases["nz32_auto"][0]["release"], cases["nz32_auto"][0]["source_revision"]
        ):
            raise ValueError(f"Unexpected GENE version: {label}")
        if label.endswith("matched") and not np.isclose(stats["dt"], float(DT), rtol=1e-8, atol=0):
            raise ValueError(f"Timestep does not match: {label}")
        cases[label] = case
    return cases


def compare(pair, test, reference, cases, *, common_end=None):
    a, b = cases[test], cases[reference]
    a_stats, a_profile, *_ = a
    b_stats, b_profile, *_ = b
    if common_end is None:
        common_end = min(a_stats["final_time"], b_stats["final_time"])
    a_fit = list(late_fits(a, common_end))[-1]
    b_fit = list(late_fits(b, common_end))[-1]
    x = a_profile[:, 0] if len(a_profile) <= len(b_profile) else b_profile[:, 0]
    p, q = [np.interp(x, prof[:, 0], prof[:, 1] + 1j * prof[:, 2])
            for prof in (a_profile, b_profile)]
    overlap = float(abs(np.vdot(p, q)) / (np.linalg.norm(p) * np.linalg.norm(q)))
    rates = (("reported_gamma", a_stats["gamma"], b_stats["gamma"]),
             ("reported_omega", a_stats["omega"], b_stats["omega"]),
             ("field_gamma", a_fit["field_gamma"], b_fit["field_gamma"]),
             ("phase_omega", a_fit["phase_omega"], b_fit["phase_omega"]),
             ("energy_gamma", a_fit["energy_gamma"], b_fit["energy_gamma"]))
    converged = a_stats["gene_converged"] and b_stats["gene_converged"]
    row = {
        "comparison": pair, "case": test, "reference": reference,
        "common_start_t": a_fit["start_t"], "common_end_t": common_end,
        "both_gene_converged": converged,
        "complex_overlap": overlap,
        "wallclock_ratio": a_stats["wallclock_s"] / b_stats["wallclock_s"],
    }
    rates_pass = True
    for name, v1, v2 in rates:
        field_value = not name.startswith("reported") or converged
        diff = relative(v1, v2) if field_value else None
        row[f"{name}_case"] = v1 if field_value else None
        row[f"{name}_reference"] = v2 if field_value else None
        row[f"{name}_relative_difference"] = diff
        rates_pass &= diff is not None and diff < 0.01 and np.sign(v1) == np.sign(v2)
    row["passes_screen"] = converged and rates_pass and overlap >= 0.999
    return row


def archive(cases, comparisons, paths, dest):
    dest.mkdir(parents=True, exist_ok=True)
    write_records(dest / "runs.csv", [{"case": label, **case[0]} for label, case in cases.items()])
    write_records(dest / "comparison.csv", comparisons)
    write_records(dest / "late_fits.csv", [
        {"case": label, **fit} for label, case in cases.items()
        if case[0]["gene_converged"]
        for fit in list(late_fits(case, case[0]["final_time"]))[:3]
    ])
    sources = ("parameters", "run.log", "out/parameters.dat", "out/omega.dat",
               "out/field.dat", "out/energy.dat", "out/dipole.dat")
    write_records(dest / "source_sha256.csv", [
        {"case": label, "run_relative_path": name,
         "sha256": hashlib.sha256((directory / name).read_bytes()).hexdigest()}
        for label, directory in zip(cases, paths) for name in sources
    ])
    for label, (stats, profile, field, _) in cases.items():
        if not stats["gene_converged"]:
            continue
        # Thin the plot data after fitting all saved samples.
        plot_data = field[::10, :4]
        np.savetxt(dest / f"{label}_field.csv", plot_data, delimiter=",", comments="",
                   header="time,log_projected_amplitude,unwrapped_phase,template_overlap", fmt="%.12e")
        np.savetxt(dest / f"{label}_profile.csv", profile, delimiter=",", comments="",
                   header="trace_fraction,phi_real_scaled,phi_imag_scaled,b_normalized", fmt="%.12e")


def draw(dest, figure, *, labels=None, title="GENE deuterium reference · timestep and coarser-grid checks",
         converged_only=False):
    fig, (phase_ax, profile_ax) = plt.subplots(1, 2, figsize=(12, 4.4), layout="constrained")
    with (dest / "runs.csv").open() as stream:
        cases = [case for case in csv.DictReader(stream)
                 if not converged_only or case["gene_converged"] == "True"]
    labels = labels or {"nz32_auto": "32 · automatic dt", "nz64_auto": "64 · automatic dt",
              "nz32_matched": "32 · matched dt", "nz24_matched": "24 · matched dt",
              "nz24_auto": "24 · automatic dt"}
    start = min(float(case["final_time"]) for case in cases) - 0.55
    for case, color in zip(cases, ("#4c545b", "#b34d2a", "#1a7186", "#8265ae", "#0e7646")):
        name = case["case"]
        t, _, phase, _ = np.loadtxt(dest / f"{name}_field.csv", delimiter=",", skiprows=1).T
        mid = t[(t >= start) & (t <= t[-1] - 0.04)]
        slope = (np.interp(mid + 0.04, t, phase) - np.interp(mid - 0.04, t, phase)) / 0.08
        line_style = "--" if name == "nz24_auto" else "-"
        phase_ax.plot(mid, slope, label=labels[name], color=color, linestyle=line_style)
        x, real, imag, _ = np.loadtxt(dest / f"{name}_profile.csv", delimiter=",", skiprows=1).T
        profile_ax.plot(x, abs(real + 1j * imag), color=color, linestyle=line_style, marker=".", markersize=3)
    phase_ax.set(xlabel="Normalized time", ylabel="Signed phase slope",
                 title="Late-time frequency from the complex field")
    profile_ax.set(xlabel="Fraction along traced field line", ylabel=r"$|\phi|/\max|\phi|$",
                   title="Final potential envelope")
    phase_ax.legend(frameon=False, fontsize="small")
    for axis in (phase_ax, profile_ax):
        axis.grid(alpha=0.22)
    fig.suptitle(title, fontweight="bold")
    figure.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(figure, dpi=175)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", nargs="+", type=Path, help="Run folders in order 32 auto, 64 auto, 32 matched, 24 matched, 24 auto. The final two are optional.")
    parser.add_argument("--gate", action="store_true", help="Check the 32-point timestep control before the 24-point run.")
    parser.add_argument("--data", type=Path, default=ROOT / "results/convergence/deuterium_timestep_nz24")
    parser.add_argument("--figure", type=Path, default=ROOT / "figures/convergence/deuterium_timestep_nz24.png")
    args = parser.parse_args()
    if args.runs:
        if len(args.runs) not in ((3,) if args.gate else (3, 4, 5)):
            parser.error("Supply three runs for the gate, or three to five for analysis.")
        cases = load_cases(args.runs)
        comparisons = [compare(*pair, cases) for pair in PAIRS if pair[1] in cases]
        if args.gate:
            for row in comparisons:
                print(row)
            raise SystemExit(0 if all(row["passes_screen"] for row in comparisons) else 1)
        archive(cases, comparisons, args.runs, args.data)
    elif args.gate:
        parser.error("--gate requires completed run folders.")
    draw(args.data, args.figure)


if __name__ == "__main__":
    main()
