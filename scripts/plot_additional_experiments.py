#!/usr/bin/env python3
"""Regenerate the ten additional-experiment figures from committed diagnostic extracts."""
import argparse
import csv
import gzip
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "results/additional_experiments"
GRADIENTS=(.2,.6,1,1.5)
COLOR=("#286487","#aa513b","#40836a","#6e528a","#936e30","#3c4d59")
GAMMA=r"Normalized growth rate $\widehat{\gamma}$"
OMEGA=r"Signed real frequency $\widehat{\omega}_r$"
T=r"Normalized time $\widehat{t}$"
A_X=r"Kinetic deuterium density gradient $\omega_{n,D}$"
B_X=r"Electron density gradient $\omega_{n,e}$"

plt.rcParams.update({"font.family":"DejaVu Sans","font.size":11,"axes.spines.top":False,
                     "axes.spines.right":False,"axes.grid":True,"grid.color":"#dce4e8",
                     "grid.linewidth":.65,"axes.axisbelow":True,"pdf.fonttype":42})


def save(fig,output,name):
    for ext in ("pdf","png"):
        fig.savefig(output/f"{name}.{ext}",dpi=330,bbox_inches="tight",facecolor="white")
    plt.close(fig)


def legend(fig, handles, columns=4):
    fig.legend(handles=handles,loc="outside lower center",ncols=columns,frameon=False,fontsize=9)


def pair(xlabel, ylabels):
    fig,axes=plt.subplots(1,2,figsize=(10.7,4.25),layout="constrained")
    for ax,y in zip(axes,ylabels):
        ax.set(xlabel=xlabel,ylabel=y)
    return fig,axes


def adiabatic_cases(rows,hyp):
    candidates={r["case"]:r for r in rows if r["origin"]=="new"}
    return [candidates[f"A_g{g:g}_h{hyp}".replace(".","p")] for g in GRADIENTS]


def a_rates(rows, fits, hyp,output):
    selected=adiabatic_cases(rows,hyp)
    fig,axes=pair(A_X,(GAMMA,OMEGA))
    fig.suptitle(r"Zero temperature gradients with adiabatic electrons ($\mathrm{hyp\_z}="+str(hyp)+r"$)")
    refs=[Line2D([],[],color=COLOR[0],marker="o",mfc="none",ls="",label="Unresolved mode; finite-time slope"),
          Line2D([],[],color=COLOR[3],marker="s",ls="",label="Qualified finite-time response"),
          Line2D([],[],color=COLOR[1],marker="D",ls="",label="Qualified IV mode")]
    statuses=set()
    for ax,k in zip(axes,("gamma","omega")):
        ax.axhline(0,color=COLOR[-1],lw=.9)
        ax.set_xticks(GRADIENTS)
        for r in selected:
            vals=[f[k] for f in fits if f["origin"]=="new" and f["case"]==r["case"] and f["window"] in {"30-40","36-44","44-52"}]
            y=r.get(k+"_final_fit")
            if y is None or not vals:
                continue
            qualified=r["status"].startswith("qualified finite")
            mode=r["status"].startswith("qualified IV")
            idx=2 if mode else int(qualified)
            ms=refs[idx]
            statuses.add(idx)
            ax.errorbar(r["omn_D"],y,yerr=[[y-min(vals)],[max(vals)-y]],ls="",capsize=4,
                        color=ms.get_color(),marker=ms.get_marker(),mfc=ms.get_markerfacecolor(),ms=7)
    legend(fig,[refs[i] for i in sorted(statuses)]+[Line2D([],[],marker="|",color=COLOR[-1],ls="",label="Range across three fitting windows")],2)
    save(fig,output,"A_01_growth_and_signed_frequency")


def a_histories(rows,signals,hyp,output):
    chosen=adiabatic_cases(rows,hyp)
    for name,label in [("energy",r"Normalized perturbation free energy $E/E_0$"),
                       ("amplitude",r"Relative $|\langle \phi_{\rm ref},\phi(t)\rangle|$"),
                       ("phase","Unwrapped projected phase (rad)")]:
        fig,ax=plt.subplots(figsize=(7.5,4.4),layout="constrained")
        for r,c in zip(chosen,COLOR):
            s=signals[r["case"]]
            t=s["t"]
            y=s[name]
            if name=="energy":
                t,y=y[:,0],y[:,1]/y[0,1]
            ax.plot(t,y,color=c,label=rf"$\omega_{{n,D}}={r['omn_D']:g}$",lw=1.2)
        for lo,hi in ((36,44),(44,52)):
            ax.axvspan(lo,hi,color="#d0e4ec" if lo==36 else "#e7e1eb",alpha=.38)
        if name=="amplitude":
            ax.set_yscale("log")
        if name=="energy":
            ax.set_ylim(.9995,1.0005)
            ax.ticklabel_format(axis="y",useOffset=False,style="plain")
        ax.set(xlabel=T,ylabel=label,xlim=(0,54.65))
        ax.legend(frameon=False,ncols=2)
        save(fig,output,{"energy":"A_02_free_energy","amplitude":"A_03_potential_amplitude","phase":"A_04_unwrapped_phase"}[name])


def a_hyp(signals,output):
    fig,axes=pair(T,(r"$E/E_0$ at $\omega_{n,D}=0.6$",r"$E/E_0$ at $\omega_{n,D}=1.5$"))
    for ax,g in zip(axes,("0p6","1p5")):
        for h,color in enumerate(COLOR[:4]):
            case=f"A_g{g}_h{h}" if h!=4 else ""
            if h==3:
                h=4; case=f"A_base_g{g}_h4"
            s=signals[case]["energy"]
            use=s[:,0]<=54.65
            ax.plot(s[use,0],s[use,1]/s[0,1],color=color,label=rf"$\mathrm{{hyp\_z}}={h}$",lw=1.6)
        ax.axvline(52,color="#82888d",ls=":",lw=.9)
    legend(fig,axes[1].get_legend_handles_labels()[0],4)
    save(fig,output,"A_05_hyperdiffusion")


def modes(signals, cases, name,output):
    fig,axes=pair("Normalized field-line coordinate",(r"Normalized potential $|\phi|$",r"Relative spatial phase (rad)"))
    handles=[]
    for (case,label),color in zip(cases,COLOR):
        s=signals.get(case)
        if s is None:
            continue
        y=s["template"]
        z=np.linspace(-1,1,len(y))
        phase=np.unwrap(np.angle(y))
        phase-=phase[len(phase)//2]
        axes[0].plot(z,np.abs(y),color=color,lw=1.5)
        phase[np.abs(y)<.03]=np.nan
        axes[1].plot(z,phase,color=color,lw=1.5)
        handles.append(Line2D([],[],color=color,lw=1.5,label=label))
    legend(fig,handles,3)
    save(fig,output,name)


def b_results(rows,signals,output):
    selected=sorted((r for r in rows if r["case"] in {"B_g0p5","B_g0p75","B_g1","B_g1p25","B_g1p5","B_g2"}),key=lambda r:r["omn_e"])
    reference=next(r for r in rows if r["case"]=="B_pure_D_g1")
    fig,axes=pair(B_X,(GAMMA,OMEGA))
    fig.suptitle(r"Compensated scan with $\omega_{n,D}=1$ and $\omega_{n,\mathrm{He}}=4\omega_{n,e}-3$")
    qualified=[r for r in selected if r["status"].startswith("qualified IV")]
    for k,ax in zip(("gamma","omega"),axes):
        ax.axhline(0,color=COLOR[-1],lw=.85)
        ax.set_xticks([.5,.75,1,1.25,1.5,2])
        for row in selected:
            if row in qualified:
                ax.scatter(row["omn_e"],row[k+"_native"],color=COLOR[0],marker="o",zorder=4)
            elif row.get(k+"_final_fit") is not None:
                ax.scatter(row["omn_e"],row[k+"_final_fit"],facecolor="none",edgecolor=COLOR[0],marker="o",zorder=4)
        for a,b in zip(selected,selected[1:]):
            if a in qualified and b in qualified:
                ax.plot([a["omn_e"],b["omn_e"]],[a[k+"_native"],b[k+"_native"]],color=COLOR[0],lw=1.45)
        if reference[k+"_native"] is not None:
            ax.scatter(1,reference[k+"_native"],color=COLOR[1],marker="D",zorder=5)
    handles=[Line2D([],[],color=COLOR[0],marker="o",label="Compensated D–He–electron scan"),
             Line2D([],[],color=COLOR[1],marker="D",ls="",label="Separate two-species D reference")]
    if len(qualified)!=len(selected):
        handles.append(Line2D([],[],color=COLOR[0],marker="o",mfc="none",ls="",label="Unresolved finite-time fit"))
    legend(fig,handles,2)
    save(fig,output,"B_01_growth_and_signed_frequency")

    cases=[("B_g0p5","$\\omega_{n,e}=0.50$"),("B_g1","$\\omega_{n,e}=1.00$"),("B_g2","$\\omega_{n,e}=2.00$"),
           ("B_pure_D_g1","Two-species reference")]
    fig,ax=plt.subplots(figsize=(7.5,4.4),layout="constrained")
    for (case,label),color in zip(cases,COLOR):
        if case in signals and len(e:=signals[case]["energy"]):
            ax.semilogy(e[:,0],e[:,1]/e[0,1],color=color,label=label,lw=1.6)
    ax.set(xlabel=T,ylabel=r"Normalized perturbation free energy $E/E_0$")
    ax.legend(frameon=False)
    save(fig,output,"B_02_free_energy")
    modes(signals,cases,"B_03_mode_structure",output)

    copies={r["case"]:r for r in rows if r["origin"]=="new"}
    checks=[("B_g1","B_g1_z32","1.0: $n_z$"),("B_g1","B_g1_halfdt","1.0: half step (RKC1)"),("B_g1","B_g1_halfdt_rkc2","1.0: half step (RKC2)"),("B_g2","B_g2_v64","2.0: $n_v$")]
    summary=[]
    for base,check,label in checks:
        for expected in (base,check):
            if expected not in copies:
                break
        else:
            a,b=copies[base],copies[check]
            if not all(x["status"].startswith("qualified IV") for x in (a,b)):
                continue
            g=100*(b["gamma_final_fit"]/a["gamma_final_fit"]-1)
            w=100*(b["omega_final_fit"]/a["omega_final_fit"]-1)
            summary.append(dict(control=label,case=check,reference=base,gamma_pct=g,omega_pct=w,
                                reference_dt=a["dt_measured"],control_dt=b["dt_measured"]))
    if summary:
        fig,ax=plt.subplots(figsize=(7.5,4.0),layout="constrained")
        loc=np.arange(len(summary))
        ax.barh(loc-.16,[r["gamma_pct"] for r in summary],.28,color=COLOR[0],label="Growth")
        ax.barh(loc+.16,[r["omega_pct"] for r in summary],.28,color=COLOR[1],label="Signed frequency")
        ax.axvline(0,color=COLOR[-1],lw=.9)
        ax.set(yticks=loc,yticklabels=[r["control"] for r in summary],xlabel="Change in late field-fit rate (%)")
        ax.legend(frameon=False)
        save(fig,output,"B_04_numerical_controls")


def read_rows(name):
    path = DATA / name
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", newline="") as stream:
        return list(csv.DictReader(stream))


def read_signals():
    histories = defaultdict(list)
    energies = defaultdict(list)
    profiles = defaultdict(list)
    for row in read_rows("complex_field_history.csv.gz"):
        histories[row["case"]].append([float(row[key]) for key in
                                       ("time", "relative_projection_amplitude", "unwrapped_phase")])
    for row in read_rows("energy_history.csv.gz"):
        energies[row["case"]].append([float(row["time"]), float(row["total_energy"])])
    for row in read_rows("mode_profiles.csv"):
        profiles[row["case"]].append(complex(float(row["real"]), float(row["imaginary"])))
    signals = {}
    for case, history in histories.items():
        time, amplitude, phase = np.asarray(history).T
        signals[case] = dict(t=time, amplitude=amplitude, phase=phase,
                             template=np.asarray(profiles[case]),
                             energy=np.asarray(energies[case]))
    return signals


def convert(rows, numeric):
    for row in rows:
        for key in numeric:
            row[key] = float(row[key]) if row[key] else None
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "generated/additional_experiments")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    rows = convert(read_rows("all_runs.csv"),
                   ("omn_D", "omn_e", "gamma_native", "omega_native",
                    "gamma_final_fit", "omega_final_fit", "dt_measured"))
    fits = convert(read_rows("field_fits.csv"), ("gamma", "omega"))
    signals = read_signals()
    a_rates(rows, fits, 0, args.out)
    a_histories(rows, signals, 0, args.out)
    a_hyp(signals, args.out)
    modes(signals, [("A_g1p5_h0", "24/64/24"),
                    ("A_g1p5_h0_nz48", "48/64/24, half step"),
                    ("A_g1p5_h0_nv96_halfdt", "24/96/24, half step"),
                    ("A_base_g1p5_h4", "24/64/24, hyp_z=4")],
          "A_06_mode_structure", args.out)
    b_results(rows, signals, args.out)


if __name__ == "__main__":
    main()
