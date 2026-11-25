#!/usr/bin/env python3
"""Read completed IV fields, fit complex projections and audit native diagnostics."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re

import numpy as np

from archived_field_reader import read_fields
from run_experiments import A, B, ROOT, get_fields

OUT=ROOT/"Numerical_Results"
A_WINDOWS=((10,20),(20,30),(30,40),(40,47),(47,53),(36,44),(44,52),(54,64),(64,74))
A_CHECK=((36,44),(44,52))


def csv_write(name, records):
    if records:
        with (OUT/name).open("w",newline="") as stream:
            writer=csv.DictWriter(stream,fieldnames=list(dict.fromkeys(k for row in records for k in row)))
            writer.writeheader()
            writer.writerows(records)


def fit_slope(time, y):
    fit=np.polyfit(time,y,1)
    residue=np.sqrt(np.mean((y-np.polyval(fit,time))**2))
    return float(fit[0]),float(residue)


def energy_data(path):
    # Column 14's initial derivative can contain Inf; the native energy and
    # analytic balance occupy only columns 1–9 of this writer.
    if not path.exists() or not path.stat().st_size:
        return np.empty((0,9))
    e=np.atleast_2d(np.loadtxt(path,usecols=tuple(range(9))))
    e=e[np.isfinite(e).all(axis=1)&(e[:,1]>0)]
    return e[np.r_[np.diff(e[:,0])>0,True]] if len(e) else e


def parse_run(path, stage):
    out=path/"out"
    text=(path/"parameters").read_text()
    fields=get_fields(text)
    metadata=get_fields((out/"parameters.dat").read_text()) if (out/"parameters.dat").exists() else {}
    log=(path/"run.log").read_text()
    process=json.loads((path/"process.json").read_text()) if (path/"process.json").exists() else {}
    species=[get_fields(x) for x in re.findall(r"(?ms)^&species\b.*?^/",text)]
    inputs={x["name"].strip("'"):float(x["omn"]) for x in species}
    native=None
    omega_path=out/"omega.dat"
    if omega_path.is_file() and omega_path.stat().st_size:
        vals=np.loadtxt(omega_path).ravel()
        if len(vals)==3:
            native=vals
    native_flag="Linear growth rate is converged, exiting time loop" in log
    runtime=re.search(r"Total wallclock time for GENE:\s+([\d.]+)",log)
    steps=re.search(r"Computed\s+(\d+) time steps",log)
    recurrence=dict((k,float(v)) for k,v in re.findall(r"(?m)^\*\* (deuterium|ions|electrons|helium)\s*:\s*([\d.]+)",log))
    nz,nv,nw=[int(fields[x]) for x in ("nz0","nv0","nw0")]
    setup_match=all(metadata.get(key)==fields[key] for key in ("nz0","nv0","nw0","comp_type")) if metadata else False
    closure=("Electrons are adiabatic" in log if len(species)==1 else "Kinetic electrons and ions" in log)
    row=dict(case=path.name,origin=stage,nz=nz,nv=nv,nw=nw,n_spec=len(species),
             omn_D=inputs.get("deuterium",inputs.get("ions")),omn_e=inputs.get("electrons"),omn_He=inputs.get("helium"),
             hyp_z=float(fields.get("hyp_z",0)),dt_mode="automatic" if fields["calc_dt"]=="T" else "fixed",
             dt_input=float(fields["dt_max"]) if "dt_max" in fields else None,
             coll=float(fields["coll"]),closure_checked=closure,input_setup_matches_native=setup_match,
             steps=int(steps[1]) if steps else None,convergence_flag=native_flag,
             native_wall_s=float(runtime[1]) if runtime else None,process_s=process.get("elapsed_s"),
             returncode=process.get("returncode"),early_stop=process.get("early_stop"),rescalings=log.lower().count("rescaled amplitudes"),
             requested_timestep_ok=None,ion_recurrence=recurrence.get("deuterium",recurrence.get("ions")),
             electron_recurrence=recurrence.get("electrons"),helium_recurrence=recurrence.get("helium"),
             gamma_native=None,omega_native=None, gamma_final_fit=None,omega_final_fit=None,
             input_sha256=hashlib.sha256(text.encode()).hexdigest(), path=str(path.relative_to(ROOT)))
    if native is not None:
        row.update(omega_file_gamma_raw=float(native[1]),omega_file_omega_raw=float(native[2]))
    if native_flag and native is not None and native[0]==.7 and np.isfinite(native).all() and np.any(native[1:]!=0):
        row.update(gamma_native=float(native[1]),omega_native=float(native[2]))
    if stage=="setup_attempt":
        row["status"]=("invalid input setup (omitted collision bound); excluded" if row["n_spec"]==3 else "invalid input setup (subnormal timestep); excluded")
        row["requested_timestep_ok"]=False
        return row,[],None
    e=energy_data(out/"energy.dat")
    if not (out/"field.dat").exists() or not (out/"field.dat").stat().st_size:
        row["status"]="unresolved; no readable complex field"
        return row,[],None
    try:
        t,phi,total_records=read_fields(out/"field.dat",nz)
    except ValueError as err:
        row["status"]=f"unresolved; {err}"
        return row,[],None
    if len(t)<12:
        row["status"]="unresolved; insufficient field samples"
        return row,[],None
    dt=float(np.median(np.diff(t)))
    dt_ok=(dt>1e-10 and (row["dt_input"] is None or np.isclose(dt,row["dt_input"],rtol=1e-7,atol=1e-12)))
    row.update(dt_measured=dt,end_time=float(t[-1]),field_records=total_records,requested_timestep_ok=bool(dt_ok))
    is_a=len(species)==1
    end=float(t[-1])
    ref_limit=min(end,.94*row["ion_recurrence"]) if is_a and row["ion_recurrence"] else end
    i_ref=np.searchsorted(t,min(ref_limit,52) if is_a else ref_limit,side="right")-1
    ref=phi[i_ref]
    template=ref/ref[np.argmax(np.abs(ref))]
    dot=phi@template.conj()
    norm=np.linalg.norm(phi,axis=1)
    proj=dot/np.vdot(template,template).real
    max_norm=norm.max()
    bounded=(norm>max_norm*1e-14)&(np.abs(proj)>np.abs(proj).max()*1e-14)
    baseline=np.abs(proj[bounded][0])
    phase=np.unwrap(np.angle(proj))
    phase=phase-phase[0]
    overlap=np.minimum(np.abs(dot)/np.maximum(norm*np.linalg.norm(template),1e-300),1)
    spec=np.abs(np.fft.fft(template))**2
    k=np.abs(np.fft.fftfreq(nz))
    high_k=float(spec[k>=.375].sum()/spec.sum())
    if is_a:
        windows=[(f"{l:g}-{u:g}",l,u) for l,u in A_WINDOWS if u<ref_limit]
    else:
        width=min(.6,end*.35)
        windows=[("earlier",end-width*1.5,end-width*.5),("late",end-width,end),("last-half",end-width*.5,end)]
    fits=[]
    for label,l,u in windows:
        keep=bounded&(t>=l)&(t<=u)
        if keep.sum()<12:
            continue
        tt=t[keep]
        gamma,lrms=fit_slope(tt,np.log(np.abs(proj[keep])))
        omega,prms=fit_slope(tt,phase[keep])
        max_jump=float(np.max(np.abs(np.angle(proj[keep][1:]/proj[keep][:-1]))))
        fits.append(dict(case=path.name,origin=stage,window=label,t_first=float(tt[0]),t_last=float(tt[-1]),
                         n=int(keep.sum()),gamma=gamma,omega=omega,overlap_min=float(overlap[keep].min()),
                         overlap_median=float(np.median(overlap[keep])),log_amplitude_rms=lrms,
                         phase_rms=prms,max_phase_increment=max_jump))
    row.update(template_time=float(t[i_ref]),max_high_k_fraction=high_k)
    good=dt_ok and row["returncode"] in (None,0) and not row["early_stop"] and not row["rescalings"] and closure and setup_match
    if is_a:
        if len(e):
            row["energy_peak_ratio"]=float(e[:,1].max()/e[0,1])
        local=[f for f in fits if f["window"] in {"36-44","44-52"}]
        row["status"]="unresolved; finite-time fits are window-dependent"
        if len(local)==2:
            f=local[-1]
            row.update(gamma_final_fit=f["gamma"],omega_final_fit=f["omega"],
                       gamma_fit_min=min(x["gamma"] for x in local),gamma_fit_max=max(x["gamma"] for x in local),
                       omega_fit_min=min(x["omega"] for x in local),omega_fit_max=max(x["omega"] for x in local))
            if (good and all(x["overlap_min"]>=.99 and x["log_amplitude_rms"]<.015 and x["phase_rms"]<.03 for x in local)
                and abs(local[0]["gamma"]-f["gamma"])<=max(.0005,.05*abs(f["gamma"]))
                and abs(local[0]["omega"]-f["omega"])<=max(.001,.05*abs(f["omega"]))):
                row["status"]="qualified finite-time estimate; mode not established"
        elif len(local)==1:
            row.update(gamma_final_fit=local[0]["gamma"],omega_final_fit=local[0]["omega"])
            row["status"]="unresolved; one shared pre-recurrence window"
        if len(e)>1:
            use=e[e[:,0]<=min(52,e[-1,0])]
            if len(use)>1:
                final=use[-1]
                hyp=float(np.trapezoid(use[:,7],use[:,0]))
                change=float(final[1]-use[0,1])
                row.update(energy_audit_time=float(final[0]),energy_final_over_initial=float(final[1]/use[0,1]),
                           energy_delta=change,integrated_hyp_z=hyp,energy_hyp_residual=change-hyp,
                           peak_nonhyp_deriv=float(np.max(np.abs(use[:,2]-use[:,7]))))
        if (row.get("energy_peak_ratio",0)>2 and not np.any(e[:,3])):
            row["status"]="rejected numerical runaway; zero recorded drive"
            row["gamma_native"]=row["omega_native"]=None
    else:
        local=[f for f in fits if f["window"]=="last-half"]
        row["status"]="unresolved; native and independent checks incomplete"
        if local:
            f=local[0]
            row.update(gamma_final_fit=f["gamma"],omega_final_fit=f["omega"])
            if (good and high_k<.01 and row["gamma_native"] is not None
                    and abs(f["gamma"]-row["gamma_native"])<=.002
                    and abs(f["omega"]-row["omega_native"])<=.002
                    and all(x["overlap_min"]>=.995 and x["max_phase_increment"]<.2 and
                            abs(x["gamma"]-f["gamma"])<=.008 and abs(x["omega"]-f["omega"])<=.008 for x in fits)):
                row["status"]="qualified IV growing mode" if f["gamma"]>0 else "qualified IV damped mode"
    return row,fits,dict(t=t,phi=phi,phase=phase,amplitude=np.abs(proj)/baseline,
                         norm=norm,overlap=overlap,template=template,energy=e)


def collect():
    rows,fits,signals=[],[],{}
    for root in (A,B):
        cases=[(p,"new") for p in sorted((root/"Runs").glob("*")) if (p/"process.json").is_file()]
        cases += [(p,"archive") for p in sorted((root/"Archive").glob("*")) if (p/"source.json").is_file()]
        cases += [(p,"setup_attempt") for p in sorted((root/"Setup_Attempts").glob("*")) if (p/"process.json").is_file()]
        for case,stage in cases:
            row,case_fits,field=parse_run(case,stage)
            rows.append(row)
            fits.extend(case_fits)
            if field:
                signals[row["case"]]=field
    return rows,fits,signals


def publish_csv(rows,fits,signals):
    csv_write("all_runs.csv",rows)
    csv_write("field_fits.csv",fits)
    history=[]
    mode=[]
    for name,signal in signals.items():
        for t,amp,phase,overlap in zip(signal["t"],signal["amplitude"],signal["phase"],signal["overlap"]):
            history.append(dict(case=name,time=float(t),relative_projection_amplitude=float(amp),
                                unwrapped_phase=float(phase),template_overlap=float(overlap)))
        for z,phi in zip(np.linspace(-1,1,len(signal["template"])),signal["template"]):
            mode.append(dict(case=name,normalized_z=float(z),real=float(phi.real),imaginary=float(phi.imag),magnitude=float(abs(phi))))
    csv_write("complex_field_history.csv",history)
    csv_write("mode_profiles.csv",mode)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case",help="Show evidence for a single completed case")
    args=parser.parse_args()
    if args.case:
        candidates=[p for root in (A,B) for p in (root/"Runs"/args.case,root/"Archive"/args.case) if p.is_dir()]
        if not candidates:
            parser.error("case directory missing")
        p=candidates[0]
        row,fits,_=parse_run(p,"new" if p.parent.name=="Runs" else "archive")
        print(json.dumps({"result":row,"fits":fits},indent=2))
    else:
        rows,fits,signals=collect()
        publish_csv(rows,fits,signals)
        for row in rows:
            if row["origin"]!="setup_attempt":
                print(row["case"],row["status"],row.get("dt_measured"),
                      row["gamma_native"],row["omega_native"],row["gamma_final_fit"],row["omega_final_fit"])


if __name__=="__main__":
    main()
