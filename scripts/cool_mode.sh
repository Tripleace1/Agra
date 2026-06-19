#!/usr/bin/env bash
# Aggressive thermal-safe profile for hot or under-cooled laptops.
# Use on dev machines where the fan can't keep up with sustained inference.
# Do NOT use these settings on the ADTC reference machine during the audit —
# they cost 30-50% of your tokens/sec.
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

if [[ -z "${AGRA_MODEL:-}" ]]; then
  CAND=$(ls backend/models/*.gguf 2>/dev/null | head -n1 || true)
  if [[ -n "$CAND" ]]; then
    export AGRA_MODEL=$(basename "$CAND")
  fi
fi

# Thermal-safe profile:
#   2 threads, batch 64, 30 ms cooldown between streamed tokens.
export AGRA_THREADS=2
export AGRA_N_BATCH=64
export AGRA_COOLDOWN=0.03

echo "==============================================================="
echo " Agra COOL MODE — thermal-safe profile"
echo "   threads=$AGRA_THREADS  batch=$AGRA_N_BATCH  cooldown=${AGRA_COOLDOWN}s"
echo "   model=${AGRA_MODEL:-<not set>}"
echo "   Expect ~50% of normal tokens/sec. CPU should stay <80°C."
echo "==============================================================="

cd backend
exec python app.py
