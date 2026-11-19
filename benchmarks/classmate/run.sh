#!/bin/sh
# Run the identical shared input in an unused directory.
set -eu
here=$(CDPATH='' cd "$(dirname "$0")" && pwd)
case "${1:-}" in
    /*) gene=$1 ;;
    *) echo "Usage: sh $0 /absolute/path/to/gene" >&2; exit 2 ;;
esac
test -x "$gene"
run=$(mktemp -d "${TMPDIR:-/tmp}/gene-pair-benchmark.XXXXXX")
mkdir "$run/out"
cp "$here/parameters" "$run/parameters"
printf 'Run directory: %s\n' "$run"
(cd "$run" && export OMP_NUM_THREADS=1 && "$gene" >run.log 2>run.stderr)
sh "$here/read_rates.sh" "$run"
