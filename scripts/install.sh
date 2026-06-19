#!/usr/bin/env bash
# Agra — one-time install on Ubuntu 22.04 (4 GB RAM box).
set -euo pipefail
HERE="$(cd "$(dirname "$0")"/.. && pwd)"
cd "$HERE"

echo "[1/5] Installing system packages…"
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
  python3 python3-venv python3-pip build-essential cmake \
  sqlite3 curl ca-certificates

echo "[2/5] Creating Python venv at $HERE/.venv …"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip wheel setuptools

echo "[3/5] Installing Python deps (this builds llama-cpp-python — takes a few minutes)…"
# CMAKE_ARGS keeps the build CPU-only with OpenBLAS off to minimise RAM during build.
CMAKE_ARGS="-DGGML_NATIVE=ON" pip install -r requirements.txt

echo "[4/5] Seeding SQLite database…"
cd backend && python db/seed.py && cd "$HERE"

echo "[5/5] Done."
echo
echo "Next: ./scripts/download_model.sh   (downloads ~1.1 GB GGUF — run online ONCE)"
echo "Then: ./scripts/run.sh              (starts the offline portal)"
