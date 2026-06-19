#!/usr/bin/env bash
# Measures: RAM (RSS), CPU temp, first-token latency, tokens/sec.
# Run while ./scripts/run.sh is up in another terminal.
set -euo pipefail

URL="http://127.0.0.1:5000"

echo "== Agra performance benchmark =="

PID=$(pgrep -f "backend/app.py" | head -n1 || true)
if [[ -z "$PID" ]]; then
  echo "Server not running. Start ./scripts/run.sh in another terminal first."
  exit 1
fi

echo "[1] RSS before warm-up:"
RSS_BEFORE=$(awk '/VmRSS/ {print $2/1024 " MB"}' /proc/$PID/status)
echo "    $RSS_BEFORE"

echo
echo "[2] Cold inference (first token timing):"
START=$(date +%s.%N)
curl -sS -X POST "$URL/api/chat" -H "Content-Type: application/json" \
  -d '{"prompt":"Briefly: list two crops good for sandy soil.","lang":"en","history":[]}' \
  -o /tmp/agra_bench1.json
END=$(date +%s.%N)
LAT=$(awk -v s="$START" -v e="$END" 'BEGIN {printf "%.2f", e-s}')
echo "    Full request latency (cold): ${LAT}s"

echo
echo "[3] Warm inference (5 prompts, avg):"
TOTAL_TOK=0
TOTAL_S=0
for i in 1 2 3 4 5; do
  S=$(date +%s.%N)
  RESP=$(curl -sS -X POST "$URL/api/chat" -H "Content-Type: application/json" \
    -d "{\"prompt\":\"Give one tip on irrigation method $i.\",\"lang\":\"en\",\"history\":[]}")
  E=$(date +%s.%N)
  # rough token estimate: words * 1.3
  WORDS=$(echo "$RESP" | python3 -c "import sys, json; d=json.load(sys.stdin); print(len(d.get('answer','').split()))")
  TOK=$(awk -v w="$WORDS" 'BEGIN {printf "%.0f", w*1.3}')
  DT=$(awk -v s="$S" -v e="$E" 'BEGIN {printf "%.2f", e-s}')
  TPS=$(awk -v t="$TOK" -v d="$DT" 'BEGIN {if (d>0) printf "%.2f", t/d; else print "0"}')
  echo "    run $i: ${TOK} tok in ${DT}s → ${TPS} tok/s"
  TOTAL_TOK=$(awk -v a="$TOTAL_TOK" -v b="$TOK" 'BEGIN {print a+b}')
  TOTAL_S=$(awk -v a="$TOTAL_S" -v b="$DT" 'BEGIN {print a+b}')
done
AVG=$(awk -v t="$TOTAL_TOK" -v s="$TOTAL_S" 'BEGIN {if (s>0) printf "%.2f", t/s; else print "0"}')
echo "    AVG tokens/s: $AVG"

echo
echo "[4] RSS after inference:"
RSS_AFTER=$(awk '/VmRSS/ {print $2/1024 " MB"}' /proc/$PID/status)
echo "    $RSS_AFTER"

echo
echo "[5] CPU temperature (highest core):"
if command -v sensors >/dev/null 2>&1; then
  sensors | awk '/Core/ {gsub("\\+|°C",""); if ($3+0 > max) max=$3+0} END {print "    " max "°C"}'
else
  echo "    (install lm-sensors: sudo apt install lm-sensors)"
fi

echo
echo "Targets: RSS < 2.5 GB · CPU temp < 82°C · tokens/s > 6 (1.5B on i5-8th gen)"
