#!/usr/bin/env python3
"""Draw the three final deuterium figures from qualified GENE IV samples."""
import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.ticker import MaxNLocator
import numpy as np

from analyze_deuterium_meeting import CONFIGS, ROOT, align, load_profiles, read_run, write_csv
from compare_parallel_resolution import read_fields

MEETING = ROOT / 'results/deuterium_meeting'
DATA = ROOT / 'results/deuterium_final'
FIGURES = ROOT / 'figures/deuterium_final'
COLORS = ('#245986', '#008071', '#AB4E29', '#7953A2')
INK = '#142638'
MUTED = '#45576A'
GRID = '#E7EDF2'
KY = r'$k_y\rho_{\mathrm{ref}}$'
OMN = r'$\mathrm{omn}_e=\mathrm{omn}_D$'
SETUP = r'Electron–deuterium dipole · linear IV · $\mathrm{omt}_e=\mathrm{omt}_D=2$'
QUANTITIES = (
    ('gamma', 'Growth rate', r'$\gamma L_{\mathrm{ref}}/c_{\mathrm{ref}}$'),
    ('omega', 'Signed real frequency', r'$\omega L_{\mathrm{ref}}/c_{\mathrm{ref}}$'),
)


def read_csv(path):
    with path.open(newline='') as stream:
        return list(csv.DictReader(stream))


def collect(gene_runs, work, dest):
    wave = gene_runs / 'ky_scan/deuterium'
    cases = []
    for ky, suffix in ((0.1, '0p1'), (0.2, '0p2'), (0.3, '0p3'), (1.5, '1p5'), (2.0, '2')):
        name = f'ky_{suffix}'
        cases.append((f'omn_2_ky_{suffix}', wave / name, CONFIGS / 'ky/deuterium' / name / 'parameters',
                      2, ky, 32, 'archive', 'wavenumber'))
    for gradient in (1, 3):
        name = f'omn_{gradient}_ky_1p5'
        cases.append((name, work / name, CONFIGS / 'deuterium_final' / name / 'parameters',
                      gradient, 1.5, 24, 'new', 'wavenumber'))
    records = [read_run(case) for case in cases]
    dest.mkdir(parents=True, exist_ok=True)
    for i, name in enumerate(('runs', 'fits', 'profiles', 'raw_checksums')):
        rows = [record[0] for record in records] if i == 0 else [row for record in records for row in record[i]]
        write_csv(dest / f'{name}.csv', rows)
    profiles = load_profiles(read_csv(MEETING / 'profiles.csv') + read_csv(dest / 'profiles.csv'))
    reference = 'matrix_2_0p7'
    comparisons = [dict(case=row['case'], reference=reference, overlap=align(profiles, row['case'], reference)[-1])
                   for row, *_ in records if row['qualified']]
    _, suspect, _ = read_fields(wave / 'ky_0p3/out/field.dat', 32)
    _, nearby, _ = read_fields(wave / 'ky_0p5/out/field.dat', 32)
    overlap = abs(np.vdot(suspect[-1], nearby[-1])) / (np.linalg.norm(suspect[-1]) * np.linalg.norm(nearby[-1]))
    comparisons.append(dict(case='omn_2_ky_0p3', reference='matrix_2_0p5', overlap=overlap))
    write_csv(dest / 'spatial_overlaps.csv', comparisons)


def axes_style(ax):
    ax.set_axisbelow(True)
    ax.grid(True, color=GRID, linewidth=0.65)
    ax.spines[['top', 'right']].set_visible(False)
    ax.spines[['left', 'bottom']].set_color('#B6C3CD')
    ax.tick_params(length=3.2, width=0.7, color='#9AABB9', labelcolor=INK)


def heading(fig, number, title):
    fig.text(0.080, 0.936, f'FIGURE {number}', color=COLORS[0], fontsize=9, fontweight='bold')
    fig.text(0.080, 0.879, title, color=INK, fontsize=22, fontweight='bold')


def caption(fig, text):
    fig.text(0.080, 0.060, text, color=MUTED, fontsize=10.0, linespacing=1.55, va='bottom')


def scan_figure(points, number, title, x_values, curves, curve_key, x_label, curve_label, bottom):
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 6.4), facecolor='white')
    fig.subplots_adjust(left=0.102, right=0.962, bottom=0.285, top=0.753, wspace=0.285)
    heading(fig, number, title)
    for ax, (quantity, panel_title, units) in zip(axes, QUANTITIES):
        axes_style(ax)
        for curve, color in zip(curves, COLORS):
            y = []
            for x in x_values:
                key = (curve, x) if curve_key == 'omn' else (x, curve)
                row = points.get(key)
                y.append(float(row[quantity]) if row and row['qualified'] == 'True' else np.nan)
            ax.plot(x_values, y, marker='o', markersize=5.9, markeredgecolor='white', markeredgewidth=0.8,
                    color=color, lw=1.9, label=curve_label(curve), zorder=3)
        ax.set_title(panel_title, loc='left', fontsize=13, fontweight='bold', color=INK, pad=11)
        ax.set_xticks([x for x in x_values if x != 0])
        ax.set_xticklabels([f'{x:g}' for x in x_values if x != 0])
        ax.set_xlabel(x_label, labelpad=9)
        ax.set_ylabel(units, labelpad=9)
        ax.yaxis.set_major_locator(MaxNLocator(5))
        ax.margins(x=0.045, y=0.09)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(0.53, 0.139),
               ncols=len(curves), frameon=False, handlelength=2.1, columnspacing=1.65,
               fontsize=10.5)
    caption(fig, bottom)
    return fig


def closure_figure(runs, profiles):
    fig = plt.figure(figsize=(10.8, 6.4), facecolor='white')
    heading(fig, 5, 'Adiabatic electrons weaken the instability')
    axes = (fig.add_axes([0.225, 0.565, 0.315, 0.175]), fig.add_axes([0.640, 0.565, 0.315, 0.175]))
    treatments = ('kinetic_collisionless', 'adiabatic_collisionless')
    names = ('Kinetic electrons', 'Adiabatic electrons')
    colors = (COLORS[0], COLORS[2])
    for i, (ax, (key, title, units)) in enumerate(zip(axes, QUANTITIES)):
        axes_style(ax)
        ax.yaxis.grid(False)
        ax.spines['left'].set_visible(False)
        ax.set_title(title, loc='left', fontsize=13, fontweight='bold', color=INK, pad=11)
        ax.axvline(0.0, color='#A1AFBC', linewidth=1.0)
        ax.set(xlabel=units, ylim=(-0.60, 1.52), xlim=((-0.12, 5.12) if i == 0 else (-0.22, 1.28)))
        ax.xaxis.set_major_locator(MaxNLocator(5))
        ax.set_yticks([1, 0], names if i == 0 else ['', ''])
        ax.tick_params(axis='y', length=0, pad=9)
        for y, case, color in zip((1, 0), treatments, colors):
            value = float(runs[case][key])
            ax.scatter(value, y, s=72, color=color, edgecolors='white', linewidths=0.7, zorder=4)
            ax.annotate(f'{value:+.3f}' if key == 'omega' else f'{value:.3f}', (value, y), xytext=(9, 0),
                        textcoords='offset points', va='center', color=color, fontweight='bold')

    ax = fig.add_axes([0.136, 0.228, 0.817, 0.185])
    axes_style(ax)
    ax.set_title('Electrostatic potential along the field line', loc='left', fontsize=12,
                 fontweight='bold', color=INK, pad=9)
    for case, name, color in zip(treatments, names, colors):
        s, amplitude, _, _ = align(profiles, case, treatments[0])
        ax.plot(s, amplitude, color=color, lw=1.9, label=name)
    ax.set(xlim=(0, 1), ylim=(0.67, 1.035), xticks=[0, 0.25, 0.5, 0.75, 1],
           xlabel='Field-line coordinate / full turn', ylabel=r'$|\phi|/\max|\phi|$')
    ax.set_xticklabels(['0', '¼', '½', '¾', '1'])
    ax.legend(frameon=False, loc='lower center', ncols=2, fontsize=9.4)
    caption(fig, SETUP + r' · common $\mathrm{omn}=2$ · $k_y\rho_{\mathrm{ref}}=0.7$ · collisionless' + '\n' +
            'The Boltzmann closure replaces the kinetic electron response. The amplitude peak shifts along the field line.')
    return fig


def plot(data, output):
    meeting = read_csv(MEETING / 'runs.csv')
    extended = read_csv(data / 'runs.csv')
    by_case = {row['case']: row for row in meeting + extended}
    matrix = {(float(row['omn']), float(row['kymin'])): row for row in meeting + extended
              if row['purpose'] in ('matrix', 'wavenumber')}
    density = {(float(row['omn']), float(row['kymin'])): row for row in meeting if row['purpose'] == 'density'}
    density.update(matrix)
    profiles = load_profiles(read_csv(MEETING / 'profiles.csv'))
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'mathtext.fontset': 'stix', 'font.size': 11,
                         'axes.labelcolor': INK, 'axes.labelsize': 11.5, 'text.color': INK,
                         'pdf.fonttype': 42})
    figures = (
        ('figure_1_wavenumber', scan_figure(
            matrix, 1, 'Growth and frequency versus wavenumber', (0.5, 0.7, 1.0, 1.5, 2.0),
            (1, 2, 3), 'omn', f'Normalized binormal wavenumber  {KY}',
            lambda g: rf'$\mathrm{{omn}}={g:g}$', SETUP + '\n' +
            'Curves connect consecutive simulated samples. The longest curve continues to 2.0 at common omn = 2.')),
        ('figure_2_density', scan_figure(
            density, 2, 'Growth and frequency versus density gradient', (0, 0.5, 1, 2, 3, 4, 5),
            (0.5, 0.7, 1.0, 1.5), 'kymin', f'Common density gradient  {OMN}',
            lambda k: rf'$k_y\rho_{{\mathrm{{ref}}}}={k:g}$', SETUP + '\n' +
            'The density scan spans 0.5 to 5 at wavenumber 0.7. Other curves cover the shared range from 1 to 3.')),
        ('figure_5_electron_response', closure_figure(by_case, profiles)),
    )
    output.mkdir(parents=True, exist_ok=True)
    date = datetime(2026, 11, 18, tzinfo=timezone.utc)
    metadata = {'Title': 'Electron–deuterium dipole stability', 'CreationDate': date, 'ModDate': date}
    with PdfPages(output / 'final_figures.pdf', metadata=metadata) as combined:
        for name, fig in figures:
            fig.savefig(output / f'{name}.png', dpi=360)
            fig.savefig(output / f'{name}.pdf', metadata=metadata)
            combined.savefig(fig)
            plt.close(fig)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--extract', nargs=2, type=Path, metavar=('GENE_RUNS', 'FINAL_WORK'))
    parser.add_argument('--data', type=Path, default=DATA)
    parser.add_argument('--figures', type=Path, default=FIGURES)
    args = parser.parse_args()
    if args.extract:
        collect(*args.extract, args.data)
    plot(args.data, args.figures)
