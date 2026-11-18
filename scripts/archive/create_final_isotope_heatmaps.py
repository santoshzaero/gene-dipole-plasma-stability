from pathlib import Path
import csv
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

ROOT = Path(__file__).resolve().parent
BASE = ROOT / 'runs' / 'isotope_scan'
OUT = BASE / 'plots' / 'final_comparison'
OUT.mkdir(parents=True, exist_ok=True)
VALUES = [0, 0.5, 1, 2, 3, 4, 5]
N = len(VALUES)
QUALIFIED_OVERRIDE = {('deuterium', 0.0, 0.0)}


def index(row):
    return VALUES.index(float(row['omt'])), VALUES.index(float(row['omn']))


def read_data(isotope):
    rates = np.full((N, N), np.nan)
    kind = np.full((N, N), 'missing', dtype=object)
    with (BASE / f'{isotope}_results.csv').open(newline='') as f:
        for row in csv.DictReader(f):
            if row['status'] == 'CONVERGED' and row['gamma'].strip():
                j, i = index(row)
                rates[j, i] = float(row['gamma'])
                kind[j, i] = 'gene'
    with (BASE / 'energy_fit_results.csv').open(newline='') as f:
        for row in csv.DictReader(f):
            if row['isotope'] != isotope:
                continue
            j, i = index(row)
            if kind[j, i] == 'gene':
                raise ValueError(f'Unexpected overlap with GENE result: {isotope} {row}')
            rates[j, i] = float(row['gamma_last15'])
            key = (isotope, float(row['omn']), float(row['omt']))
            kind[j, i] = ('qualified' if row['fit_status'] == 'CONSISTENT'
                          or key in QUALIFIED_OVERRIDE else 'uncertain')
    return rates, kind

H, HK = read_data('hydrogen')
D, DK = read_data('deuterium')
counts = {name: int(np.count_nonzero(HK == name) + np.count_nonzero(DK == name))
          for name in ('gene', 'qualified', 'uncertain', 'missing')}
print('Data classifications:', counts)
assert counts == {'gene': 85, 'qualified': 6, 'uncertain': 7, 'missing': 0}, (
    'Unexpected classification counts; inspect the CSVs before plotting.')

# Both figure sets share scales, including the negative uniform-gradient estimates.
common_min = float(min(np.nanmin(H), np.nanmin(D)))
common_max = float(max(np.nanmax(H), np.nanmax(D)))
all_diffs = H - D
lim = max(0.1, float(np.nanmax(np.abs(all_diffs))))


def draw(matrix, kinds, title, filepath, difference=False, supplementary=False):
    fig, ax = plt.subplots(figsize=(9.2, 7.7))
    cmap = plt.get_cmap('coolwarm' if difference else 'viridis').copy()
    cmap.set_bad('#dedede')
    if difference:
        im = ax.imshow(matrix, origin='lower', cmap=cmap,
                       norm=TwoSlopeNorm(vmin=-lim, vcenter=0, vmax=lim))
    else:
        im = ax.imshow(matrix, origin='lower', cmap=cmap,
                       vmin=common_min, vmax=common_max)
    ax.set_xticks(range(N), [str(v) for v in VALUES])
    ax.set_yticks(range(N), [str(v) for v in VALUES])
    ax.set_xlabel('Density gradient (omn)')
    ax.set_ylabel('Temperature gradient (omt)')
    ax.set_title(title, fontsize=14, pad=12)
    for j in range(N):
        for i in range(N):
            value, kind = matrix[j, i], kinds[j, i]
            if not np.isfinite(value):
                label, color = 'N/C', '#222222'
            else:
                symbol = '*' if kind == 'qualified' else '†' if kind == 'uncertain' else ''
                label = f'{value:.2f}{symbol}'
                rgba = im.cmap(im.norm(value))
                luminance = 0.2126*rgba[0] + 0.7152*rgba[1] + 0.0722*rgba[2]
                color = '#101010' if luminance > 0.52 else 'white'
            ax.text(i, j, label, ha='center', va='center', color=color, fontsize=9)
    fig.colorbar(im, ax=ax, label=('Hydrogen − deuterium normalized growth rate'
                                  if difference else 'Normalized growth rate'))
    note = ('* Qualified free-energy fit  |  † Uncertain free-energy fit'
            if supplementary else '* Qualified free-energy fit  |  N/C No reliable estimate')
    fig.text(0.5, 0.024, note, ha='center', fontsize=9)
    fig.tight_layout(rect=[0, 0.045, 1, 1])
    fig.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close(fig)


def subset(rates, kinds, include_uncertain):
    values = rates.copy()
    if not include_uncertain:
        values[kinds == 'uncertain'] = np.nan
    return values


def difference_kinds(hk, dk):
    out = np.full((N, N), 'gene', dtype=object)
    out[(hk == 'qualified') | (dk == 'qualified')] = 'qualified'
    out[(hk == 'uncertain') | (dk == 'uncertain')] = 'uncertain'
    return out

for label, full in [('primary_validated', False), ('supplementary_exploratory', True)]:
    h = subset(H, HK, full)
    d = subset(D, DK, full)
    diff = h - d
    dkinds = difference_kinds(HK, DK)
    suffix = 'Exploratory: all fitted values' if full else 'Primary: qualified values only'
    draw(h, HK, f'Electron–Hydrogen Growth Rates — {suffix}',
         OUT / f'{label}_hydrogen.png', supplementary=full)
    draw(d, DK, f'Electron–Deuterium Growth Rates — {suffix}',
         OUT / f'{label}_deuterium.png', supplementary=full)
    draw(diff, dkinds, f'Isotope Difference (H − D) — {suffix}',
         OUT / f'{label}_difference.png', difference=True, supplementary=full)
    print(f'{label}: {np.isfinite(h).sum()} H cells, {np.isfinite(d).sum()} D cells, '
          f'{np.isfinite(diff).sum()} paired cells')

with (OUT / 'all_98_growth_rates_with_quality.csv').open('w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['isotope', 'omn', 'omt', 'gamma', 'classification', 'estimation_method'])
    for isotope, rates, kinds in [('hydrogen', H, HK), ('deuterium', D, DK)]:
        for j, omt in enumerate(VALUES):
            for i, omn in enumerate(VALUES):
                method = ('GENE eigenvalue' if kinds[j, i] == 'gene'
                          else 'last 15% total-free-energy log slope')
                writer.writerow([isotope, omn, omt, f'{rates[j, i]:.8f}',
                                 kinds[j, i], method])

print('Created six PNG heatmaps and a full results CSV in:', OUT.resolve())
