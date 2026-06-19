# Agra — Offline Agricultural Advisor

Offline-first soil diagnosis, RAG chat, and crop traceability for African smallholders.
Built for **Ubuntu 22.04, 4 GB RAM, 256 GB storage**, with **English + Yorùbá** UI.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│ Browser (127.0.0.1:5000)                                │
│   vanilla JS + glassmorphism UI + i18n (EN / YO)        │
└──────────────────┬──────────────────────────────────────┘
                   │ HTTP (loopback only, no egress)
┌──────────────────▼──────────────────────────────────────┐
│ Flask app.py                                            │
│   ├─ soil.py        deterministic NPK/pH match          │
│   ├─ rag.py         SQLite FTS5 retrieval               │
│   ├─ llm.py         llama-cpp-python (Qwen2.5-1.5B)     │
│   └─ traceability.py harvest batch ledger               │
└──────────────────┬──────────────────────────────────────┘
                   │
            ┌──────▼───────┐    ┌────────────────────┐
            │ agra.sqlite  │    │ Qwen2.5-1.5B GGUF  │
            │ + FTS5 index │    │ ~1.1 GB Q4_K_M     │
            └──────────────┘    └────────────────────┘
```

## Model choice — ADTC submission vs. local dev

ADTC judges test on **7 GB RAM**, so the **submission default is Qwen2.5-3B**. Use the smaller models only for development on your 4 GB box.

| Model | Disk | RAM (load) | Tokens/s | Use |
|---|---|---|---|---|
| **Qwen2.5-3B-Instruct Q4_K_M** | ~2.2 GB | ~3.0 GB | 6–10 | **ADTC submission default** |
| Qwen2.5-1.5B-Instruct Q4_K_M | ~1.1 GB | ~1.5 GB | 7–12 | Dev on 4 GB laptop |
| Qwen2.5-0.5B-Instruct Q4_K_M | ~400 MB | ~700 MB | 18–25 | Tiny fallback |

The 3B target leaves ~3 GB headroom under the 7 GB ADTC ceiling — that converts to ~9 of 20 efficiency points in the official scoring formula.

Yorùbá note: Qwen2.5 understands Yorùbá at a passable but not fluent level. Soil diagnoses and ledger work translate cleanly (template strings); chat answers in YO may be uneven. For best YO chat fluency consider Aya-Expanse later; not available in <2 GB GGUF today.

## Install

```bash
cd ~/Documents/Agra
chmod +x scripts/*.sh
./scripts/install.sh          # apt + venv + pip + DB seed (~10 min, mostly llama-cpp compile)
./scripts/download_model.sh   # ~1.1 GB GGUF — only step that needs internet
```

## Run

```bash
./scripts/run.sh              # http://127.0.0.1:5000
```

## Test offline

After install + model download:

```bash
# 1. Disconnect WiFi / unplug ethernet.
# 2. Confirm: ping 8.8.8.8 should fail.
# 3. Start the app
./scripts/run.sh
# 4. In another terminal:
./scripts/verify_offline.sh
```

The verify script:
- Checks `/api/health` on `127.0.0.1:5000`.
- Lists every TCP socket the Python process opened (should be loopback only).
- Hits `/api/chat` while internet is cut and confirms a real answer comes back.
- Tries to reach `huggingface.co` — failure here proves you're truly offline.

For a hard guarantee, also block egress at the firewall:

```bash
sudo ufw default deny outgoing
sudo ufw default allow incoming
sudo ufw allow in on lo
sudo ufw allow out on lo
sudo ufw enable
```

(Re-enable later with `sudo ufw disable`.)

## Performance verification

In one terminal:
```bash
./scripts/run.sh
```
In another:
```bash
./scripts/benchmark.sh
```
You should see:
- RSS after inference: **< 2.5 GB**
- Avg tokens/s: **> 6** (1.5B on Intel 8th-gen i5)
- CPU temp: **< 82 °C**

## Optimisations applied

1. **`n_ctx=2048`** — caps context so KV cache stays small (~150 MB).
2. **`n_threads=min(nproc, 4)`** — prevents thermal throttling on tight chassis.
3. **`use_mmap=True, use_mlock=False`** — model pages can swap if memory pressure spikes.
4. **`n_batch=256`** — balances prompt-processing throughput against RAM.
5. **Chat history capped at 4 turns** — `llm._trim_history()` keeps prompts under 1024 tokens.
6. **FTS5 with `porter unicode61` tokeniser** — millisecond-range retrieval; no embedding model needed → saves 100+ MB RAM.
7. **Lazy LLM load** — model only loads on first `/api/chat`, so soil diagnosis & ledger work instantly.
8. **Fallback summaries** — soil diagnosis works even if the model is missing.
9. **Vanilla JS frontend** — no React/Vue, browser uses <250 MB.

## API endpoints

| Method | Path | Body |
|---|---|---|
| GET | `/api/health` | – |
| POST | `/api/soil/diagnose` | `{soil_type, ph, n, p, k, lang, summarize}` |
| POST | `/api/chat` | `{prompt, lang, history}` |
| POST | `/api/chat/stream` | same — text/plain stream |
| POST | `/api/trace/register` | `{farmer_name, location, crop_type, harvest_date, weight_kg, quality_grade, notes?}` |
| GET | `/api/trace/list?q=…` | – |
| GET | `/api/trace/<trace_id>` | – |

## Troubleshooting

| Symptom | Fix |
|---|---|
| Install hangs at `Building llama-cpp-python` | Normal — takes 8–15 min on i5. Watch RAM with `htop`. |
| `ModuleNotFoundError` at runtime | `source .venv/bin/activate` was missed; `./scripts/run.sh` handles it. |
| Chat returns 503 "Model not found" | Run `./scripts/download_model.sh`. |
| Out-of-memory during chat | Switch to 0.5B model: re-run `download_model.sh` and choose option 2. |
| YO chat answers in English | Small models drift; use `lang=yo` consistently. |
