#!/usr/bin/env python3
"""Check the report's selections, raw-field fits, and archived energy estimates."""
from collections import Counter

import numpy as np

from make_figures import DATA, histories, profiles, rows, scan_points


def main():
    inputs = rows('input_inventory')
    for record in inputs:
        if record['solver'] == 'IV' and record['species'] == '2' and record['masses']:
            masses = sorted(float(m.replace('D', 'E')) for m in record['masses'].split(';'))
            if np.allclose(masses, [.00054462, 2], rtol=1e-8, atol=0):
                assert len(set(float(n) for n in record['omn'].split(';'))) == 1, record
    matrix, density = scan_points()
    active = [((g, k), record) for (g, k), record in sorted(matrix.items()) if record['qualified'] == 'True']
    assert len(active) == 13
    for g in (1, 2, 3):
        records = [r for (grad, _), r in active if grad == g]
        assert all(r['solver'] == 'IV' and float(r['omt']) == 2 and r['rescalings'] == '0' for r in records)
        assert np.all(np.diff([float(r['gamma']) for r in records]) < 0)
        assert np.all(np.diff([float(r['omega']) for r in records]) > 0)
        assert all(float(r['omega']) > 0 for r in records)
    cut = [r for (_, k), r in sorted(density.items()) if k == .7 and r['qualified'] == 'True']
    slopes = np.diff([float(r['gamma']) for r in cut]) / np.diff([float(r['omn']) for r in cut])
    assert np.all(slopes > 0) and np.all(np.diff(slopes) < 0)

    energy = histories()
    original_fits = rows('isotope_fit')
    assert len(original_fits) == 13
    for r in original_fits:
        omn, omt = (f'{float(r[key]):g}'.replace('.', 'p') for key in ('omn', 'omt'))
        t, w = energy[f"{r['isotope']}_omn_{omn}_omt_{omt}"]
        for percent in (50, 30, 15):
            j = int(len(t) * (1 - percent / 100))
            fitted = np.polyfit(t[j:], np.log(w[j:]), 1)[0] / 2
            np.testing.assert_allclose(fitted, float(r[f'gamma_last{percent}']), atol=1e-12, rtol=0)
    assert Counter(r['classification'] for r in rows('isotope_quality')) == {
        'gene': 85, 'qualified': 6, 'uncertain': 7,
    }

    stored = rows('closure_time_series.csv.gz')
    fits = [r for r in rows('phase2_fits') if r['case'].endswith('collisionless')]
    assert len(fits) == 7
    for r in fits:
        t, a, p = np.array([[float(x[key]) for key in ('time', 'relative_amplitude', 'phase')]
                             for x in stored if x['case'] == r['case']]).T
        selected = (t >= float(r['start'])) & (t <= float(r['end']))
        np.testing.assert_equal(selected.sum(), int(r['samples']))
        gamma = np.polyfit(t[selected], np.log(a[selected]), 1)[0]
        omega = np.polyfit(t[selected], p[selected], 1)[0]
        np.testing.assert_allclose([gamma, omega], [float(r['gamma']), float(r['omega'])], rtol=0, atol=1e-12)
    phase_data = rows('pair_projection')
    z = np.array([complex(float(r['projection_real']), float(r['projection_imag'])) for r in phase_data])
    np.testing.assert_allclose(np.unwrap(np.angle(z / z[-1])), 0, atol=1e-14, rtol=0)
    p = profiles()
    for case, ref, expected in [('omn_2_ky_0p3', 'matrix_2_0p5', .00155937178),
                                ('kinetic_collisionless', 'adiabatic_collisionless', .990518681)]:
        s, a = p[case]
        sr, b = p[ref]
        common = np.linspace(0, 1, 241) if case.endswith('collisionless') else s
        a, b = np.interp(common, s, a), np.interp(common, sr, b)
        rate = abs(np.vdot(a, b)) / (np.linalg.norm(a) * np.linalg.norm(b))
        np.testing.assert_allclose(rate, expected, atol=1e-8, rtol=0)
    print('Verified 13 qualified scan points, 39 energy-window refits, 7 closure fits, pair phase, and field overlaps.')
    if (DATA / 'followup_runs.csv').exists():
        verify_followup()


def verify_followup():
    cases = {r['case']:r for r in rows('followup_runs')}
    original = cases['ky_03_original']
    assert int(original['log_rescales']) == int(original['detected_field_jumps']) == 29
    np.testing.assert_allclose(float(original['raw_logratio_omega']),float(original['omega']),rtol=0,atol=.0005)
    np.testing.assert_allclose(float(original['raw_logratio_gamma']),float(original['gamma']),rtol=0,atol=.0005)
    phase = float(original['same_window_unwrapped_omega'])
    alias = phase + 3*2*np.pi/(10*float(original['dt']))
    np.testing.assert_allclose(alias,float(original['raw_logratio_omega']),rtol=0,atol=1e-8)
    helium = sorted((r for r in cases.values() if r['group']=='three_species'),key=lambda r:float(r['omn_e']))
    assert len(helium)==3
    for r in helium:
        assert r['gene_flag']=='True' and r['log_rescales']=='0'
        assert float(r['qn'])==float(r['qn_gradient'])==0
        assert float(r['omn_e'])==.75*2+.25*float(r['omn_he'])
    for rate in ('gamma','omega'):
        assert np.all(np.diff([float(r[rate]) for r in helium])>0)
    fits = rows('followup_common_fits')
    case_names = ('ky_03_fixed_dt', 'ky_03_fixed_dt_nz48')
    assert tuple(fit['case'] for fit in fits) == case_names
    for case in case_names:
        result = cases[case]
        assert result['gene_flag'] == 'True' and result['log_rescales'] == '0'
        assert result['detected_field_jumps'] == '0'
        np.testing.assert_allclose(float(result['dt']), .0004175, rtol=0, atol=1e-13)
    coarse, refined = fits
    assert (coarse['start'], coarse['end']) == (refined['start'], refined['end'])
    differences = [100 * abs(float(refined[key]) / float(coarse[key]) - 1) for key in ('gamma', 'omega')]
    np.testing.assert_allclose(differences, [0.123, 0.022], rtol=0, atol=.0005)
    matched_overlap = next(r for r in rows('followup_overlaps')
                           if (r['reference'], r['case']) == case_names)
    assert float(matched_overlap['overlap']) > .99999999
    print('Verified compensated gradients, pilot trend, native phase alias, and matched low-wavenumber controls.')


if __name__ == '__main__':
    main()
