#!/usr/bin/env sh
# Launch one copy of the exact class benchmark or analyze a completed run.
set -eu

benchmark_dir=$(CDPATH='' cd "$(dirname "$0")" && pwd)
project_dir=$(dirname "$benchmark_dir")
python_command=${GENE_BENCHMARK_PYTHON:-python3}

if [ "$#" -eq 2 ] && [ "$1" = "--analyze" ]; then
    exec "$python_command" "$project_dir/scripts/measure_class_benchmark.py" "$2"
fi
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 /absolute/path/to/gene or $0 --analyze /path/to/completed-run" >&2
    exit 2
fi
case "$1" in
    /*) gene_bin=$1 ;;
    *) echo "Use an absolute path to the GENE executable." >&2; exit 2 ;;
esac
if [ ! -x "$gene_bin" ]; then
    echo "GENE executable not found: $gene_bin" >&2
    exit 2
fi

"$python_command" - "$benchmark_dir/parameters" <<'PY'
import hashlib
from pathlib import Path
import sys
import matplotlib
import numpy

expected = "d8e40c0f055746b882c0c7da8a8753dd3d536f3ef27e1dfbf02cdc6908616600"
if hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest() != expected:
    raise SystemExit("Benchmark input checksum mismatch")
PY

case_dir=$(mktemp -d "${TMPDIR:-/tmp}/gene-class-benchmark.XXXXXX")
mkdir "$case_dir/out"
cp "$benchmark_dir/parameters" "$case_dir/parameters"
printf 'Benchmark run directory: %s\n' "$case_dir"
(
    cd "$case_dir"
    export OMP_NUM_THREADS=1
    "$gene_bin" >run.log 2>run.stderr
)
"$python_command" "$project_dir/scripts/measure_class_benchmark.py" "$case_dir" > "$case_dir/benchmark.json"
printf 'Comparison record: %s/benchmark.json\n' "$case_dir"
