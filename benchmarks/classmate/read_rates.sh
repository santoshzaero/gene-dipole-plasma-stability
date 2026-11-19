#!/bin/sh
# Extract a validated single-mode IV result from a completed run.
set -eu
if [ "$#" -ne 1 ]; then
    echo "Usage: sh $0 /path/to/completed-run" >&2
    exit 2
fi
run=$1
if ! grep -q 'Linear growth rate is converged' "$run/run.log" ||
   grep -q 'rescaled amplitudes' "$run/run.log"; then
    echo "No clean IV convergence. Inspect $run/run.log." >&2
    exit 1
fi
awk '
    BEGIN { number = "^[-+]?[0-9]+([.][0-9]+)?([eE][-+]?[0-9]+)?$" }
    NF == 3 && $1 ~ number && $2 ~ number && $3 ~ number { count++; row=$0 }
    END {
        if (count != 1) { print "Expected one numeric omega.dat row" > "/dev/stderr"; exit 1 }
        print "kymin  normalized_growth  signed_real_frequency"
        print row
    }
' "$run/out/omega.dat"
