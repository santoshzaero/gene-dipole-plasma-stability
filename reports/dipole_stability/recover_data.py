#!/usr/bin/env python3
"""Prepare a portable report snapshot from saved results. This script only reads simulations."""
import argparse
import csv
import gzip
import hashlib
import io
import re
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

REPORT = Path(__file__).resolve().parent
ROOT = REPORT.parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from compare_parallel_resolution import read_fields

TABLES = {
    'run_index': 'run_index.csv', 'regression': 'installation/regression_summary.csv',
    'pair_density': 'pair/density_scan.csv', 'pair_grid': 'pair/gradient_scan.csv',
    'pair_windows': 'pair/classmate_iv/late_fits.csv', 'pair_projection': 'pair/classmate_iv/field_history.csv',
    'isotope_hydrogen': 'isotope/hydrogen.csv', 'isotope_deuterium': 'isotope/deuterium.csv',
    'isotope_fit': 'isotope/energy_fit_original.csv', 'isotope_quality': 'isotope/growth_rates_with_quality_original.csv',
    'isotope_wavenumber': 'ky/original.csv', 'phase2_runs': 'deuterium_meeting/runs.csv',
    'phase2_fits': 'deuterium_meeting/fits.csv', 'phase2_extension': 'deuterium_final/runs.csv',
    'phase2_extension_fits': 'deuterium_final/fits.csv', 'phase2_extension_overlap': 'deuterium_final/spatial_overlaps.csv',
    'phase2_overlap': 'deuterium_meeting/spatial_overlaps.csv', 'pilot_comparison': 'deuterium_density_pilot/comparison.csv',
}
CONTROLS = {'z': 'deuterium_nz32_nz64', 'step': 'deuterium_timestep_nz24', 'v': 'deuterium_nv48_nv64',
            'mu': 'deuterium_nw32_nw48', 'combined': 'deuterium_combined', 'domain': 'deuterium_moment_controls'}
DATALESS = 0x40000000  # Darwin SF_DATALESS; offloaded files can otherwise block opening.


def csv_rows(path):
    with path.open(newline='') as stream:
        return list(csv.DictReader(stream))


def write_rows(path, rows):
    if path.suffix == '.gz':
        stream = io.TextIOWrapper(gzip.GzipFile(filename='', fileobj=path.open('wb'), mode='wb', mtime=0), newline='')
    else:
        stream = path.open('w', newline='')
    with stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys(), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def available_bytes(path):
    if not path.is_file():
        return None
    if getattr(path.stat(), 'st_flags', 0) & DATALESS:
        try:
            return subprocess.run(['cat', str(path)], capture_output=True, check=True, timeout=2).stdout
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            return None
    return path.read_bytes()


def add_energy(output, lineage, name, stored, raw=None):
    content = available_bytes(raw) if raw is not None else None
    if content is not None:
        data = np.loadtxt(io.BytesIO(content), usecols=(0, 1))
        method = 'native energy.dat'
        sha = hashlib.sha256(content).hexdigest()
    elif stored is not None:
        delimiter = ',' if stored.name.endswith('.csv.gz') else None
        data = np.loadtxt(stored, usecols=(0, 1), skiprows=1, delimiter=delimiter)
        method = 'curated energy diagnostic'
        sha = hashlib.sha256(stored.read_bytes()).hexdigest()
    else:
        lineage.append(dict(case=name, quantity='energy', source='unavailable', sha256=''))
        return
    usable = np.isfinite(data).all(axis=1) & (data[:, 1] > 0)
    output.extend(dict(case=name, time=f'{t:.16g}', energy=f'{w:.16g}') for t, w in data[usable])
    lineage.append(dict(case=name, quantity='energy', source=method, sha256=sha))


def native_field(path, nodes, scratch):
    content = available_bytes(path)
    if content is None:
        return None
    scratch.write_bytes(content)
    t, field, _ = read_fields(scratch, nodes)
    return t, field, hashlib.sha256(content).hexdigest()


def recover_profiles(archive, raw, work, output, lineage, scratch):
    stored = {}
    for path in ('deuterium_meeting/profiles.csv', 'deuterium_final/profiles.csv'):
        source = archive / path
        for row in csv_rows(source):
            stored.setdefault(row['case'], []).append(row)
    raw_paths = {
        'matrix_1_0p7': work / 'deuterium_density_pilot/omn_1',
        'matrix_2_0p7': work / 'convergence/deuterium_nz24_nw24_auto',
        'matrix_3_0p7': work / 'deuterium_density_pilot/omn_3',
        'matrix_2_0p5': raw / 'ky_scan/deuterium/ky_0p5', 'matrix_2_1': raw / 'ky_scan/deuterium/ky_1',
        'omn_2_ky_1p5': raw / 'ky_scan/deuterium/ky_1p5', 'omn_2_ky_2': raw / 'ky_scan/deuterium/ky_2',
        'omn_2_ky_0p3': raw / 'ky_scan/deuterium/ky_0p3',
        'h_reference': raw / 'ky_scan/hydrogen/ky_0p7', 'd_reference': raw / 'ky_scan/deuterium/ky_0p7',
    }
    for gradient in (1, 3):
        for ky in ('0p5', '1'):
            raw_paths[f'matrix_{gradient}_{ky}'] = work / f'deuterium_meeting/omn_{gradient}_ky_{ky}'
        name = f'omn_{gradient}_ky_1p5'
        raw_paths[name] = work / 'deuterium_final' / name
    for model in ('kinetic', 'adiabatic'):
        name = f'{model}_collisionless'
        raw_paths[name] = work / 'deuterium_meeting' / name
    histories = []
    for case, source in raw_paths.items():
        nr = stored.get(case, [])
        n = len(nr) or 32
        resolved = native_field(source / 'out/field.dat', n, scratch)
        if resolved is None:
            if nr:
                output.extend(nr)
                source_name = 'curated final complex samples'
            else:
                source_name = 'unavailable'
            lineage.append(dict(case=case, quantity='field', source=source_name, sha256=''))
            continue
        t, field, sha = resolved
        final = field[-1] / np.max(np.abs(field[-1]))
        if nr:
            expected = np.array([complex(float(r['real']), float(r['imag'])) for r in nr])
            np.testing.assert_allclose(final, expected, rtol=1e-12, atol=1e-13, err_msg=case)
        output.extend(dict(case=case, s=float(z), real=p.real, imag=p.imag) for z, p in zip(np.linspace(0, 1, n), final))
        lineage.append(dict(case=case, quantity='field', source='native field.dat', sha256=sha))
        if case.endswith('collisionless'):
            projection = field @ final.conj() / np.vdot(final, final).real
            keep = np.abs(projection) > 0
            phase = np.unwrap(np.angle(projection[keep] / projection[-1]))
            histories.extend(dict(case=case, time=ti, relative_amplitude=abs(a / projection[-1]), phase=ph)
                             for ti, a, ph in zip(t[keep], projection[keep], phase))
    return histories


def recover_pair(work, data, lineage, scratch):
    source = work / 'classmate_reference/pair_iv/out/field.dat'
    resolved = native_field(source, 24, scratch)
    if resolved is None:
        lineage.append(dict(case='pair_benchmark', quantity='field', source='curated projection and peak', sha256=''))
        return
    t, f, sha = resolved
    a = f @ f[-1].conj() / np.linalg.norm(f[-1])**2
    keep = np.abs(a) > 0
    stored = csv_rows(data / 'pair_projection.csv')
    assert sha == '4c4560380df22d172f0fad297778bac270222d108b53cf0b5058208a18b79cdc'
    np.testing.assert_allclose(t[keep], [float(r['time']) for r in stored], rtol=1e-13, atol=0)
    p = np.array([complex(float(r['projection_real']), float(r['projection_imag'])) for r in stored])
    np.testing.assert_allclose(a[keep] / a[-1], p / p[-1], rtol=1e-12, atol=1e-15)
    lineage.append(dict(case='pair_benchmark', quantity='field', source='native field.dat with verified projection', sha256=sha))


def survey(roots):
    rows = []
    for label, root in roots:
        for path in sorted(root.rglob('parameters')):
            content = available_bytes(path)
            if not content:
                rows.append(dict(collection=label, path=str(path.relative_to(root)), solver='', species='',
                                 kymin='', masses='', charges='', omn='', omt='', input_sha256=''))
                continue
            text = re.sub(r'(?m)!.*$', '', content.decode(errors='replace'))
            def values(key):
                return ';'.join(re.findall(rf'(?im)^\s*{key}\s*=\s*[\'\"]?([^\s,\'\"]+)', text))
            blocks = re.findall(r'(?ims)^\s*&species\b(.*?)^\s*/', text)
            rows.append(dict(collection=label, path=str(path.relative_to(root)), solver=values('comp_type'), species=len(blocks),
                             kymin=values('kymin'), masses=values('mass'), charges=values('charge'), omn=values('omn'),
                             omt=values('omt'), input_sha256=hashlib.sha256(content).hexdigest()))
    return rows


def copy_table(source, destination):
    destination.write_bytes(source.read_bytes().replace(b'\r\n', b'\n'))


def recover(source_repo, raw, work, data):
    archive = source_repo / 'results'
    data.mkdir(parents=True, exist_ok=True)
    for key, relative in TABLES.items():
        copy_table(archive / relative, data / f'{key}.csv')
    for key, study in CONTROLS.items():
        for kind in ('runs', 'comparison', 'late_fits'):
            copy_table(archive / 'convergence' / study / f'{kind}.csv', data / f'{key}_{kind}.csv')
    for n in (32, 64):
        filename = f'field_nz{n}.csv.gz'
        shutil.copyfile(archive / 'convergence/deuterium_nz32_nz64' / filename, data / filename)
    lineage, energies, profiles = [], [], []
    for group, version, directory in [('pair', 'extended', 'gradient_scan_extended'), ('pair', 'original', 'gradient_scan_2d')]:
        for path in sorted((archive / group / 'energy_histories' / version).glob('*/time_energy.tsv.gz')):
            add_energy(energies, lineage, f'pair_{version}_{path.parent.name}', path,
                       raw / directory / path.parent.name / 'out/energy.dat')
    for path in sorted((archive / 'isotope/energy_histories').glob('*/*/time_energy.tsv.gz')):
        relative = path.relative_to(archive / 'isotope/energy_histories')
        add_energy(energies, lineage, f'{relative.parts[0]}_{relative.parts[1]}', path,
                   raw / 'isotope_scan' / relative.parent / 'out/energy.dat')
    for ky in ('0p3', '0p5'):
        path = Path(f'deuterium/ky_{ky}')
        add_energy(energies, lineage, f'ky_{ky}', archive / 'ky/energy_histories' / path / 'time_energy.tsv.gz',
                   raw / 'ky_scan' / path / 'out/energy.dat')
    for key, cases in {'v': ('nv32', 'nv32_fixed', 'nv48'), 'combined': ('extent', 'extent_fixed', 'reduced')}.items():
        for case in cases:
            path = archive / 'convergence' / CONTROLS[key] / f'{case}_energy.csv.gz'
            add_energy(energies, lineage, case, path)
    zero_raw = raw / 'zero_gradient_20000/out/energy.dat'
    if zero_raw.is_file():
        add_energy(energies, lineage, 'hydrogen_zero_extension', None, zero_raw)
    scratch = data / '.field.tmp'
    try:
        histories = recover_profiles(archive, raw, work, profiles, lineage, scratch)
        recover_pair(work, data, lineage, scratch)
    finally:
        scratch.unlink(missing_ok=True)
    write_rows(data / 'raw_lineage.csv', lineage)
    write_rows(data / 'energy_histories.csv.gz', energies)
    write_rows(data / 'field_profiles.csv', profiles)
    if histories:
        write_rows(data / 'closure_time_series.csv.gz', histories)
    write_rows(data / 'input_inventory.csv', survey((('tracked configs', source_repo / 'configs'),
                                                   ('saved GENE runs', raw), ('local work', work))))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-repo', type=Path, default=ROOT)
    p.add_argument('--runs', type=Path, required=True)
    p.add_argument('--work', type=Path, default=ROOT / 'work')
    p.add_argument('--data', type=Path, default=REPORT / 'data')
    args = p.parse_args()
    recover(args.source_repo, args.runs, args.work, args.data)
