#!/usr/bin/env python3
"""Audit saved IV follow-up runs and extract compact, traceable plot data."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re

import numpy as np
from scipy.stats import linregress

from recover_data import ROOT, REPORT, read_fields, write_rows

WORK = ROOT / 'work/deuterium_followup'
CONFIG = ROOT / 'configs/deuterium_followup'


def paths(gene_runs, work):
    for case, ky, name in [('ky_03_original', .3, 'ky_0p3'), ('ky_05_reference', .5, 'ky_0p5')]:
        yield case, 'low_ky', gene_runs / 'ky_scan/deuterium' / name, ROOT / 'configs/ky/deuterium' / name / 'parameters', 32, ky, 2, None
    for name in ('ky_03_fixed_dt', 'ky_03_fixed_dt_nz48'):
        directory = work / name
        if (directory / 'process.json').exists():
            yield name, 'low_ky', directory, CONFIG / name / 'parameters', 48 if name.endswith('nz48') else 32, .3, 2, None
    for suffix, ge, ghe in [('175',1.75,1), ('200',2,2), ('225',2.25,3)]:
        name = 'he_omn_e_' + suffix
        directory = work / name
        if (directory / 'process.json').exists():
            yield name, 'three_species', directory, CONFIG / name / 'parameters', 24, .7, ge, ghe


def required(pattern, text):
    found = re.search(pattern, text, re.M)
    if not found:
        raise ValueError(f'Metadata missing {pattern}')
    return found[1]


def species(text):
    groups = re.findall(r'(?ims)^\s*&species\b(.*?)^\s*/', re.sub(r'(?m)!.*$', '', text))
    return [tuple(float(required(rf'(?m)^{key}\s*=\s*([\dEe.+-]+)', group))
                  for key in ('dens','mass','charge','omn','omt','temp')) for group in groups]


def extract(case, group, directory, config, nz, ky, ge, ghe):
    raw = (directory / 'parameters').read_bytes()
    assert raw == config.read_bytes(), case
    out = directory / 'out'
    status = (directory / 'process.json').read_text() if (directory / 'process.json').exists() else '{}'
    log = (directory / 'run.log').read_text()
    metadata = (out / 'parameters.dat').read_text()
    assert required(r"^comp_type\s*=\s*'([^']+)'", metadata) == 'IV', case
    for key, value in {'nz0':nz,'nv0':48,'nw0':24 if group=='three_species' else 32,'nx0':1,'nky0':1,'n_fields':1,
                       'PRECISION':'DOUBLE','ENDIANNESS':'LITTLE','OMP_NUM_THREADS':1}.items():
        assert required(rf'^{key}\s*=\s*(\S+)',metadata) == str(value), (case,key)
    initial = species(raw.decode())
    actual = species(metadata)
    np.testing.assert_allclose(actual, initial, rtol=0, atol=1e-10, err_msg=case)
    if ghe is not None:
        assert actual == [(0.75,2,1,2,2,1),(1,.00054462,-1,ge,2,1),(.125,4,2,ghe,2,1)], case
    balance = sum(n*z for n,_,z,_,_,_ in actual)
    balance_g = sum(n*z*g for n,_,z,g,_,_ in actual)
    assert abs(balance)<1e-12 and abs(balance_g)<1e-12, case
    assert 'Violation of quasineutrality' not in log, case
    assert required(r'We have\s+(\d+) MPI tasks',log) == '1', case
    code_ky, native_g, native_w = np.loadtxt(out / 'omega.dat')
    assert code_ky==ky, case
    t, phi, records = read_fields(out / 'field.dat', nz)
    norm = np.linalg.norm(phi,axis=1)
    keep = norm>0
    t, phi, norm = t[keep], phi[keep], norm[keep]
    assert len(t)>10 and np.all(np.diff(t)>0),case
    last = phi[-1]/np.linalg.norm(phi[-1])
    projection = phi @ last.conj()
    phase = np.unwrap(np.angle(projection / projection[-1]))
    overlap = abs(projection) / norm
    log_norm = np.log(norm/norm[0])
    rescale_steps = np.flatnonzero(np.diff(log_norm)<-10)+1
    final_reset = int(rescale_steps[-1]) if len(rescale_steps) else 0
    energy_t, energy = np.loadtxt(out / 'energy.dat', usecols=(0,1)).T
    keep = np.isfinite(energy) & (energy>0)
    energy_t, energy = energy_t[keep], energy[keep]
    fits = []
    for label, i0, i1 in [('late', t[-1]-.5, t[-1]), ('earlier', t[-1]-1., t[-1]-.5),
                          ('last_10_steps', t[-11],t[-1])]:
        selection = (t>=i0)&(t<=i1)&(np.arange(len(t))>=final_reset)&(abs(projection)>0)
        if selection.sum()<8:
            continue
        tx = t[selection]
        g = linregress(tx,np.log(abs(projection[selection])))
        w = linregress(tx,phase[selection])
        fits.append(dict(case=case,window=label,start=tx[0],end=tx[-1],samples=len(tx),
                         gamma=g.slope,omega=w.slope,growth_r2=g.rvalue**2,phase_r2=w.rvalue**2,
                         min_overlap=min(overlap[selection]),
                         phase_residual_rms=np.sqrt(np.mean((phase[selection]-w.intercept-w.slope*tx)**2))))
    previous = phi[-11]
    mask = np.abs(previous) > np.finfo(float).eps
    interval = t[-1] - t[-11]
    weights = np.abs(previous[mask])
    weighted_rate = np.average(np.log(phi[-1,mask]/previous[mask])/interval, weights=weights)
    node_phase = np.unwrap(np.angle(phi[-11:,mask]), axis=0)
    weighted_unwrapped = np.average((node_phase[-1]-node_phase[0])/interval, weights=weights)
    spatial = [dict(case=case,s=s,real=z.real,imag=z.imag) for s,z in zip(np.linspace(0,1,nz),last/max(abs(last)))]
    traces = [dict(case=case,time=ti,log_field_norm=an,phase=ph,template_overlap=ov)
              for ti,an,ph,ov in zip(t,log_norm,phase,overlap)]
    energies = [dict(case=case,time=ti,energy_ratio=we) for ti,we in zip(energy_t,energy/energy[0])]
    summary = dict(case=case,group=group,input=config.relative_to(ROOT).as_posix(),ky=ky,nz=nz,nv=48,
                   nw=24 if ghe is not None else 32,omn_e=ge,omn_d=2,omn_he=ghe,qn=balance,qn_gradient=balance_g,
                   dt=np.median(np.diff(t)),end_time=t[-1],field_records=records,
                   steps=int(required(r'Computed\s+(\d+) time steps',log)),
                   gene_flag='Linear growth rate is converged' in log,log_rescales=log.count('rescaled amplitudes'),
                   detected_field_jumps=len(rescale_steps),gamma=native_g,omega=native_w,
                   raw_logratio_gamma=weighted_rate.real,raw_logratio_omega=weighted_rate.imag,
                   same_window_unwrapped_omega=weighted_unwrapped,
                   roughness=np.linalg.norm(np.diff(last)),
                   wall_s=float(required(r'Total wallclock time for GENE:\s+([\d.]+)',log)),
                   returncode=json.loads(status).get('returncode'),sha256_input=hashlib.sha256(raw).hexdigest())
    digests = [dict(case=case,file=name,sha256=hashlib.sha256((directory/name).read_bytes()).hexdigest())
               for name in ('parameters','run.log','out/omega.dat','out/parameters.dat','out/field.dat','out/energy.dat')]
    return summary,fits,spatial,traces,energies,digests


def compare(profiles):
    z = defaultdict(list)
    for row in profiles:
        z[row['case']].append(complex(row['real'],row['imag']))
    results=[]
    for name, raw in z.items():
        check='he_omn_e_200' if name.startswith('he_') else 'ky_05_reference'
        references = [check] if not name.endswith('nz48') else [check,'ky_03_fixed_dt']
        for ref in references:
            if name==ref or ref not in z:
                continue
            p,q=np.asarray(raw),np.asarray(z[ref]); grid=np.linspace(0,1,241)
            if p.size!=q.size:
                p=np.interp(grid,np.linspace(0,1,p.size),p)
                q=np.interp(grid,np.linspace(0,1,q.size),q)
            similarity=abs(np.vdot(p,q))/(np.linalg.norm(p)*np.linalg.norm(q))
            results.append(dict(case=name,reference=ref,overlap=similarity))
    return results


def common_window(results):
    cases = ('ky_03_fixed_dt', 'ky_03_fixed_dt_nz48')
    series = {r[0]['case']: r[3] for r in results if r[0]['case'] in cases}
    if len(series) != len(cases):
        return []
    end = min(rows[-1]['time'] for rows in series.values())
    fits = []
    for case, rows in series.items():
        t, logged, phase, overlap = np.array([[r[k] for k in ('time','log_field_norm','phase','template_overlap')]
                                               for r in rows if end-.5<=r['time']<=end]).T
        gamma = linregress(t,logged+np.log(overlap)).slope
        omega = linregress(t,phase).slope
        fits.append(dict(case=case,start=t[0],end=t[-1],gamma=gamma,omega=omega,min_overlap=min(overlap)))
    return fits


def main(gene_runs, work, dest):
    results=[extract(*case) for case in paths(gene_runs,work)]
    dest.mkdir(parents=True,exist_ok=True)
    for i,name in enumerate(('runs.csv','fits.csv','profiles.csv','field_history.csv.gz','energy_history.csv.gz','hashes.csv')):
        rows=[record[0] for record in results] if i==0 else [row for record in results for row in record[i]]
        write_rows(dest/f'followup_{name}',rows)
    comparisons=compare(row for record in results for row in record[2])
    write_rows(dest/'followup_overlaps.csv',comparisons)
    matched = common_window(results)
    if matched:
        write_rows(dest/'followup_common_fits.csv',matched)
    print(f'Audited {len(results)} saved IV runs.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs',type=Path,required=True)
    parser.add_argument('--work',default=WORK,type=Path)
    parser.add_argument('--data',default=REPORT/'data',type=Path)
    args=parser.parse_args()
    main(args.runs,args.work,args.data)
