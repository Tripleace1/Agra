import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = BASE_DIR / "db" / "agra.sqlite"
MODELS_DIR = BASE_DIR / "models"

MODEL_FILENAME = os.environ.get("AGRA_MODEL", "qwen2.5-3b-instruct-q4_k_m.gguf")
MODEL_PATH = MODELS_DIR / MODEL_FILENAME

N_CTX = 2048
# Default: use physical cores only (not SMT/hyperthreads) to halve heat.
# Override per-machine via AGRA_THREADS env var.
N_THREADS = int(os.environ.get("AGRA_THREADS", "2"))
N_BATCH = int(os.environ.get("AGRA_N_BATCH", "128"))
MAX_TOKENS = 384
TEMPERATURE = 0.4
TOP_P = 0.9
# Quantise KV cache to q4_0 to cut RAM by ~40% with negligible accuracy loss.
CACHE_TYPE_K = "q4_0"
CACHE_TYPE_V = "q4_0"
# Cooldown sleep between tokens (seconds). 0 = off. Set 0.02-0.05 on a hot box.
COOLDOWN_S = float(os.environ.get("AGRA_COOLDOWN", "0"))

CHAT_HISTORY_TURNS = 4
RAG_TOP_K = 3

HOST = "127.0.0.1"
PORT = 5000
