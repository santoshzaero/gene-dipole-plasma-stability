from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import subprocess
import os
import re
import csv

ROOT = Path(__file__).resolve().parent
GENE = ROOT / "bin/gene_mac_arm64"
BASE = ROOT / "runs/electron_hydrogen_extended/parameters"
OUTPUT = ROOT / "runs/isotope_scan"
VALUES = [0, 0.5, 1, 2, 3, 4, 5]

def replace_setting(text, key, value):
    pattern = rf"(?m)^(\s*{key}\s*=\s*)[0-9.Ee+-]+"
    text, count = re.subn(
        pattern,
        lambda m: m.group(1) + str(value),
        text
    )
    if count != 1:
        raise ValueError(f"Expected one {key}, found {count}")
    return text

def configure(base, ion_mass, omn, omt):
    parts = re.split(r"(?m)^&species\s*$", base)
    if len(parts) != 3:
        raise ValueError("Expected two species")

    head = replace_setting(parts[0], "ntimesteps", 5000)
    head = replace_setting(head, "istep_vsp", 0)

    species = []
    for i, block in enumerate(parts[1:]):
        block = replace_setting(block, "omn", omn)
        block = replace_setting(block, "omt", omt)
        if i == 0:
            block = replace_setting(block, "mass", ion_mass)
        species.append(block)

    return head + "&species" + species[0] + "&species" + species[1]

def run_case(args):
    isotope, mass, omn, omt = args
    name = f"omn_{str(omn).replace('.', 'p')}_omt_{str(omt).replace('.', 'p')}"
    folder = OUTPUT / isotope / name
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "out").mkdir(exist_ok=True)

    base = BASE.read_text()
    params = configure(base, mass, omn, omt)
    (folder / "parameters").write_text(params)

    env = os.environ.copy()
    env["MACHINE"] = "mac_arm64"
    env["OMP_NUM_THREADS"] = "1"

    with (folder / "run.log").open("w") as log:
        result = subprocess.run(
            [str(GENE)],
            cwd=folder,
            stdout=log,
            stderr=subprocess.STDOUT,
            env=env
        )

    log_text = (folder / "run.log").read_text(errors="replace")
    converged = "Linear growth rate is converged" in log_text
    underflow = "Exit due to reaching the underflow limit" in log_text

    gamma = ""
    omega = ""
    omega_file = folder / "out/omega.dat"

    if converged and omega_file.exists():
        try:
            fields = omega_file.read_text().splitlines()[-1].split()
            gamma = float(fields[1])
            omega = float(fields[2])
        except (IndexError, ValueError):
            pass

    if result.returncode != 0:
        status = "ERROR"
    elif converged:
        status = "CONVERGED"
    elif underflow:
        status = "UNDERFLOW"
    else:
        status = "UNRESOLVED"

    return isotope, omn, omt, status, gamma, omega, result.returncode

def worker(isotope, mass):
    tasks = [(isotope, mass, omn, omt)
             for omn in VALUES for omt in VALUES]
    results = []

    for task in tasks:
        result = run_case(task)
        results.append(result)
        _, omn, omt, status, gamma, omega, _ = result
        print(
            f"[{isotope}] omn={omn:g}, omt={omt:g}: "
            f"{status} gamma={gamma} omega={omega}",
            flush=True
        )

        csv_path = OUTPUT / f"{isotope}_results.csv"
        with csv_path.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "isotope", "omn", "omt", "status",
                "gamma", "omega", "returncode"
            ])
            writer.writerows(results)

    return isotope, len(results)

def main():
    if not GENE.exists() or not BASE.exists():
        raise FileNotFoundError("GENE executable or hydrogen baseline missing")

    OUTPUT.mkdir(parents=True, exist_ok=True)

    print("Starting 98 simulations using two parallel workers.",
          flush=True)

    with ProcessPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(worker, "hydrogen", 1.0),
            pool.submit(worker, "deuterium", 2.0)
        ]
        for future in as_completed(futures):
            print("Finished:", future.result(), flush=True)

    print("All isotope scans completed.", flush=True)

if __name__ == "__main__":
    main()
