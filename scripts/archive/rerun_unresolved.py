from pathlib import Path
import subprocess
import os
import re
import shutil

ROOT = Path.home() / "Developer/gene-complete"
SOURCE = ROOT / "runs/gradient_scan_2d"
DEST = ROOT / "runs/gradient_scan_extended"
GENE = ROOT / "bin/gene_mac_arm64"

CASES = [
    "omn_0_omt_0",
    "omn_0_omt_0p5",
    "omn_0p5_omt_0p5",
    "omn_0_omt_1",
    "omn_0p5_omt_1",
]

env = os.environ.copy()
env["MACHINE"] = "mac_arm64"
env["OMP_NUM_THREADS"] = "1"

for name in CASES:
    source = SOURCE / name
    target = DEST / name

    if target.exists():
        print(f"Skipping existing directory: {target}")
        continue

    target.mkdir(parents=True)
    (target / "out").mkdir()

    params = (source / "parameters").read_text()

    params, count = re.subn(
        r"(?im)^(\s*ntimesteps\s*=\s*)\d+",
        lambda m: m.group(1) + "5000",
        params,
    )

    if count != 1:
        raise RuntimeError("Could not update ntimesteps")

    (target / "parameters").write_text(params)

    print(f"\nRunning {name}: 5000 steps maximum", flush=True)

    with (target / "run.log").open("w") as log:
        result = subprocess.run(
            [str(GENE)],
            cwd=target,
            stdout=log,
            stderr=subprocess.STDOUT,
            env=env,
        )

    log = (target / "run.log").read_text(errors="replace")

    if result.returncode != 0:
        status = "ERROR - inspect run.log"
    elif "Linear growth rate is converged" in log:
        status = "CONVERGED"
    else:
        status = "NOT CONVERGED"

    print(f"{name}: {status}", flush=True)

print("\nExtended runs completed.")
