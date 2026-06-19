#!/usr/bin/env bash
# Downloads Qwen2.5-Instruct GGUF.  ADTC judges run on 7 GB RAM, so 3B is default.
# Run ONCE while you still have internet. After this you can go fully offline.
set -euo pipefail
HERE="$(cd "$(dirname "$0")"/.. && pwd)"
MODEL_DIR="$HERE/backend/models"
mkdir -p "$MODEL_DIR"

choose_model() {
  echo
  echo "Choose model size:"
  echo "  1) Qwen2.5-3B-Instruct  Q4_K_M  (~2.2 GB disk, ~3.0 GB RAM)  [ADTC submission — recommended]"
  echo "  2) Qwen2.5-1.5B-Instruct Q4_K_M (~1.1 GB disk, ~1.5 GB RAM)  [dev on 4 GB box]"
  echo "  3) Qwen2.5-0.5B-Instruct Q4_K_M (~400 MB disk, ~700 MB RAM)  [tiny fallback]"
  read -rp "Selection [1]: " CHOICE
  CHOICE=${CHOICE:-1}
  case "$CHOICE" in
    1) FILE="qwen2.5-3b-instruct-q4_k_m.gguf"
       URL="https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf?download=true" ;;
    2) FILE="qwen2.5-1.5b-instruct-q4_k_m.gguf"
       URL="https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf?download=true" ;;
    3) FILE="qwen2.5-0.5b-instruct-q4_k_m.gguf"
       URL="https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf?download=true" ;;
    *) echo "Invalid choice"; exit 1 ;;
  esac
}

choose_model

DEST="$MODEL_DIR/$FILE"
if [[ -f "$DEST" ]]; then
  SIZE=$(stat -c%s "$DEST")
  if (( SIZE > 100000000 )); then
    echo "Model already present: $DEST ($((SIZE/1024/1024)) MB) — skipping."
    exit 0
  fi
fi

echo "Downloading $FILE …"
curl -L --fail --progress-bar -o "$DEST.part" "$URL"
mv "$DEST.part" "$DEST"

echo
echo "Saved to: $DEST"
echo "Export AGRA_MODEL=$FILE  to lock this model for ./scripts/run.sh"
