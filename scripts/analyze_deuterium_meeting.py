#!/usr/bin/env python3
"""Validate completed GENE IV runs and make the meeting tables and figures offline."""
import argparse
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.lines import Line2D
import numpy as np

from compare_parallel_resolution import capture, read_fields

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'results/deuterium_meeting'
FIGURES = ROOT / 'figures/deuterium_meeting'
CONFIGS = ROOT / 'configs'
POLICY = re.compile(r"(?m)^comp_type\s*=\s*'IV'\s*$")
COLORS = ('#226584', '#963f25', '#35745b')
RATES = {'gamma': r'Growth rate $\gamma L_{\rm ref}/c_{\rm ref}$',
         'omega': r'Signed real frequency $\omega L_{\rm ref}/c_{\rm ref}$'}


def cases(gene_runs, work):
    isotope = gene_runs / 'isotope_scan/deuterium'
    wave = gene_runs / 'ky_scan/deuterium'
    for gradient in (0, 0.5, 1, 2, 3, 4, 5):
        name = f'omn_{gradient:g}_omt_2'.replace('.', 'p')
        yield f'density_archived_{gradient:g}', isotope / name, CONFIGS / 'isotope/deuterium' / name / 'parameters', gradient, 0.7, 32, 'archive', 'density'
    for gradient in (1, 2, 3):
        if gradient == 2:
            name = 'deuterium_nz24_nw24_auto'
            directory, config = work / 'convergence' / name, CONFIGS / 'convergence' / name / 'parameters'
        else:
            name = f'omn_{gradient}'
            directory, config = work / 'deuterium_density_pilot' / name, CONFIGS / 'deuterium_density_pilot' / name / 'parameters'
        yield f'matrix_{gradient}_0p7', directory, config, gradient, 0.7, 24, 'archive', 'matrix'
    for gradient in (1, 2, 3):
        for ky, suffix in ((0.5, '0p5'), (1.0, '1')):
            label = f'matrix_{gradient}_{suffix}'
            if gradient == 2:
                name = f'ky_{suffix}'
                yield label, wave / name, CONFIGS / 'ky/deuterium' / name / 'parameters', gradient, ky, 32, 'archive', 'matrix'
            else:
                name = f'omn_{gradient}_ky_{suffix}'
                yield label, work / 'deuterium_meeting' / name, CONFIGS / 'deuterium_meeting' / name / 'parameters', gradient, ky, 24, 'new', 'matrix'
    for model in ('kinetic', 'adiabatic'):
        name = f'{model}_collisionless'
        yield name, work / 'deuterium_meeting' / name, CONFIGS / 'deuterium_meeting' / name / 'parameters', 2, 0.7, 24, 'new', 'closure'


def write_csv(path, rows):
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def read_run(case):
    label, directory, config, gradient, ky, nz, origin, purpose = case
    adiabatic = label == 'adiabatic_collisionless'
    species = 1 if adiabatic else 2
    collision = 0 if purpose == 'closure' else 0.01
    input_bytes = (directory / 'parameters').read_bytes()
    supplied = input_bytes.decode()
    if input_bytes != config.read_bytes() or not POLICY.search(supplied):
        raise ValueError(f'Unexpected archived input or solver: {label}')
    for key, values in {'omn': [gradient] * species, 'omt': [2] * species, 'kymin': [ky],
                        'nz0': [nz], 'nv0': [48], 'nw0': [nz], 'lv': [3.5], 'lw': [12.25],
                        'n_spec': [species], 'coll': [collision], 'mref': [1]}.items():
        seen = [float(value) for value in re.findall(rf'(?m)^{key}\s*=\s*([+\-\d.Ee]+)', supplied)]
        if seen != values:
            raise ValueError(f'Unexpected {key} in {label}: {seen}')
    process = json.loads((directory / 'process.json').read_text()) if origin == 'new' else {}
    log = (directory / 'run.log').read_text()
    metadata_path = directory / 'out/parameters.dat'
    metadata = metadata_path.read_text() if metadata_path.exists() else ''
    solver_converged = 'Linear growth rate is converged, exiting time loop' in log
    rescalings = log.lower().count('rescaled amplitudes')
    omega_file = directory / 'out/omega.dat'
    native = np.loadtxt(omega_file) if omega_file.exists() else np.array([])
    gamma = omega = None
    if native.shape == (3,) and np.isfinite(native).all() and native[0] == ky:
        gamma, omega = native[1:]
    case_ok = (solver_converged and not rescalings and process.get('returncode', 0) == 0 and
               gamma is not None and (gamma != 0 or omega != 0))
    if purpose == 'closure' and case_ok:
        banner = 'Electrons are adiabatic' if adiabatic else 'Kinetic electrons and ions'
        if banner not in log or 'without collisions' not in log:
            raise ValueError(f'GENE reported a different closure or collision setting: {label}')
    runtime = re.search(r'Total wallclock time for GENE:\s+([\d.]+)', log)
    steps = re.search(r'Computed\s+(\d+) time steps', log)
    recurrence = {name: float(value) for name, value in re.findall(
        r'(?m)^\*\* (ions|electrons)\s*:\s*([\d.]+)', log)}
    row = dict(case=label, purpose=purpose, origin=origin, input_path=config.relative_to(ROOT).as_posix(),
               omn=gradient, omt=2, kymin=ky, nz=nz, nv=48, nw=nz, lv=3.5, lw=12.25, solver='IV',
               electrons='adiabatic' if adiabatic else 'kinetic', coll=collision, auto_dt=True,
               solver_converged=solver_converged, qualified=case_ok, rescalings=rescalings,
               process_returncode=process.get('returncode'),
               gamma=gamma if case_ok else None, omega=omega if case_ok else None,
               raw_gamma=gamma, raw_omega=omega,
               gene_wall_s=float(runtime[1]) if runtime else None,
               process_elapsed_s=process.get('elapsed_s'), steps=int(steps[1]) if steps else None,
               dt=None, end_time=None, field_records=None, ion_recurrence=recurrence.get('ions'),
               electron_recurrence=recurrence.get('electrons'),
               input_sha256=hashlib.sha256(input_bytes).hexdigest(), source_revision=None)
    files = ('parameters', 'out/field.dat', 'out/omega.dat', 'out/parameters.dat', 'run.log')
    hashes = [dict(case=label, artifact=f, sha256=hashlib.sha256((directory / f).read_bytes()).hexdigest())
              for f in files if (directory / f).is_file()]
    field = directory / 'out/field.dat'
    if not field.exists():
        if case_ok:
            raise ValueError(f'Converged run lacks field diagnostic: {label}')
        return row, [], [], hashes
    for key, value in {'nz0': nz, 'nx0': 1, 'nky0': 1, 'n_fields': 1, 'PRECISION': 'DOUBLE',
                       'ENDIANNESS': 'LITTLE', 'OMP_NUM_THREADS': 1}.items():
        if capture(rf'^{key}\s*=\s*(\S+)', metadata) != str(value):
            raise ValueError(f'Unexpected field format in {label}: {key}')
    capture(r'We have\s+(1) MPI tasks', log)
    t, field_samples, records = read_fields(field, nz)
    row.update(dt=float(np.median(np.diff(t))), end_time=float(t[-1]), field_records=records,
               source_revision=capture(r'^GIT_BRANCH\s*=\s*(\w+)', metadata))
    if not case_ok:
        return row, [], [], hashes
    profile = field_samples[-1] / np.max(np.abs(field_samples[-1]))
    projected = field_samples @ profile.conj() / np.vdot(profile, profile).real
    keep = (np.abs(projected) > 0) & (np.linalg.norm(field_samples, axis=1) > 0)
    t, field_samples, projected = t[keep], field_samples[keep], projected[keep]
    phase = np.unwrap(np.angle(projected / projected[-1]))
    log_abs = np.log(np.abs(projected))
    overlap = np.abs(field_samples @ profile.conj()) / (np.linalg.norm(field_samples, axis=1) * np.linalg.norm(profile))
    overlap = np.minimum(overlap, 1)
    fits = []
    width = 5 if adiabatic else 0.5
    windows = [('late', t[-1] - width, t[-1]), ('earlier', t[-1] - 1.5 * width, t[-1] - 0.5 * width)]
    if adiabatic:
        windows.extend((('pre_recurrence_1', 30, 35), ('pre_recurrence_2', 35, 40), ('pre_recurrence_3', 40, 42)))
    for name, begin, end in windows:
        use = (t >= begin) & (t <= end)
        if use.sum() < 10:
            continue
        growth = np.polyfit(t[use], log_abs[use], 1)
        frequency = np.polyfit(t[use], phase[use], 1)
        fits.append(dict(case=label, window=name, start=t[use][0], end=t[use][-1], samples=use.sum(),
                         gamma=growth[0], omega=frequency[0], min_overlap=overlap[use].min(),
                         log_amplitude_rms=np.sqrt(np.mean((log_abs[use] - np.polyval(growth, t[use])) ** 2)),
                         phase_rms_rad=np.sqrt(np.mean((phase[use] - np.polyval(frequency, t[use])) ** 2))))
    spatial = [dict(case=label, s=s, real=p.real, imag=p.imag)
               for s, p in zip(np.linspace(0, 1, nz), profile)]
    return row, fits, spatial, hashes


def collect(gene_runs, work, dest):
    records = [read_run(case) for case in cases(gene_runs, work)]
    dest.mkdir(parents=True, exist_ok=True)
    for idx, name in enumerate(('runs', 'fits', 'profiles', 'raw_checksums')):
        rows = [group[0] for group in records] if idx == 0 else [row for group in records for row in group[idx]]
        write_csv(dest / f'{name}.csv', rows)


def load_profiles(data):
    profiles = {}
    for row in data:
        profiles.setdefault(row['case'], []).append((float(row['s']), complex(float(row['real']), float(row['imag']))))
    return {key: (np.array([s for s, _ in pairs]), np.array([p for _, p in pairs])) for key, pairs in profiles.items()}


def align(profiles, case, reference):
    s, p = profiles[case]
    s_ref, p_ref = profiles[reference]
    common = np.linspace(0, 1, 241)
    a = np.interp(common, s_ref, p_ref)
    b = np.interp(common, s, p)
    dot = np.vdot(a, b)
    overlap = float(np.clip(abs(dot) / (np.linalg.norm(a) * np.linalg.norm(b)), 0, 1))
    p = p * np.exp(-1j * (np.angle(dot) + np.angle(p_ref[0])))
    phase = np.where(np.abs(p) >= 0.05, np.angle(p), np.nan)
    return s, np.abs(p), phase, overlap


def plot_density(runs, quantity):
    fig, ax = plt.subplots(figsize=(7.2, 4.6), layout='constrained')
    for grid, selected, color, marker in (
        ('Archived 32 × 48 × 32', [r for r in runs if r['purpose'] == 'density'], COLORS[1], 's'),
        ('Reused 24 × 48 × 24', [r for r in runs if r['purpose'] == 'matrix' and r['kymin'] == '0.7'], COLORS[0], 'o'),
    ):
        rates = [float(r[quantity]) if r['qualified'] == 'True' else np.nan for r in selected]
        ax.plot([float(r['omn']) for r in selected], rates, color=color, marker=marker,
                markerfacecolor='white' if marker == 's' else color, linestyle='--' if marker == 's' else '-',
                linewidth=1.7, markersize=6, label=grid)
    ax.set(xticks=[0, 0.5, 1, 2, 3, 4, 5], xlabel=r'Common density gradient $\mathrm{omn}_e=\mathrm{omn}_D$',
           ylabel=RATES[quantity], title='Electron–deuterium dipole · density-gradient trend')
    ax.text(0.03, 0.78, r'$k_y\rho_{\mathrm{ref}}=0.7$  ·  $\mathrm{omt}_e=\mathrm{omt}_D=2$' + '\n' +
            'IV  ·  omn = 0 unresolved', transform=ax.transAxes, va='top', color='#414b53', fontsize=9)
    ax.legend(loc='upper left', frameon=False)
    ax.grid(alpha=0.22)
    return fig


def marker(row, color):
    if row['nz'] == '32':
        return dict(marker='s', markerfacecolor='white', markeredgecolor=color)
    return dict(marker='o', markerfacecolor=color if row['origin'] == 'new' else 'white', markeredgecolor=color)


def plot_wave(matrix, quantity):
    fig, ax = plt.subplots(figsize=(7.2, 4.65), layout='constrained')
    curves = []
    for gradient, color in zip((1, 2, 3), COLORS):
        selected = sorted((r for r in matrix if int(r['omn']) == gradient), key=lambda r: float(r['kymin']))
        x = [float(r['kymin']) for r in selected]
        y = [float(r[quantity]) if r['qualified'] == 'True' else np.nan for r in selected]
        line, = ax.plot(x, y, color=color, label=f'Common omn = {gradient}', lw=1.65)
        curves.append(line)
        for row, ky, rate in zip(selected, x, y):
            ax.plot(ky, rate, linestyle='none', color=color, markersize=7, **marker(row, color))
    style = [Line2D([0], [0], marker=shape, markerfacecolor=face, color='#424b55', linestyle='none',
                    label=label)
             for shape, face, label in [('o', '#424b55', 'New 24 × 48 × 24'),
                                         ('o', 'white', 'Reused 24 × 48 × 24'),
                                         ('s', 'white', 'Archived 32 × 48 × 32')]]
    loc = 'upper right' if quantity == 'gamma' else 'upper left'
    ax.legend(handles=curves + style, loc=loc, ncols=2, frameon=False, fontsize=8.5)
    ax.margins(y=0.19)
    ax.set(xlabel=r'Normalized binormal wavenumber $k_y\rho_{\rm ref}$', ylabel=RATES[quantity],
           title='Electron–deuterium dipole · wavenumber dependence', xticks=[0.5, 0.7, 1.0])
    ax.text(0.985, 0.03, r'IV  ·  $\mathrm{omt}_e=\mathrm{omt}_D=2$', transform=ax.transAxes,
            ha='right', va='bottom', fontsize=9, color='#414b53')
    ax.grid(alpha=0.22)
    return fig


def draw_profile(ax_a, ax_p, profiles, items, reference, ylabel):
    for case, label, color, style in items:
        if case not in profiles:
            continue
        s, amplitude, phase, _ = align(profiles, case, reference)
        ax_a.plot(s, amplitude, label=label, color=color, linestyle=style, lw=1.7)
        ax_p.plot(s, phase, color=color, linestyle=style, lw=1.7)
    for ax in (ax_a, ax_p):
        ax.set_xticks([0, 0.25, 0.5, 0.75, 1])
        ax.grid(alpha=0.22)
    ax_a.legend(frameon=False, fontsize=8.5, loc='best')
    ax_a.set_ylabel(ylabel)
    ax_p.set_ylabel('Relative phase (rad)')
    ax_p.set_xlabel('Field-line coordinate / full turn')


def plot_modes(profiles):
    fig, axes = plt.subplots(2, 2, figsize=(9.1, 6.0), layout='constrained', sharex='col')
    colors = zip(COLORS, ('-', '--', ':'))
    entries = list(colors)
    density = [(f'matrix_{g}_0p7', f'omn = {g}', color, style)
               for g, (color, style) in zip((1, 2, 3), entries)]
    wave = [(f'matrix_2_{suffix}', f'$k_y\\rho_{{\\rm ref}}$ = {ky}{archive}', color, style)
            for suffix, ky, archive, (color, style) in zip(('0p5', '0p7', '1'), (0.5, 0.7, 1.0), (' (32)', ' (24)', ' (32)'), entries)]
    amp = r'$|\phi|/\max |\phi|$'
    draw_profile(*axes[:, 0], profiles, density, 'matrix_2_0p7', amp)
    draw_profile(*axes[:, 1], profiles, wave, 'matrix_2_0p7', amp)
    axes[0, 0].set_title(r'Common density gradient at $k_y\rho_{\rm ref}=0.7$')
    axes[0, 1].set_title(r'Wavenumber at common $\mathrm{omn}=2$')
    fig.suptitle(r'Late-time complex IV modes  ·  $\mathrm{omt}_e=\mathrm{omt}_D=2$')
    return fig


def plot_closure(runs, profiles):
    fig, axes = plt.subplots(2, 2, figsize=(9.1, 6.2), layout='constrained')
    axes[1, 0].sharex(axes[0, 0])
    plt.setp(axes[0, 0].get_xticklabels(), visible=False)
    selected = [r for r in runs if r['purpose'] == 'closure']
    labels = ['Kinetic', 'Adiabatic']
    colors = COLORS[:2]
    items = [(r['case'], label + ' electrons', color, style)
             for r, label, color, style in zip(selected, labels, colors, ('-', '--'))]
    draw_profile(*axes[:, 0], profiles, items, 'kinetic_collisionless', r'$|\phi|/\max |\phi|$')
    for ax, quantity in zip(axes[:, 1], RATES):
        for i, (row, color) in enumerate(zip(selected, colors)):
            if row['qualified'] == 'True':
                value = float(row[quantity])
                ax.bar(i, value, color=color, width=0.5)
                ax.annotate(f'{value:+.3f}' if quantity == 'omega' else f'{value:.3f}', (i, value),
                            xytext=(0, 5 if value >= 0 else -4), textcoords='offset points',
                            va='bottom' if value >= 0 else 'top', ha='center', color=color, fontsize=10)
        ax.set(xticks=[0, 1], xticklabels=labels, ylabel=RATES[quantity], xlim=(-0.6, 1.6))
        ax.axhline(0, color='#424b55', lw=0.7)
        if quantity == 'omega':
            ax.set_ylim(-0.21, 1.10)
        else:
            ax.margins(y=0.21)
        ax.grid(axis='y', alpha=0.22)
        ax.set_axisbelow(True)
    fig.suptitle(r'Collisionless IV comparison  ·  common $\mathrm{omn}=\mathrm{omt}=2$  ·  $k_y\rho_{\rm ref}=0.7$')
    return fig


def plot_map(matrix):
    fig, axes = plt.subplots(1, 2, figsize=(9.3, 4.05), sharey=True, layout='constrained')
    ky = [0.5, 0.7, 1.0]
    gradients = [1, 2, 3]
    for ax, (quantity, cmap) in zip(axes, [('gamma', 'YlGnBu'), ('omega', 'YlOrBr')]):
        grid = np.full((3, 3), np.nan)
        for row in matrix:
            if row['qualified'] == 'True':
                g, k = gradients.index(int(row['omn'])), ky.index(float(row['kymin']))
                grid[g, k] = float(row[quantity])
        image = ax.imshow(grid, origin='lower', interpolation='nearest', cmap=cmap, aspect='auto')
        for row in matrix:
            g, k = gradients.index(int(row['omn'])), ky.index(float(row['kymin']))
            value = grid[g, k]
            if np.isfinite(value):
                lightness = np.dot(image.cmap(image.norm(value))[:3], [0.2126, 0.7152, 0.0722])
                ax.text(k, g, f'{value:.3f}' + ('*' if row['nz'] == '32' else ''), color='black' if lightness > 0.54 else 'white',
                        ha='center', va='center', fontsize=10)
        ax.set(xticks=range(3), xticklabels=ky, yticks=range(3), yticklabels=gradients,
               xlabel=r'$k_y\rho_{\rm ref}$', title=RATES[quantity])
    axes[0].set_ylabel(r'Common density gradient $\mathrm{omn}$')
    fig.suptitle(r'Discrete IV samples  ·  $\mathrm{omt}_e=\mathrm{omt}_D=2$  ·  * archived $32\times48\times32$')
    return fig


def figures_and_overlaps(data, output):
    with (data / 'runs.csv').open() as stream:
        runs = list(csv.DictReader(stream))
    with (data / 'profiles.csv').open() as stream:
        profiles = load_profiles(csv.DictReader(stream))
    matrix = [r for r in runs if r['purpose'] == 'matrix']
    pairs = [(r['case'], 'matrix_2_0p7') for r in matrix if r['case'] in profiles]
    pairs.append(('adiabatic_collisionless', 'kinetic_collisionless'))
    write_csv(data / 'spatial_overlaps.csv', [dict(case=case, reference=reference, overlap=align(profiles, case, reference)[-1])
                                              for case, reference in pairs if case in profiles and reference in profiles])
    charts = (
        ('01_density_growth', plot_density(runs, 'gamma')),
        ('02_density_frequency', plot_density(runs, 'omega')),
        ('03_wavenumber_growth', plot_wave(matrix, 'gamma')),
        ('04_wavenumber_frequency', plot_wave(matrix, 'omega')),
        ('05_mode_structure', plot_modes(profiles)),
        ('06_adiabatic_comparison', plot_closure(runs, profiles)),
        ('07_discrete_stability_map', plot_map(matrix)),
    )
    output.mkdir(parents=True, exist_ok=True)
    fixed_date = datetime(2026, 11, 18, tzinfo=timezone.utc)
    with PdfPages(output / 'meeting_figures.pdf', metadata={'Title': 'MAE 190 electron–deuterium dipole study',
                                                           'CreationDate': fixed_date, 'ModDate': fixed_date}) as pdf:
        for name, fig in charts:
            fig.savefig(output / f'{name}.png', dpi=240, facecolor='white')
            pdf.savefig(fig)
            plt.close(fig)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--extract', nargs=2, type=Path, metavar=('GENE_RUNS', 'REPOSITORY_WORK'))
    parser.add_argument('--data', type=Path, default=DATA)
    parser.add_argument('--figures', type=Path, default=FIGURES)
    args = parser.parse_args()
    if args.extract:
        collect(*args.extract, args.data)
    figures_and_overlaps(args.data, args.figures)
