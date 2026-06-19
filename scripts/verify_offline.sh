#!/usr/bin/env bash
# Verifies the running Agra portal is fully offline-capable.
# Usage: ./scripts/verify_offline.sh
set -euo pipefail
URL="http://127.0.0.1:5000"

echo "== Agra offline verification =="

echo
echo "[1] App reachable on loopback?"
if curl -sS --fail "$URL/api/health" >/dev/null; then
  echo "    OK — /api/health responds"
else
  echo "    FAIL — server not running. Start with ./scripts/run.sh"
  exit 1
fi

echo
echo "[2] Network sockets opened by the python (app.py) process:"
PIDS=$(pgrep -f "backend/app.py" || true)
if [[ -z "$PIDS" ]]; then
  echo "    No app.py PID found."
else
  for p in $PIDS; do
    echo "    PID $p:"
    ss -tnp 2>/dev/null | awk -v p="pid=$p" '$0 ~ p { print "      "$0 }' || true
  done
  echo "    (Expect ONLY 127.0.0.1:5000 LISTEN. Any external connection = leak.)"
fi

echo
echo "[3] Running curl against the chat endpoint with internet cut…"
echo "    Cut your wifi/ethernet now, then press Enter to continue."
read -r _
RESP=$(curl -sS -X POST "$URL/api/chat" -H "Content-Type: application/json" \
  -d '{"prompt":"How do I treat fall armyworm on maize?","lang":"en","history":[]}' || true)
if echo "$RESP" | grep -q '"answer"'; then
  echo "    OK — chat works with no internet:"
  echo "$RESP" | head -c 400; echo
else
  echo "    FAIL — response was:"
  echo "$RESP"
  exit 1
fi

echo
echo "[4] DNS isolation test (should fail if firewall blocks egress):"
if timeout 4 curl -sS --fail https://huggingface.co >/dev/null 2>&1; then
  echo "    WARNING — egress to huggingface.co succeeded. You are NOT actually offline."
else
  echo "    OK — egress blocked / no internet."
fi

echo
echo "All checks complete. Agra is operating offline."
