#!/usr/bin/env python3
"""Prepare and run separate GENE IV cases. Explicit batch selection is required."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import struct
import time

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "01_Adiabatic_Zero_Temperature_Gradient"
B = ROOT / "02_Compensated_Electron_Density_Gradient"
A_DT = 0.0496570359086059
B_GRADIENTS = (0.5, 0.75, 1.0, 1.25, 1.5, 2.0)
DIAGNOSTICS = ("parameters.dat","field.dat","energy.dat","omega.dat","omega_Ef_species.dat","nrg.dat","dipole.dat")


def tag(number):
    return f"{number:g}".replace(".", "p")


def get_fields(text):
    return dict(re.findall(r"(?mi)^\s*(\w+)\s*=\s*([^!\s]+)", text))


def match_setting(text, key, value):
    changed, count = re.subn(rf"(?m)^([ \t]*{key}[ \t]*=)[^\n]*$", rf"\g<1> {value}", text)
    if count != 1:
        raise ValueError(f"Expected exactly one {key}, got {count}")
    return changed


def clean(text):
    text = re.sub(r"(?mi)^[ \t]*(which_ev|ev_max_it|ev_n_test)[ \t]*=.*\n", "", text)
    for key in ("istep_mom","istep_vsp"):
        text = match_setting(text, key, 0)
    return text


def a_input(template, gradient, hyp, nz=24, nv=64, dt=A_DT, steps=1100):
    text = clean(template)
    for key, value in dict(omn=gradient,hyp_z=hyp,nz0=nz,nv0=nv,ntimesteps=steps).items():
        text = match_setting(text,key,value)
    if dt is not None:
        text = match_setting(text, "calc_dt", f"F\ndt_max = {dt:.16g}\ndt_vlasov = {dt:.16g}")
    return text


def b_input(template, gradient, nz=24, nv=48, nw=24, dt=None, thin=True, collision_bound=3104):
    text = clean(template)
    if thin:
        text = match_setting(text, "istep_energy", 5)
        text = match_setting(text, "istep_nrg", 10)
    gradients = {"deuterium":Decimal(1), "electrons":Decimal(str(gradient)),
                 "helium":4*Decimal(str(gradient))-3}
    for key, value in dict(nz0=nz,nv0=nv,nw0=nw).items():
        text = match_setting(text, key, value)
    def update(match):
        species = get_fields(match[0])["name"].strip("'\"")
        return match_setting(match[0], "omn", gradients[species])
    text = re.sub(r"(?ms)^&species\b.*?^/", update, text)
    if dt is not None:
        text = match_setting(text, "calc_dt", f"F\ndt_max = {dt:.16g}\ndt_vlasov = {dt:.16g}\nev_coll = {collision_bound:.16g}")
    return text


def validate(text):
    p = get_fields(text)
    assert p["comp_type"]=="'IV'" and p["nonlinear"]=="F"
    assert p["diagdir"]=="'./out'" and p["write_checkpoint"]=="F"
    assert p["magn_geometry"]=="'dipole'" and Decimal(p["kymin"])==Decimal("0.7")
    assert Decimal(p["beta"])==0 and p["istep_vsp"]=="0"
    assert Decimal(p["lv"])==Decimal("3.5") and Decimal(p["lw"])==Decimal("12.25")
    species=[get_fields(block) for block in re.findall(r"(?ms)^&species\b.*?^/",text)]
    assert len(species)==int(p["n_spec"])
    charge = [Decimal(s["charge"])*Decimal(s["dens"]) for s in species]
    gradient_charge = sum(c*Decimal(s["omn"]) for c,s in zip(charge,species))
    if len(species)==3:
        assert sum(charge)==gradient_charge==0
        assert Decimal(species[0]["omn"])==1
        assert Decimal(p["mref"])==Decimal(1) and Decimal(p["coll"])==Decimal(".01")
        expected=[("deuterium","2","1",".75"),("electrons",".00054462","-1","1"),("helium","4","2",".125")]
        for s,(name,mass,z,n) in zip(species,expected):
            assert s["name"].strip("'")==name and Decimal(s["mass"])==Decimal(mass)
            assert Decimal(s["charge"])==Decimal(z) and Decimal(s["dens"])==Decimal(n)
            assert Decimal(s["omt"])==2 and Decimal(s["temp"])==1
        return {"charge_residual":str(sum(charge)), "gradient_residual":str(gradient_charge)}
    s, = species
    assert s["name"]=="'deuterium'" and [Decimal(s[k]) for k in ("mass","charge","temp","dens","omt")]==[2,1,1,1,0]
    assert Decimal(p["coll"])==0 and Decimal(p["tau"])==1
    return {"electron_response":"implicit Boltzmann", "quasineutral_equilibrium_gradient":s["omn"]}


def archive(source, dest, origin):
    if (dest/"source.json").exists():
        return
    dest.mkdir(parents=True,exist_ok=True)
    (dest/"out").mkdir(exist_ok=True)
    for name in ("parameters","run.log","process.json","exit_status.txt","runtime_seconds.txt"):
        path=source/name
        if path.is_file():
            (dest/name).write_bytes(path.read_bytes())
    for name in DIAGNOSTICS:
        for path in (source/"out"/name,source/name):
            if path.is_file():
                (dest/"out"/name).write_bytes(path.read_bytes())
                break
    (dest/"source.json").write_text(json.dumps({"original":str(source),"origin":origin},indent=2)+"\n")
    print(f"Copied archival diagnostics for {dest.name}",flush=True)


def unstable(directory, zero_drive_control=False):
    log = (directory/"run.log").read_text(errors="replace").lower()
    if log.count("rescaled amplitudes") >= 4:
        return "four or more native amplitude rescalings"
    if re.search(r"floating.point exception|sigsegv|violation of quasineutrality", log):
        return "fatal numerical or equilibrium diagnostic in run.log"
    path=directory/"out"/"energy.dat"
    if path.exists() and path.stat().st_size:
        with path.open("rb") as handle:
            handle.seek(max(0,path.stat().st_size-4096))
            tail=handle.read().decode(errors="replace")
        energy0=None
        if zero_drive_control:
            with path.open() as handle:
                for line in handle:
                    if line.strip() and not line.lstrip().startswith("#"):
                        energy0=float(line.split()[1])
                        break
        for line in tail.splitlines()[1:]:
            columns = line.split()
            if len(columns) >= 8 and columns[0] != "#":
                if any(re.fullmatch(r"(?i)[+-]?(nan|infinity|inf)", columns[i]) for i in (1,2,7)):
                    return "nonfinite free energy or energy-balance term"
                if energy0 and float(columns[1])>2*energy0 and float(columns[3])==0:
                    return "free-energy runaway with zero recorded drive"
    path=directory/"out/field.dat"
    if path.exists() and path.stat().st_size >= 32:
        with path.open("rb") as handle:
            first=handle.read(20)
            if len(first)==20:
                size,t0,closing,phi_size=struct.unpack("<idii",first)
                if size==closing==8 and 0 < phi_size < 1_000_000:
                    handle.seek(24+phi_size)
                    second=handle.read(12)
                    if len(second)==12:
                        marker,t1=struct.unpack("<id",second)
                        if marker==8 and (not math.isfinite(t1) or t1-t0<1e-10):
                            return "invalid field time step"
    return None


def execute(root, case, input_text, exe):
    preflight=validate(input_text)
    if shutil.disk_usage(ROOT).free < 350_000_000:
        raise RuntimeError("Insufficient free space for a new case")
    directory=root/"Runs"/case
    directory.mkdir(parents=True,exist_ok=False)
    (directory/"out").mkdir()
    (directory/"parameters").write_text(input_text)
    (ROOT/"Parameters"/f"{case}.nml").write_text(input_text)
    env=dict(os.environ, OMP_NUM_THREADS="1",OPENBLAS_NUM_THREADS="1",GFORTRAN_UNBUFFERED_ALL="1")
    started=time.monotonic()
    started_epoch=time.time()
    reason=None
    with (directory/"run.log").open("w") as log:
        proc=subprocess.Popen([str(exe)],cwd=directory,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        print(f"Started {case}, PID {proc.pid}, preflight {preflight}",flush=True)
        while proc.poll() is None:
            time.sleep(2)
            reason=unstable(directory, preflight.get("electron_response")=="implicit Boltzmann")
            if reason and proc.poll() is None:
                os.killpg(proc.pid,signal.SIGTERM)
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid,signal.SIGKILL)
                    proc.wait()
                break
    elapsed=time.monotonic()-started
    process=dict(case=case,executable=str(exe),returncode=proc.returncode,elapsed_s=elapsed,
                 started_epoch=started_epoch,finished_epoch=time.time(),early_stop=reason,preflight=preflight,
                 input_sha256=hashlib.sha256(input_text.encode()).hexdigest())
    (directory/"process.json").write_text(json.dumps(process,indent=2)+"\n")
    (directory/"exit_status.txt").write_text(f"{proc.returncode}\n")
    (directory/"runtime_seconds.txt").write_text(f"{elapsed:.3f}\n")
    print(f"Finished {case}: return {proc.returncode}, elapsed {elapsed:.1f} s, {reason or 'see native diagnostics'}",flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch",choices=("archive","stage1","a_dissipation","b_scan","a_controls","a_v_retry","a_remaining","b_controls","b_step_retry","b_step_matched"))
    parser.add_argument("--gene",type=Path,default=Path.home()/"Developer/gene-complete")
    parser.add_argument("--repo",type=Path,required=True)
    parser.add_argument("--jobs",type=int,default=3)
    parser.add_argument("--hyp",type=int,choices=(0,1,2),default=0)
    parser.add_argument("--b-dt",type=float)
    parser.add_argument("--a-gradient",type=float,default=1.5)
    parser.add_argument("--a-z-dt",type=float,default=A_DT/2)
    args=parser.parse_args()
    assert args.jobs>0
    gene, repo = args.gene.resolve(),args.repo.resolve()
    archive_a=gene/"runs"/"matched_adiabatic_gradients_20261119_174530"
    archive_e=repo/"work"/"deuterium_adiabatic_density_omt0"
    helium=repo/"work"/"deuterium_followup"/"he_omn_e_200"
    a_template=(archive_a/"omn_0p6"/"parameters").read_text()
    b_template=(helium/"parameters").read_text()
    if args.batch=="archive":
        for g in (0.2,0.6,1.0,1.5):
            archive(archive_a/f"omn_{str(g).replace('.', 'p')}", A/"Archive"/f"A_base_g{tag(g)}_h4","reused finer baseline")
        for g in (0.2,0.4,0.6,1.0,1.5):
            archive(archive_e/f"omn_{str(g).replace('.', 'p')}", A/"Archive"/f"A_econ_g{tag(g)}_h4","reused economical scan")
        reference=repo/"work"/"deuterium_density_pilot"/"omn_1"
        archive(reference,B/"Archive"/"B_pure_D_g1","reused pure deuterium reference")
        archive(helium,B/"Archive"/"B_previous_He_Dg2","earlier He compensation template; different fixed D gradient")
        return
    if args.batch in {"stage1","a_dissipation"}:
        jobs=[(B,"B_g1",b_input(b_template,1,thin=False))] if args.batch=="stage1" else []
        jobs.extend((A,f"A_g{tag(g)}_h{h}",a_input(a_template,g,h))
                    for h in (2,1,0) for g in (0.6,1.5))
    elif args.batch=="b_scan":
        jobs=[(B,f"B_g{tag(g)}",b_input(b_template,g)) for g in B_GRADIENTS if g!=1]
    elif args.batch=="a_controls":
        g,h=args.a_gradient,args.hyp
        jobs=[(A,f"A_g{tag(g)}_h{h}_nv96",a_input(a_template,g,h,nv=96,steps=1550)),
              (A,f"A_g{tag(g)}_h{h}_nz48",a_input(a_template,g,h,nz=48,dt=args.a_z_dt,steps=math.ceil(53.5/args.a_z_dt))),
              (A,f"A_g{tag(g)}_h{h}_halfdt",a_input(a_template,g,h,dt=args.a_z_dt,steps=math.ceil(53.5/args.a_z_dt)))]
    elif args.batch=="a_v_retry":
        g,h=args.a_gradient,args.hyp
        jobs=[(A,f"A_g{tag(g)}_h{h}_nv96_halfdt",
               a_input(a_template,g,h,nv=96,dt=args.a_z_dt,steps=math.ceil(75/args.a_z_dt)))]
    elif args.batch=="a_remaining":
        jobs=[(A,f"A_g{tag(g)}_h{args.hyp}",a_input(a_template,g,args.hyp)) for g in (0.2,1.0)]
    else:
        if args.b_dt is None or args.b_dt<=0:
            parser.error("b_controls requires --b-dt measured from the central case")
        if args.batch=="b_step_matched":
            matched=b_input(b_template,1,dt=args.b_dt/2)
            matched=match_setting(matched,"calc_dt","F\ncoll_split_scheme = 'RKC2'")
            jobs=[(B,"B_g1_halfdt_rkc2",matched)]
        elif args.batch=="b_step_retry":
            jobs=[(B,"B_g1_halfdt",b_input(b_template,1,dt=args.b_dt/2))]

        else:
            jobs=[(B,"B_g1_z32",b_input(b_template,1,nz=32)),
              (B,"B_g1_halfdt",b_input(b_template,1,dt=args.b_dt/2)),
              (B,"B_g2_v64",b_input(b_template,2,nv=64))]
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures=[pool.submit(execute,root,case,data,gene/"bin/gene_mac_arm64") for root,case,data in jobs]
        for future in futures:
            future.result()


if __name__=="__main__":
    main()
