#!/usr/bin/env python3
"""Rebuild the report's Matplotlib figures and compact LaTeX tables offline."""
import csv
import gzip
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from matplotlib.transforms import Bbox
import numpy as np

ROOT = Path(__file__).resolve().parent
DATA, FIGURES = ROOT / 'data', ROOT / 'figures'
BLUE, RED, GREEN, VIOLET, TAN = '#215c83', '#a44830', '#237868', '#73559a', '#9b741f'
COLORS = (BLUE, GREEN, RED, VIOLET, TAN)
GROWTH = r'Growth rate $\widehat\gamma$'
FREQ = r'Real frequency $\widehat\omega$'
KY = r'Binormal wavenumber $k_y\rho_{\mathrm{ref}}$'
OMN = r'Common density gradient $\mathrm{omn}$'
TIME = r'Normalized time $\widehat t$'
GRADIENTS = (0, .5, 1, 2, 3, 4, 5)
GRID = '#e6eaed'
DATE = datetime(2026, 11, 19, tzinfo=timezone.utc)

plt.rcParams.update({'font.family': 'serif', 'font.serif': ['STIXGeneral', 'DejaVu Serif'], 'mathtext.fontset': 'stix',
                     'font.size': 10, 'axes.labelsize': 10.5, 'axes.titlesize': 11, 'legend.fontsize': 9,
                     'axes.spines.top': False, 'axes.spines.right': False, 'axes.edgecolor': '#67727b',
                     'axes.linewidth': .65, 'xtick.major.size': 3, 'ytick.major.size': 3, 'pdf.fonttype': 42,
                     'ps.fonttype': 42, 'figure.facecolor': 'white', 'savefig.facecolor': 'white'})


def rows(name):
    path = DATA / (name if name.endswith('.gz') else f'{name}.csv')
    opener = gzip.open if path.suffix == '.gz' else open
    with opener(path, 'rt', newline='') as handle:
        return list(csv.DictReader(handle))


def axes_grid(ax):
    ax.set_axisbelow(True)
    ax.grid(color=GRID, linewidth=.65)


def pair_axes(xlabel, width=7.1, height=2.75, layout='constrained'):
    fig, ax = plt.subplots(1, 2, figsize=(width, height), layout=layout)
    for axis, ylabel in zip(ax, (GROWTH, FREQ)):
        axis.set(xlabel=xlabel, ylabel=ylabel)
        axis.yaxis.set_major_locator(MaxNLocator(5))
        axes_grid(axis)
    return fig, ax


def points(ax, x, y, label, color, marker='o', **options):
    return ax.plot(x, y, color=color, lw=1.55, marker=marker, ms=4.6, mew=.55, mec='white', label=label, **options)[0]


def save(fig, name):
    width, height = fig.get_size_inches()
    extent = Bbox.from_bounds(0, 0, width, height + .14)
    fig.text(.986, 1.005, 'GENE', ha='right', va='bottom', fontsize=7, color='#53606a')
    fig.savefig(FIGURES / f'{name}.pdf', bbox_inches=extent,
                metadata={'Title': name, 'CreationDate': DATE, 'ModDate': DATE})
    fig.savefig(FIGURES / f'{name}.png', bbox_inches=extent, dpi=360)
    plt.close(fig)


def grad_array(data):
    matrix = np.full((7, 7), np.nan)
    for r in data:
        if r['status'] == 'CONVERGED':
            matrix[GRADIENTS.index(float(r['omt'])), GRADIENTS.index(float(r['omn']))] = float(r['gamma'])
    return matrix


def heat(ax, array, title, cmap, clim):
    edges = np.arange(8) - .5
    image = ax.pcolormesh(edges, edges, np.ma.masked_invalid(array), shading='flat', cmap=cmap,
                          vmin=clim[0], vmax=clim[1], rasterized=False)
    ax.set_aspect('equal')
    ax.set_facecolor('#dadddf')
    ax.set(xticks=range(7), yticks=range(7), xticklabels=[f'{x:g}' for x in GRADIENTS],
           yticklabels=[f'{x:g}' for x in GRADIENTS], xlabel=r'Common $\mathrm{omn}$', title=title)
    ax.tick_params(length=0)
    return image


def vector_colorbar(fig, image, **options):
    scale = fig.colorbar(image, **options)
    scale.solids.set_rasterized(False)


def pair_scans():
    fig, axes = plt.subplots(1, 2, figsize=(7.1, 2.78), layout='constrained', gridspec_kw={'width_ratios': [1.05, 1]})
    ax, line = axes
    image = heat(ax, grad_array(rows('pair_grid')), 'Historical joint-gradient survey', 'viridis', (0, 8))
    ax.set_ylabel(r'Common temperature gradient $\mathrm{omt}$')
    vector_colorbar(fig, image, ax=ax, label=GROWTH, pad=.025, shrink=.88)
    scan = rows('pair_density')
    points(line, [float(r['omn']) for r in scan], [float(r['gamma']) for r in scan], None, BLUE)
    line.set(xlabel=OMN, ylabel=GROWTH, title=r'Density cut at $\mathrm{omt}=2$')
    axes_grid(line)
    save(fig, '01_pair_gradients')


def pair_benchmark():
    dataset = rows('pair_projection')
    t = np.array([float(row['time']) for row in dataset])
    z = np.array([complex(float(r['projection_real']), float(r['projection_imag'])) for r in dataset])
    peak = np.array([complex(float(r['peak_real']), float(r['peak_imag'])) for r in dataset])
    a, p = np.log(np.abs(z / z[-1])), np.unwrap(np.angle(z / z[-1]))
    peak_phase = np.unwrap(np.angle(peak / peak[-1]))
    late = t >= 1.46088
    fig, (amp, phase) = plt.subplots(1, 2, figsize=(7.1, 2.52), layout='constrained')
    amp.semilogy(t, np.exp(a), color=BLUE, lw=1.65, label='Field projection')
    amp.semilogy(t[late], np.exp(np.polyval(np.polyfit(t[late], a[late], 1), t[late])), '--', color=RED,
                 lw=1, label='Late exponential fit')
    phase.plot(t[late], p[late]*1e3, color=BLUE, lw=1.55, label='Field projection')
    phase.plot(t[late], peak_phase[late]*1e3, 'o', ms=3.2, markevery=5, mec=RED, mfc='white', mew=.75,
               label='Peak node')
    phase.set(ylim=(-.82, .82), yticks=[-.5, 0., .5], ylabel='Relative phase (mrad)')
    amp.set(ylabel=r'$|a(t)|/|a(t_{\mathrm{end}})|$')
    for ax in (amp, phase):
        ax.set_xlabel(TIME)
        axes_grid(ax)
        ax.legend(frameon=False)
    amp.set_title('Exponential amplification')
    phase.set_title('Temporal phase over the fit window')
    save(fig, '02_pair_benchmark')


def histories():
    traces = defaultdict(list)
    for r in rows('energy_histories.csv.gz'):
        traces[r['case']].append((float(r['time']), float(r['energy'])))
    return {name: np.asarray(trace).T for name, trace in traces.items()}


def energy_plot(ax, trace, label, color, linestyle='-'):
    t, energy = trace
    ax.semilogy(t, energy / energy[0], color=color, lw=1.35, ls=linestyle, label=label)
    axes_grid(ax)
    ax.set(xlabel=TIME, ylabel=r'Free energy $W(\widehat t)/W(0)$')


def pair_unresolved(traces):
    fig, ax = plt.subplots(figsize=(6.8, 2.84))
    fig.subplots_adjust(left=.115, right=.98, bottom=.31, top=.96)
    for key, label, color, style in zip(
        ('0_omt_0', '0_omt_0p5', '0_omt_1', '0p5_omt_0p5', '0p5_omt_1'),
        ('(0, 0)', '(0, 0.5)', '(0, 1)', '(0.5, 0.5)', '(0.5, 1)'), COLORS, ('-', '-', '-', '--', '--')):
        energy_plot(ax, traces[f'pair_extended_omn_{key}'], label, color, style)
    fig.legend(ncols=5, loc='lower center', bbox_to_anchor=(.55, .022), frameon=False)
    save(fig, '03_pair_unresolved_energy')


def isotope_maps():
    h, d = (grad_array(rows(f'isotope_{x}')) for x in ('hydrogen', 'deuterium'))
    fig, ax = plt.subplots(1, 3, figsize=(7.2, 2.39), layout='constrained')
    for axis, data, title in zip(ax[:2], (h, d), ('Hydrogen', 'Deuterium')):
        image = heat(axis, data, title, 'viridis', (0, np.ceil(np.nanmax([h, d]))))
    ax[0].set_ylabel(r'Common $\mathrm{omt}$')
    ax[1].tick_params(labelleft=False)
    ax[2].tick_params(labelleft=False)
    vector_colorbar(fig, image, ax=ax[:2], label=GROWTH, pad=.026, shrink=.83)
    diff = heat(ax[2], h-d, 'Hydrogen minus deuterium', 'magma', (0, 3.5))
    vector_colorbar(fig, diff, ax=ax[2], label=r'$\Delta\widehat\gamma$', pad=.023, shrink=.83)
    save(fig, '04_isotope_gradient_comparison')


def isotope_energy(traces):
    fig, ax = plt.subplots(figsize=(5.8, 2.38), layout='constrained')
    for key, label, color in [('deuterium_omn_0_omt_2',r'$\mathrm{omt}=2$ (qualified)',GREEN),
                              ('deuterium_omn_0_omt_1',r'$\mathrm{omt}=1$ (uncertain)',VIOLET)]:
        t, e = traces[key]
        energy_plot(ax, (t,e), label, color)
        start = int(.85 * len(t))
        fit = np.polyfit(t[start:],np.log(e[start:]/e[0]),1)
        ax.plot(t[start:],np.exp(np.polyval(fit,t[start:])),color='#853c16', lw=1.45, ls='--')
    ax.legend(frameon=False)
    save(fig, '05_isotope_fit_examples')
    fig, ax = plt.subplots(figsize=(5.4, 2.17), layout='constrained')
    for species, color in [('Hydrogen', RED), ('Deuterium', BLUE)]:
        energy_plot(ax, traces[f'{species.lower()}_omn_0_omt_0'], species, color)
    ax.legend(frameon=False)
    save(fig, '05_zero_gradient_energy')


def isotope_wave():
    fig, ax = pair_axes(KY)
    scan = rows('isotope_wavenumber')
    for name, color in [('hydrogen', RED), ('deuterium', BLUE)]:
        chosen = [r for r in scan if r['isotope'] == name and float(r['kymin']) >= .5 and r['status'] == 'CONVERGED']
        for axis, y in zip(ax, ('gamma', 'omega')):
            points(axis, [float(r['kymin']) for r in chosen], [float(r[y]) for r in chosen], name.title(), color)
            axis.set_xticks([.5, .7, 1, 1.5, 2])
    ax[0].legend(frameon=False)
    save(fig, '06_isotope_wavenumber')


def comparisons():
    z, = rows('z_comparison')
    data = {label: {r['comparison']: r for r in rows(f'{label}_comparison')} for label in ('step','v','mu','combined')}
    specs = [
        ('Parallel grid 32 vs 64', float(z['common_window_field_gamma_relative_difference_vs_nz64']),
         float(z['common_window_phase_omega_relative_difference_vs_nz64'])),
    ]
    for label, family, key in [
        ('Timestep at 32 parallel points','step','timestep'), ('Parallel grid 24 vs 32, fixed step','step','coarsen_24_32'),
        ('Parallel velocity 48 vs 64','v','parallel_velocity_48_64'), ('Parallel velocity 32 fixed vs 48','v','parallel_velocity_32_fixed_48'),
        ('Magnetic moment 32 vs 48','mu','magnetic_moment_32_48'), ('Magnetic moment 24 vs 32','mu','magnetic_moment_24_32'),
        ('Combined reduced vs original','combined','reduced_vs_original')]:
        r = data[family][key]
        specs.append((label, float(r['field_gamma_relative_difference']), float(r['phase_omega_relative_difference'])))
    return specs


def resolution():
    fig, axis = plt.subplots(figsize=(7.15, 3.25), layout='constrained')
    data = comparisons()
    y = np.arange(len(data))[::-1]
    for j, (label, color, marker) in enumerate([(r'Growth $\widehat\gamma$', BLUE, 'o'), (r'Real frequency $\widehat\omega$', RED, 'D')], start=1):
        axis.scatter([100*r[j] for r in data], y, label=label, s=32, color=color, marker=marker,
                     edgecolors='white', linewidths=.45, zorder=3)
    axis.axvline(1, color='#888f96', lw=.9, ls='--', label='1% comparison screen')
    axis.set(xscale='log', yticks=y, yticklabels=[r[0] for r in data], xlabel='Absolute relative difference (%)', xlim=(1e-5, 1.55))
    axes_grid(axis)
    axis.legend(frameon=False, loc='lower left', ncols=2)
    save(fig, '07_resolution_and_timestep')


def controls(traces):
    fig, axes = plt.subplots(2, 2, figsize=(7.1, 4.24), layout='constrained')
    for ax, panel in zip(axes[0], (
        [('nv32', r'$n_v=32$, auto', RED), ('nv32_fixed', r'$n_v=32$, fixed', GREEN), ('nv48', r'$n_v=48$, auto', BLUE)],
        [('extent', r'$L_\mu=16.25$, automatic', RED), ('extent_fixed', r'$L_\mu=16.25$, fixed', GREEN),
         ('reduced', r'$L_\mu=12.25$, automatic', BLUE)])):
        for key, label, color in panel:
            energy_plot(ax, traces[key], label, color)
    axes[0,0].legend(frameon=False, loc='upper right', fontsize=8)
    axes[0,1].legend(frameon=False, loc='upper right', fontsize=8)
    axes[0,0].set_title('Parallel-velocity stepping')
    axes[0,1].set_title('Magnetic-moment extent and stepping')
    record = rows('domain_comparison')
    a, b = record[0], record[2]
    cases = [('12.25\n(24)', a['field_gamma_reference'], a['phase_omega_reference']),
             ('16.25\n(24)', a['field_gamma_case'], a['phase_omega_case']),
             ('16.25\n(32)', b['field_gamma_case'], b['phase_omega_case'])]
    for j, (ax, ylabel) in enumerate(zip(axes[1], (GROWTH, FREQ)), start=1):
        vals = [float(r[j]) for r in cases]
        ax.scatter(range(3), vals, c=[BLUE,GREEN,VIOLET], s=32, zorder=3)
        margin = (max(vals)-min(vals))*.24
        ax.set(xticks=range(3), xticklabels=[r[0] for r in cases], xlabel=r'$L_\mu$ ($n_\mu$), fixed step',
               ylabel=ylabel, ylim=(min(vals)-margin,max(vals)+margin))
        ax.yaxis.set_major_locator(MaxNLocator(4))
        axes_grid(ax)
    save(fig, '08_velocity_and_domain_controls')


def profiles():
    data = defaultdict(list)
    for r in rows('field_profiles'):
        data[r['case']].append((float(r['s']), complex(float(r['real']), float(r['imag']))))
    return {key: (np.asarray([x for x, _ in seq]), np.asarray([z for _, z in seq])) for key, seq in data.items()}


def scan_points():
    meeting = rows('phase2_runs')
    matrix = {(float(r['omn']), float(r['kymin'])):r for r in meeting + rows('phase2_extension')
              if r['purpose'] in ('matrix', 'wavenumber')}
    density = {(float(r['omn']), float(r['kymin'])):r for r in meeting if r['purpose']=='density'}
    density.update(matrix)
    return matrix, density


def phase2_scans():
    matrix, density = scan_points()
    # The low-wavenumber control is admitted after both grids independently converge.
    if (DATA / 'followup_common_fits.csv').exists():
        controls = {r['case']:r for r in rows('followup_runs')}
        low = controls['ky_03_fixed_dt']
        fine = controls['ky_03_fixed_dt_nz48']
        if all(r['gene_flag']=='True' and r['log_rescales']=='0' for r in (low,fine)):
            matrix[(2.0,.3)] = low | {'qualified':'True'}
    for filename, data, xvals, curves, density_axis in (
        ('10_deuterium_wavenumber',matrix,(.3,.5,.7,1,1.5,2),(1,2,3),False),
        ('11_deuterium_density',density,(.5,1,2,3,4,5),(.5,.7,1,1.5),True)):
        fig, ax = pair_axes(OMN if density_axis else KY, height=2.9, layout=None)
        axes_handles = []
        for curve, color in zip(curves,COLORS):
            label = rf'$k_y\rho_{{\rm ref}}={curve:g}$' if density_axis else rf'$\mathrm{{omn}}={curve:g}$'
            selection = [data.get((x,curve) if density_axis else (curve,x)) for x in xvals]
            for axis, key in zip(ax, ('gamma','omega')):
                vals=[float(r[key]) if r and r['qualified']=='True' else np.nan for r in selection]
                handle = points(axis,xvals,vals,label,color)
                axis.set_xticks(xvals, [f'{x:g}' for x in xvals])
                if axis is ax[0]:
                    axes_handles.append(handle)
        # Reserve a single row below both panels for the shared legend.
        fig.subplots_adjust(left=.105, right=.98, top=.87, bottom=.30, wspace=.28)
        fig.legend(handles=axes_handles, loc='lower center', bbox_to_anchor=(.51,.015), ncols=len(curves), frameon=False)
        save(fig,filename)


def aligned(modes, key, reference):
    s, raw = modes[key]
    rs, r = modes[reference]
    grid = np.linspace(0,1,241)
    angle=np.angle(np.vdot(np.interp(grid,rs,r), np.interp(grid,s,raw))) + np.angle(r[0])
    z = raw * np.exp(-1j*angle)
    return s, np.abs(z), np.where(np.abs(z)>=.05,np.angle(z),np.nan)


def mode_fig(modes):
    ref = 'matrix_2_0p7'
    groups = [[(f'matrix_{n}_0p7',rf'$\mathrm{{omn}}={n}$',c) for n,c in zip((1,2,3),COLORS)],
              [(key,rf'$k_y\rho_{{\rm ref}}={ky:g}$',c) for key,ky,c in zip(
                  ('matrix_2_0p5',ref,'matrix_2_1','omn_2_ky_1p5','omn_2_ky_2'),(.5,.7,1,1.5,2),COLORS)]]
    for phase in (False, True):
        fig, axes = plt.subplots(1,2,figsize=(7.1,2.65))
        fig.subplots_adjust(left=.115, right=.988, bottom=.22, top=.70, wspace=.37)
        for col, (axis,group,title) in enumerate(zip(axes,groups,(r'Density at $k_y\rho_{\rm ref}=0.7$',r'Wavenumber at $\mathrm{omn}=2$'))):
            for (key,label,color), style in zip(group, ('-','--',':','-.','-')):
                x,a,p=aligned(modes,key,ref)
                axis.plot(x,p if phase else a,color=color,lw=1.5,label=label,ls=style)
            axis.set(title=title, xlabel=r'Field-line position $s/L_{\rm tube}$',
                     ylabel='Relative phase (rad)' if phase else r'Amplitude $|\phi|/\max|\phi|$')
            axes_grid(axis)
            handles, labels = axis.get_legend_handles_labels()
            fig.legend(handles, labels, frameon=False, fontsize=8, ncols=3, loc='upper center',
                       bbox_to_anchor=((.295,.793)[col], .985))
        save(fig,'12_mode_phase' if phase else '12_mode_amplitude')


def closure(modes):
    fig = plt.figure(figsize=(7.1,4.15), layout='constrained')
    grid=fig.add_gridspec(2,2,height_ratios=(.85,1.15))
    axes=[fig.add_subplot(grid[0,0]),fig.add_subplot(grid[0,1]),fig.add_subplot(grid[1,:])]
    treatments=[('kinetic_collisionless','Kinetic',BLUE),('adiabatic_collisionless','Adiabatic',RED)]
    controls={r['case']:r for r in rows('phase2_runs') if r['purpose']=='closure'}
    for axis, key, ylabel, lim in zip(axes,('gamma','omega'),(GROWTH,FREQ),((-.1,5.4),(-.15,1.27))):
        for ypos,(case,label,color) in zip((1,0),treatments):
            val=float(controls[case][key])
            axis.scatter(val,ypos,s=37,color=color,zorder=3)
            axis.annotate(f'{val:+.3f}' if key=='omega' else f'{val:.3f}',(val,ypos),xytext=(7,0),
                          textcoords='offset points',va='center',color=color)
        axis.set(xlim=lim,ylim=(-.48,1.48),yticks=(0,1),yticklabels=('Adiabatic','Kinetic'),xlabel=ylabel)
        axis.axvline(0,color='#89939c',lw=.75)
        axes_grid(axis)
        axis.yaxis.grid(False)
    for case,label,color in treatments:
        s,amp,_=aligned(modes,case,treatments[0][0])
        axes[2].plot(s,amp,color=color,lw=1.55,label=label)
    axes[2].set(xlabel=r'Field-line coordinate $s/L_{\rm tube}$',ylabel=r'$|\phi|/\max |\phi|$')
    axes_grid(axes[2]);axes[2].legend(frameon=False,loc='lower center',ncols=2)
    save(fig,'13_electron_response')


def followup_figures():
    records = rows('followup_runs')
    helium = sorted([r for r in records if r['group']=='three_species'],key=lambda r:float(r['omn_e']))
    if helium:
        fig, axes = pair_axes(r'Electron density gradient $\mathrm{omn}_e$',height=2.4)
        for axis,key in zip(axes,('gamma','omega')):
            values = [float(r[key]) if r['gene_flag']=='True' and r['log_rescales']=='0' else np.nan for r in helium]
            om = [float(r['omn_e']) for r in helium]
            points(axis,om,values,None,GREEN)
            axis.set_xticks(om, [f'{value:g}' for value in om])
        save(fig,'15_compensated_electron_gradient')
    energy, fields = defaultdict(list), defaultdict(list)
    for r in rows('followup_energy_history.csv.gz'):
        energy[r['case']].append((float(r['time']),float(r['energy_ratio'])))
    for r in rows('followup_profiles'):
        fields[r['case']].append((float(r['s']),abs(complex(float(r['real']),float(r['imag'])))))
    cases = [('ky_03_original',r'$n_z=32$, automatic',RED),('ky_03_fixed_dt',r'$n_z=32$, half step',BLUE),
             ('ky_03_fixed_dt_nz48',r'$n_z=48$, half step',GREEN)]
    fig, axes = plt.subplots(1,2,figsize=(7.1,2.65))
    fig.subplots_adjust(left=.122,right=.98,bottom=.31,top=.89,wspace=.36)
    for case,label,color in cases:
        if case in energy:
            axes[0].semilogy(*np.array(energy[case]).T, color=color, lw=1.15, label=label)
            axes[1].plot(*np.array(fields[case]).T, color=color, lw=1.3)
    axes[0].set(title='Recorded energy diagnostic',xlabel=TIME,ylabel=r'Free energy $W(\widehat t)/W(0)$')
    axes[1].set(title='Final field envelope',xlabel=r'Field-line position $s/L_{\rm tube}$',ylabel=r'$|\phi|/\max|\phi|$')
    for axis in axes: axes_grid(axis)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles,labels,frameon=False,ncols=3,loc='lower center',bbox_to_anchor=(.54,.025))
    save(fig,'16_low_wavenumber_controls')


def reference_settling():
    fig, (omega, shape) = plt.subplots(1, 2, figsize=(7.1, 2.62), layout='constrained')
    for n, color in [(32, BLUE), (64, RED)]:
        t, phase, overlap = np.loadtxt(DATA / f'field_nz{n}.csv.gz', delimiter=',', skiprows=1,
                                       usecols=(0, 2, 3)).T
        i = np.flatnonzero((t >= 1.23) & (t <= t[-1] - .1))[::5]
        j = np.searchsorted(t, t[i] + .1)
        rate = (phase[j] - phase[i]) / (t[j] - t[i])
        omega.plot((t[j] + t[i]) / 2, rate, color=color, lw=1.15, label=rf'$n_z={n}$')
        residual = 1 - overlap
        use = residual > 0
        shape.semilogy(t[use], residual[use], color=color, lw=1.25)
    omega.axhline(.946, color='#8895a2', lw=.8, ls='--', label='Native output')
    omega.set(ylabel=FREQ, title='Late-window phase slope')
    shape.set(ylabel=r'$1-\mathcal{O}(\phi(t),\phi_{\rm end})$', title='Departure from final shape')
    for ax in (omega, shape):
        ax.set_xlabel(TIME)
        axes_grid(ax)
    omega.legend(frameon=False)
    save(fig, '14_reference_field_settling')


def tables():
    matrix, _ = scan_points()
    body = []
    for (g,k),r in sorted(matrix.items()):
        if r['qualified']=='True':
            body.append(f"{g:g} & {k:g} & {float(r['gamma']):.3f} & ${float(r['omega']):+.3f}$ & ${r['nz']}\\times48\\times{r['nw']}$"+r' \\')
    (DATA/'matrix_rows.tex').write_text(r'\newcommand{\matrixrows}{%'+'\n'+'\n'.join(body)+'%\n}\n')
    quality={(r['isotope'],float(r['omn']),float(r['omt'])):r['classification'] for r in rows('isotope_quality')}
    fits = []
    for r in rows('isotope_fit'):
        key=(r['isotope'],float(r['omn']),float(r['omt']))
        rates=' & '.join(f"${float(r[f'gamma_last{j}']):+.4f}$" for j in (50,30,15))
        fits.append(f'{key[0].title()} & {key[1]:g} & {key[2]:g} & {rates} & {quality[key].title()}'+r' \\')
    (DATA/'energy_fit_rows.tex').write_text(r'\newcommand{\energyfitrows}{%'+'\n'+'\n'.join(fits)+'%\n}\n')


if __name__=='__main__':
    FIGURES.mkdir(exist_ok=True)
    t,m=histories(),profiles()
    pair_scans(); pair_benchmark(); pair_unresolved(t); isotope_maps(); isotope_energy(t); isotope_wave()
    resolution(); controls(t); phase2_scans(); mode_fig(m); closure(m); reference_settling(); tables()
    if (DATA / 'followup_runs.csv').exists():
        followup_figures()
