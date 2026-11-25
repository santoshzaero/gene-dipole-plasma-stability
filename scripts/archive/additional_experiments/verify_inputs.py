#!/usr/bin/env python3
"""Verify the archived and effective inputs and diagnostic files for the new IV scans."""
import csv
from decimal import Decimal
import json
from pathlib import Path
import re

from run_experiments import A,B,ROOT,DIAGNOSTICS,validate,get_fields

NUMERIC=("mass","dens","temp","charge","omt","omn")
REQUIRED=("parameters.dat","field.dat","energy.dat","omega.dat","nrg.dat")
MODEL_KEYS=("kymin","lv","lw","r0_dipole","Icurr_dipole","c_surf_dipole","beta","coll")
records=[]


def species(text):
    return [get_fields(b) for b in re.findall(r"(?ms)^&species\b.*?^/",text)]


def verify(run, root):
    inp=(run/"parameters").read_text()
    checks=validate(inp)
    final=(run/"out/parameters.dat").read_text()
    x,y=get_fields(inp),get_fields(final)
    for k in ("n_spec","nz0","nv0","nw0","magn_geometry","comp_type","calc_dt"):
        assert x[k]==y[k],(run.name,k,x[k],y[k])
    for k in MODEL_KEYS:
        if k=="coll" and k not in y and root==A:
            assert Decimal(x[k])==0 and "without collisions" in (run/"run.log").read_text()
            continue
        assert abs(Decimal(x[k])-Decimal(y[k]))<Decimal("0.00001"),(run.name,k,x[k],y[k])
    si,sf=species(inp),species(final)
    for v,w in zip(si,sf,strict=True):
        assert v["name"]==w["name"]
        for k in NUMERIC:
            assert Decimal(v[k])==Decimal(w[k]),(run.name,k,v[k],w[k])
    if root==B:
        assert Decimal(y["mref"])==1
    else:
        assert Decimal(x["tau"])==Decimal(y.get("tau","1"))==1
    for k in REQUIRED:
        assert (run/"out"/k).stat().st_size>0,(run.name,k)
    assert not (run/"out"/"vsp.dat").exists(),run.name
    process=json.loads((run/"process.json").read_text())
    assert process["preflight"]==checks and process["returncode"]==int((run/"exit_status.txt").read_text())
    if process["returncode"]!=0:
        assert process["early_stop"],run.name
    record=dict(case=run.name,closure="implicit Boltzmann electrons" if root==A else "three kinetic species",
                grid="/".join(x[k] for k in ("nz0","nv0","nw0")),dt_mode=x["calc_dt"],
                hyp_z=x.get("hyp_z","0"),preflight_charge_residual=checks.get("charge_residual"),
                preflight_gradient_residual=checks.get("gradient_residual"),
                omega_n_deuterium=si[0]["omn"],omega_n_electrons=si[1]["omn"] if root==B else "implicit",
                omega_n_helium=si[2]["omn"] if root==B else None,parameters_effective_match=True)
    records.append(record)


if __name__=="__main__":
    for root in (A,B):
        for run in sorted((root/"Runs").iterdir()):
            if (run/"process.json").is_file():
                verify(run,root)
    out=ROOT/"Numerical_Results"/"input_verification.csv"
    with out.open("w",newline="") as stream:
        wr=csv.DictWriter(stream,fieldnames=list(records[0]))
        wr.writeheader()
        wr.writerows(records)
    print(f"Validated {len(records)} completed effective inputs, diagnostics and recorded preflights.")
