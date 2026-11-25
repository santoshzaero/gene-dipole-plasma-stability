#!/usr/bin/env python3
"""Write compact editable LaTeX tables and provenance from the analyzed runs."""
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from analyze import collect,csv_write
from run_experiments import ROOT,A,B


def value(v,spec):
    return f"{v:{spec}}" if v is not None else r"\textemdash"


def latex_table(name,cols,head,rr):
    file=ROOT/"LaTeX"/"tables"/f"{name}.tex"
    file.parent.mkdir(parents=True,exist_ok=True)
    lines=[r"\begin{tabular}{@{}"+cols+r"@{}}",r"\toprule",
           " & ".join(head)+r"\\",r"\midrule"]
    lines.extend(" & ".join(row)+r"\\" for row in rr)
    lines+= [r"\bottomrule",r"\end{tabular}"]
    file.write_text("\n".join(lines)+"\n")


def overlap(a,b,z):
    a=interp(a,z)
    b=interp(b,z)
    return abs(np.vdot(a,b))/(np.linalg.norm(a)*np.linalg.norm(b))


def interp(p,z):
    native=np.linspace(-1,1,len(p))
    return np.interp(z,native,p.real)+1j*np.interp(z,native,p.imag)


def stats(rows,fits,signals):
    results={r["case"]:r for r in rows if r["origin"]!="setup_attempt"}
    a_scan=[results[f"A_g{g:g}_h0".replace(".","p")] for g in [.2,.6,1,1.5]]
    late_a=[]
    for r in a_scan:
        windows=[f for f in fits if f["case"]==r["case"] and f["window"] in {"30-40","36-44","44-52"}]
        gamma=[f["gamma"] for f in windows]
        omega=[f["omega"] for f in windows]
        late_a.append(dict(case=r["case"],omn_D=r["omn_D"],mode=r["status"],
                           gamma_44_52=r["gamma_final_fit"],omega_44_52=r["omega_final_fit"],
                           gamma_span_min=min(gamma),gamma_span_max=max(gamma),omega_span_min=min(omega),omega_span_max=max(omega),
                           runtime_s=r["native_wall_s"]))
    csv_write("A_common_window_rates.csv",late_a)
    latex_table("adiabatic_rates","rrrrrl",
                [r"$\omega_{n,D}$",r"Fit $\widehat\gamma$",r"Fit $\widehat\omega_r$",r"$\widehat\gamma$ range","Wall (s)","Mode"],
                [[f"{a['omn_D']:g}",value(a["gamma_44_52"],"+.4f"),value(a["omega_44_52"],"+.4f"),
                  f"$[{a['gamma_span_min']:+.4f},\\ {a['gamma_span_max']:+.4f}]$",
                  value(a["runtime_s"],".1f"),"Unresolved"] for a in late_a])
    latex_table("adiabatic_hyp","rrr",
                [r"\texttt{hyp\_z}",r"$E/E_0$ at $\omega_{n,D}=0.6$",r"$E/E_0$ at $\omega_{n,D}=1.5$"],
                [[str(h)]+[value(results[f"A_base_g{g}_h4" if h==4 else f"A_g{g}_h{h}"]["energy_final_over_initial"],".5f")
                           for g in ("0p6","1p5")] for h in (4,2,1,0)])
    controls=[]
    for base,control,t_cmp in [("A_g1p5_h0","A_g1p5_h0_halfdt",52),
                               ("A_g1p5_h0_halfdt","A_g1p5_h0_nz48",52),
                               ("A_g1p5_h0_halfdt","A_g1p5_h0_nv96_halfdt",52),
                               ("B_g1","B_g1_z32",None),("B_g1","B_g1_halfdt",None),("B_g1","B_g1_halfdt_rkc2",None),("B_g2","B_g2_v64",None)]:
        if base not in results or control not in results or base not in signals or control not in signals:
            continue
        a,b=results[base],results[control]
        p,q=signals[base],signals[control]
        x=p["phi"][np.argmin(np.abs(p["t"]-t_cmp))] if t_cmp is not None else p["template"]
        y=q["phi"][np.argmin(np.abs(q["t"]-t_cmp))] if t_cmp is not None else q["template"]
        g0=a["gamma_final_fit"]
        w0=a["omega_final_fit"]
        g1=b["gamma_final_fit"]
        w1=b["omega_final_fit"]
        controls.append(dict(reference=base,test=control,grid_reference=f"{a['nz']}/{a['nv']}/{a['nw']}",
                             grid_test=f"{b['nz']}/{b['nv']}/{b['nw']}",dt_reference=a["dt_measured"],dt_test=b["dt_measured"],
                             gamma_fit_reference=g0,gamma_fit_test=g1,omega_fit_reference=w0,omega_fit_test=w1,
                             gamma_absolute_change=None if g0 is None or g1 is None else g1-g0,
                             omega_absolute_change=None if w0 is None or w1 is None else w1-w0,
                             complex_overlap=float(overlap(x,y,np.linspace(-1,1,129))),
                             profile_comparison_time=t_cmp,status=b["status"]))
    csv_write("grid_timestep_mode_comparisons.csv",controls)
    trial=[results.get("A_g1p5_h0"+suffix) for suffix in ("","_halfdt","_nz48","_nv96","_nv96_halfdt")]
    a_ctrl=[]
    for r in trial:
        if r is None:
            continue
        a_ctrl.append([f"{r['nz']}/{r['nv']}/{r['nw']}",value(r["dt_measured"],".6f"),
                       value(r["ion_recurrence"],".2f"),value(r["gamma_final_fit"],"+.4f"),
                       value(r["omega_final_fit"],"+.4f"),
                       "Rejected runaway" if r["status"].startswith("rejected") else "Unresolved" if r["status"].startswith("unresolved") else "Finite-time only"])
    latex_table("adiabatic_controls","rrrrrl",
                ["Grid",r"$\Delta\widehat t$",r"$\widehat t_{\rm rec,D}$",r"Fit $\widehat\gamma$",r"Fit $\widehat\omega_r$","Assessment"],a_ctrl)
    b_scan=sorted((r for r in results.values() if r["case"] in {"B_g0p5","B_g0p75","B_g1","B_g1p25","B_g1p5","B_g2"}),key=lambda x:x["omn_e"])
    b_table=[]
    for r in b_scan+[results["B_pure_D_g1"]]:
        qualified=r["status"].startswith("qualified IV")
        b_table.append([f"{r['omn_e']:.2f}",value(r["omn_He"],"g"),value(r["gamma_native"] if qualified else None,".3f"),
                        value(r["omega_native"] if qualified else None,"+.3f"),value(r["gamma_final_fit"],".4f"),
                        value(r["omega_final_fit"],"+.4f"),value(r["native_wall_s"],".1f"),
                        "Pure D control" if r["case"]=="B_pure_D_g1" else "Qualified" if qualified else "Unresolved"])
    latex_table("compensated","rrrrrrrl",
                [r"$\omega_{n,e}$",r"$\omega_{n,\rm He}$",r"Native $\widehat\gamma$",r"Native $\widehat\omega_r$",r"Fit $\widehat\gamma$",r"Fit $\widehat\omega_r$","Wall (s)","Mode"],b_table)
    b_ctrl=[]
    for c,label in [("B_g1_z32","1.00: $n_z=32$"),("B_g1_halfdt","1.00: half step, RKC1"),("B_g1_halfdt_rkc2","1.00: half step, RKC2"),("B_g2_v64","2.00: $n_v=64$")]:
        if c in results:
            r=results[c]
            compare=next((x for x in controls if x["test"]==c),{})
            b_ctrl.append([label,value(r["dt_measured"],".7f"),value(r["gamma_native"],".3f"),
                           value(r["omega_native"],"+.3f"),value(compare.get("complex_overlap"),".6f"),
                           value(r["native_wall_s"],".1f")])
    latex_table("compensated_controls","lrrrrr",
                ["Control",r"$\Delta\widehat t$",r"Native $\widehat\gamma$",r"Native $\widehat\omega_r$","Profile overlap","Wall (s)"],b_ctrl)
    cfg=[]
    for r in rows:
        p=ROOT/r["path"]
        for f in ("parameters","run.log","process.json","out/parameters.dat","out/omega.dat","out/field.dat","out/energy.dat","out/nrg.dat"):
            file=p/f
            if file.exists():
                with file.open("rb") as stream:
                    checksum=hashlib.file_digest(stream,"sha256").hexdigest()
                cfg.append(dict(case=r["case"],origin=r["origin"],file=str(file.relative_to(ROOT)),bytes=file.stat().st_size,sha256=checksum))
    csv_write("diagnostic_checksums.csv",cfg)
    process=[json.loads((ROOT/r["path"]/"process.json").read_text()) for r in rows if r["origin"] in {"new","setup_attempt"}]
    total=dict(new_iv_integrations=sum(r["origin"]=="new" for r in rows),
               invalid_setup_attempts=sum(r["origin"]=="setup_attempt" for r in rows),
               native_s_new=sum(r.get("native_wall_s") or 0 for r in rows if r["origin"]=="new"),
               summed_process_elapsed_s=sum(p["elapsed_s"] for p in process),
               summed_setup_elapsed_s=sum(r.get("process_s") or 0 for r in rows if r["origin"]=="setup_attempt"),
               first_start_to_last_exit_s=max(p["finished_epoch"] for p in process)-min(p["started_epoch"] for p in process))
    (ROOT/"Numerical_Results"/"runtime.json").write_text(json.dumps(total,indent=2)+"\n")
    first,last=b_scan[0],b_scan[-1]
    dg=100*(last["gamma_native"]/first["gamma_native"]-1)
    dw=100*(last["omega_native"]/first["omega_native"]-1)
    checked=[c for c in controls if c["test"].startswith("B_") and c["status"].startswith("qualified IV")]
    gv=max((abs(c["gamma_absolute_change"]/c["gamma_fit_reference"])*100 for c in checked),default=0)
    wv=max((abs(c["omega_absolute_change"]/c["omega_fit_reference"])*100 for c in checked),default=0)
    native_numerical_text=(
        r"\paragraph{Scope and runtime.} "
        f"Across the six qualified samples, growth increases from {first['gamma_native']:.3f} to {last['gamma_native']:.3f} ({dg:.1f}"+r"\%) "
        f"and signed frequency from $+{first['omega_native']:.3f}$ to $+{last['omega_native']:.3f}$ ({dw:.1f}"+r"\%). "
        f"The available numerical controls change the fitted rates by up to about {gv:.2f}"+r"\% in growth and "
        f"{wv:.3f}"+r"\% in frequency. The automatic spatial and velocity refinements also change the applied timestep. "
        "These changes are small compared with the contrast along the tested compensated path. "
        f"The new integrations totaled {total['native_s_new']/60:.2f} minutes of summed native wall time across {total['new_iv_integrations']} executions. "
        "Concurrent runs overlap in elapsed time. Exact inputs, checksums, full numerical diagnostics and additional figures accompany this report. "
        r"The installed GENE reference and comparison literature are recorded in the README."
    )
    (ROOT/"LaTeX"/"tables"/"summary_text.tex").write_text(native_numerical_text+"\n")


if __name__=="__main__":
    stats(*collect())
