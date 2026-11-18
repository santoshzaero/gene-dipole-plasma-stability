#!/usr/bin/env python3
"""GENE H/D fixed-gradient ky scan; run from gene-complete project root."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import os
import re
import subprocess

ROOT = Path(__file__).resolve().parent
GENE = ROOT / 'bin/gene_mac_arm64'
BASE_DIR = ROOT / 'runs/isotope_scan'
OUT = ROOT / 'runs/ky_scan'
KY = (0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0)
ISOTOPES = ('hydrogen', 'deuterium')
FIELDS = ('isotope', 'kymin', 'status', 'gamma', 'omega', 'returncode')

def ky_name(ky):
    return f'ky_{ky:g}'.replace('.', 'p')

def set_ky(text, ky):
    pattern = r'(?m)^(\s*kymin\s*=\s*)[-+0-9.eEdD]+'
    result, count = re.subn(pattern, lambda m: m.group(1) + str(ky), text)
    if count != 1:
        raise ValueError(f'Expected exactly one kymin setting, found {count}')
    return result

def parse_result(isotope, ky, folder):
    log = folder / 'run.log'
    if not log.exists():
        return None
    contents = log.read_text(errors='replace')
    converged = 'Linear growth rate is converged' in contents
    underflow = 'Exit due to reaching the underflow limit' in contents
    omega_file = folder / 'out/omega.dat'
    gamma = omega = ''
    if converged and omega_file.exists():
        for line in reversed(omega_file.read_text(errors='replace').splitlines()):
            parts = line.split()
            if len(parts) >= 3:
                try:
                    gamma, omega = float(parts[1]), float(parts[2])
                    break
                except ValueError:
                    pass
    status = 'CONVERGED' if converged and gamma != '' else ('UNDERFLOW' if underflow else 'UNRESOLVED')
    return {'isotope': isotope, 'kymin': ky, 'status': status,
            'gamma': gamma, 'omega': omega, 'returncode': ''}

def run_isotope(isotope):
    source = BASE_DIR / isotope / 'omn_2_omt_2' / 'parameters'
    base = source.read_text()
    records = []
    env = os.environ.copy()
    env.update(MACHINE='mac_arm64', OMP_NUM_THREADS='1')
    for ky in KY:
        folder = OUT / isotope / ky_name(ky)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'out').mkdir(exist_ok=True)
        params = set_ky(base, ky)
        param_file = folder / 'parameters'
        old = parse_result(isotope, ky, folder)
        if old and old['status'] == 'CONVERGED' and param_file.exists() and param_file.read_text() == params:
            record = old
            print(f'[{isotope}] ky={ky:g}: reused converged result gamma={record["gamma"]}', flush=True)
        else:
            param_file.write_text(params)
            with (folder / 'run.log').open('w') as log:
                process = subprocess.run([str(GENE)], cwd=folder, env=env,
                                         stdout=log, stderr=subprocess.STDOUT)
            record = parse_result(isotope, ky, folder)
            if record is None:
                raise RuntimeError(f'Missing log: {folder}')
            record['returncode'] = process.returncode
            if process.returncode != 0:
                record['status'] = 'ERROR'
            print(f'[{isotope}] ky={ky:g}: {record["status"]} '
                  f'gamma={record["gamma"]} omega={record["omega"]}', flush=True)
        records.append(record)
        write_csv(OUT / f'{isotope}_ky_results.csv', records)
    return records

def write_csv(path, records):
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(records)

def plot(records):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        print('matplotlib unavailable: CSV generated, plot skipped.', flush=True)
        return
    fig, ax = plt.subplots(figsize=(9, 5.5))
    for isotope, marker in [('hydrogen', 'o'), ('deuterium', 's')]:
        points = [r for r in records if r['isotope'] == isotope and r['status'] == 'CONVERGED']
        if points:
            ax.plot([r['kymin'] for r in points], [r['gamma'] for r in points],
                    marker=marker, linewidth=2, label=f'{isotope.capitalize()} (GENE converged)')
    ax.set_xlabel('kymin (GENE normalized units)')
    ax.set_ylabel('Normalized linear growth rate γ')
    ax.set_title('Isotope comparison vs perpendicular wavenumber\nomn = omt = 2')
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    dest = OUT / 'isotope_ky_growth_comparison.png'
    fig.savefig(dest, dpi=220)
    plt.close(fig)
    print(f'Plot saved: {dest}', flush=True)

def main():
    if not GENE.is_file():
        raise FileNotFoundError(f'GENE executable not found: {GENE}')
    for isotope in ISOTOPES:
        source = BASE_DIR / isotope / 'omn_2_omt_2' / 'parameters'
        if not source.is_file():
            raise FileNotFoundError(f'Validated baseline missing: {source}')
    OUT.mkdir(parents=True, exist_ok=True)
    print('Starting 16 GENE cases with 2 parallel isotope workers.', flush=True)
    records = []
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {executor.submit(run_isotope, isotope): isotope for isotope in ISOTOPES}
        for future in as_completed(futures):
            records.extend(future.result())
    records.sort(key=lambda r: (r['isotope'], r['kymin']))
    write_csv(OUT / 'all_ky_results.csv', records)
    plot(records)
    print('Done. Summary:', flush=True)
    for isotope in ISOTOPES:
        subset = [r for r in records if r['isotope'] == isotope]
        converged = [r for r in subset if r['status'] == 'CONVERGED']
        print(f'  {isotope}: {len(converged)}/{len(subset)} converged', flush=True)
        if converged:
            peak = max(converged, key=lambda r: r['gamma'])
            print(f'    highest sampled converged γ={peak["gamma"]:.6g} at ky={peak["kymin"]:g}', flush=True)

if __name__ == '__main__':
    main()
