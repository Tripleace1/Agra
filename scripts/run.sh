#!/usr/bin/env bash
# Launch Agra. By default uses Qwen2.5-1.5B. Override with AGRA_MODEL=…
set -euo pipefail
HERE="$(cd "$(dirname "$0")"/.. && pwd)"
cd "$HERE"

if [[ ! -d .venv ]]; then
  echo "Run ./scripts/install.sh first." >&2
  exit 1
fi
source .venv/bin/activate

if [[ ! -f backend/db/agra.sqlite ]]; then
  echo "DB missing — seeding…"
  (cd backend && python db/seed.py)
fi

# Use PHYSICAL cores only (skip SMT/hyperthreads) to halve heat output.
# This is the single biggest knob for CPU temperature on dual-core laptops.
PHYS=$(lscpu | awk -F: '/^Core\(s\) per socket/ {gsub(" ",""); print $2}')
SOCKETS=$(lscpu | awk -F: '/^Socket\(s\)/ {gsub(" ",""); print $2}')
if [[ -n "$PHYS" && -n "$SOCKETS" ]]; then
  DEFAULT_THREADS=$((PHYS * SOCKETS))
else
  DEFAULT_THREADS=2
fi
# Cap at 4 even on bigger machines — protects against thermal penalty.
if (( DEFAULT_THREADS > 4 )); then DEFAULT_THREADS=4; fi
export AGRA_THREADS="${AGRA_THREADS:-$DEFAULT_THREADS}"

# Match the model file name actually present in backend/models/
if [[ -z "${AGRA_MODEL:-}" ]]; then
  CAND=$(ls backend/models/*.gguf 2>/dev/null | head -n1 || true)
  if [[ -n "$CAND" ]]; then
    export AGRA_MODEL=$(basename "$CAND")
  fi
fi

echo "Agra starting → http://127.0.0.1:5000   model=${AGRA_MODEL:-<not set>}   threads=$AGRA_THREADS   cooldown=${AGRA_COOLDOWN:-0}s"
cd backend
exec python app.py
