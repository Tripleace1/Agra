<div align="center">

# 🌾 Agra — Offline Agricultural Advisor

**Soil diagnosis · RAG chat · Crop traceability — for African smallholders, fully offline.**

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg?style=for-the-badge)](LICENSE)
[![Platform: Ubuntu 22.04](https://img.shields.io/badge/Platform-Ubuntu_22.04-E95420?style=for-the-badge&logo=ubuntu&logoColor=white)](https://ubuntu.com/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Model: Qwen2.5](https://img.shields.io/badge/LLM-Qwen2.5_3B-FF6F00?style=for-the-badge)](https://huggingface.co/Qwen)
[![Offline-first](https://img.shields.io/badge/Offline-first-2E7D32?style=for-the-badge)](#-test-offline)
[![i18n: EN · YO](https://img.shields.io/badge/i18n-EN_·_Yorùbá-008751?style=for-the-badge)](#-yorùbá--ní-èdè-yorùbá)
[![Track: Agriculture](https://img.shields.io/badge/ADTC_Track-Agriculture-4CAF50?style=for-the-badge)](#)

_No cloud. No tracking. No internet. Just the soil, the seed, and the farmer._

</div>

---

## ✨ What is Agra?

**Agra** is an offline-first AI assistant built for smallholder farmers in West Africa. It runs entirely on a modest laptop — **4 GB RAM, 256 GB disk, no internet** — and helps with:

| 🌱 | **Soil diagnosis** — deterministic NPK + pH matching, no model required |
|---|---|
| 💬 | **RAG agronomy chat** — SQLite FTS5 retrieval grounding a local Qwen2.5 LLM |
| 📒 | **Harvest traceability** — per-batch ledger for organic / origin claims |
| 🌍 | **Bilingual UI** — English + **Yorùbá**, with glassmorphism vanilla-JS frontend |

> 💡 Built for the **ADTC Agriculture Track**. Submission default targets the 7 GB judging environment with Qwen2.5-**3B**.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│  🖥️  Browser  (127.0.0.1:5000)                          │
│       vanilla JS · glassmorphism · i18n (EN / YO)       │
└────────────────────────┬────────────────────────────────┘
                         │   HTTP — loopback only
┌────────────────────────▼────────────────────────────────┐
│  🐍  Flask  app.py                                       │
│      ├─ soil.py          deterministic NPK / pH match    │
│      ├─ rag.py           SQLite FTS5 retrieval           │
│      ├─ llm.py           llama-cpp-python  (Qwen2.5)    │
│      └─ traceability.py  harvest batch ledger            │
└─────────┬───────────────────────────────┬────────────────┘
          │                               │
   ┌──────▼────────┐               ┌──────▼─────────────┐
   │ 🗄  agra.sqlite│               │ 🧠 Qwen2.5 GGUF    │
   │   + FTS5 idx  │               │   ~2.2 GB Q4_K_M   │
   └───────────────┘               └────────────────────┘
```

---

## 🎯 Model choice — ADTC submission vs. local dev

| Model | Disk | RAM (load) | Tokens/s | Use |
|---|---|---|---|---|
| 🥇 **Qwen2.5-3B-Instruct Q4_K_M** | ~2.2 GB | ~3.0 GB | 6–10 | **ADTC submission default** |
| 🥈 Qwen2.5-1.5B-Instruct Q4_K_M | ~1.1 GB | ~1.5 GB | 7–12 | Dev on 4 GB laptop |
| 🥉 Qwen2.5-0.5B-Instruct Q4_K_M | ~400 MB | ~700 MB | 18–25 | Tiny fallback |

The 3B target leaves **~3 GB headroom** under the 7 GB ADTC ceiling — worth ~9 of 20 efficiency points in the official scoring formula.

> 🪶 **Yorùbá note:** Qwen2.5 understands Yorùbá at a passable but not fluent level. Soil diagnoses and ledger work translate cleanly (template strings); chat answers in YO may be uneven. See [`scripts/eval/results/`](scripts/eval/results/) for current YO accuracy.

---

## 🚀 Install

```bash
cd ~/Documents/Agra
chmod +x scripts/*.sh
./scripts/install.sh          # apt + venv + pip + DB seed (~10 min, mostly llama-cpp compile)
./scripts/download_model.sh   # ~2.2 GB GGUF — only step that needs internet
```

## ▶️ Run

```bash
./scripts/run.sh              # http://127.0.0.1:5000
```

---

## 🔌 Test offline

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
- ✅ Checks `/api/health` on `127.0.0.1:5000`.
- ✅ Lists every TCP socket the Python process opened (should be loopback only).
- ✅ Hits `/api/chat` while internet is cut and confirms a real answer comes back.
- ✅ Tries to reach `huggingface.co` — failure here proves you're truly offline.

For a hard guarantee, also block egress at the firewall:

```bash
sudo ufw default deny outgoing
sudo ufw default allow incoming
sudo ufw allow in on lo
sudo ufw allow out on lo
sudo ufw enable
```

_(Re-enable later with `sudo ufw disable`.)_

---

## 📊 Performance verification

In one terminal:
```bash
./scripts/run.sh
```
In another:
```bash
./scripts/benchmark.sh
```
You should see:
- 📉 RSS after inference: **< 2.5 GB**
- ⚡ Avg tokens/s: **> 6** (1.5B on Intel 8th-gen i5)
- 🌡️ CPU temp: **< 82 °C**

---

## 🛠 Optimisations applied

1. **`n_ctx=2048`** — caps context so KV cache stays small (~150 MB).
2. **`n_threads=min(nproc, 4)`** — prevents thermal throttling on tight chassis.
3. **`use_mmap=True, use_mlock=False`** — model pages can swap if memory pressure spikes.
4. **`n_batch=256`** — balances prompt-processing throughput against RAM.
5. **Chat history capped at 4 turns** — `llm._trim_history()` keeps prompts under 1024 tokens.
6. **FTS5 with `porter unicode61` tokeniser** — millisecond-range retrieval; no embedding model needed → saves 100+ MB RAM.
7. **Lazy LLM load** — model only loads on first `/api/chat`, so soil diagnosis & ledger work instantly.
8. **Fallback summaries** — soil diagnosis works even if the model is missing.
9. **Vanilla JS frontend** — no React/Vue, browser uses <250 MB.

---

## 🌐 API endpoints

| Method | Path | Body |
|---|---|---|
| `GET`  | `/api/health` | – |
| `POST` | `/api/soil/diagnose` | `{soil_type, ph, n, p, k, lang, summarize}` |
| `POST` | `/api/chat` | `{prompt, lang, history}` |
| `POST` | `/api/chat/stream` | same — `text/plain` stream |
| `POST` | `/api/trace/register` | `{farmer_name, location, crop_type, harvest_date, weight_kg, quality_grade, notes?}` |
| `GET`  | `/api/trace/list?q=…` | – |
| `GET`  | `/api/trace/<trace_id>` | – |

---

## 🧪 Evaluation

The eval harness (`scripts/eval/run_eval.py`) replays a golden Q+A set through the live Flask API, measuring:

- 🎯 **Accuracy** — weighted keyword-overlap on `must_include` / `must_not_include`
- ⚡ **Tokens/sec** — end-to-end latency-based
- 🧠 **Peak RSS** — VmRSS of the backend process
- 🌡️ **CPU temp** — highest core during the run (if `lm-sensors` installed)

```bash
./scripts/run.sh                      # terminal A
python scripts/eval/run_eval.py       # terminal B
```

Reports drop into [`scripts/eval/results/`](scripts/eval/results/) as `.json` + `.md`. Categories include **soil, pest, irrigation, rotation, season, crop, traceability, reasoning, edge** plus a **Yorùbá** subset.

---

## 🌍 Yorùbá — Ní èdè Yorùbá

> Àgbé tí ó wà ní abúlé, kò gbọ́dọ̀ wà ní ọ̀nà jíjìn sí ìmọ̀.
> _A farmer in the village should never be far from knowledge._

**Agra** jẹ́ olùrànlọ́wọ́ àgbẹ̀ tí ó ń ṣiṣẹ́ **láìsí ìntánẹ́ẹ̀tì**. Ó ń ràn àwọn àgbẹ̀ kéékèèké lọ́wọ́ ní Áfríkà láti:

- 🌱 **Ṣàyẹ̀wò ilẹ̀** — wo bí pH ilẹ̀ ṣe rí, kí o sì mọ irú èròjà tí ó nílò (nitrogen, phosphorus, potassium).
- 💬 **Bá olùkọ́ àgbẹ̀ AI sọ̀rọ̀** — bi ìbéèrè nípa àrùn ọ̀gbìn, kòkòrò, tàbí àkókò gbígbìn — ní èdè Yorùbá tàbí Gẹ̀ẹ́sì.
- 📒 **Tọ́jú àkọsílẹ̀ ìkórè** — fún ìfìdí ìpilẹ̀ṣẹ̀ ọjà rẹ múlẹ̀, kí àwọn olùrà lè mọ ibi tí ó ti wá.

### 🔧 Bí a ṣe lè fi sí ẹ̀rọ

```bash
cd ~/Documents/Agra
./scripts/install.sh          # Fi gbogbo ohun èlò sí ẹ̀rọ
./scripts/download_model.sh   # Gba awòṣe Qwen2.5 (ìgbà yìí nìkan ni ìntánẹ́ẹ̀tì nílò)
./scripts/run.sh              # Ṣí olùpín náà — ìntánẹ́ẹ̀tì kò sí ní ìṣíṣẹ́ rárá
```

Lẹ́yìn náà, ṣí ẹ̀rọ ìwòran rẹ kí o sì lọ sí **http://127.0.0.1:5000**. Yan **Yorùbá** ní ojú-ìwé akọ́kọ́, kí o sì bẹ̀rẹ̀.

### 📌 Àkíyèsí

Awòṣe Qwen2.5 mọ Yorùbá ní ìpele kékeré. Ìdáhùn fún àyẹ̀wò ilẹ̀ àti ìwé ìkórè ti gba ìtumọ̀ kíkún, ṣùgbọ́n ìjíròrò gbígbòòrò ní Yorùbá lè má pé pérépéré ní gbogbo ìgbà. A ń ṣiṣẹ́ lórí àwọn awòṣe Yorùbá tí ó dára jù lọ.

---

## 🩹 Troubleshooting

| Symptom | Fix |
|---|---|
| Install hangs at `Building llama-cpp-python` | Normal — takes 8–15 min on i5. Watch RAM with `htop`. |
| `ModuleNotFoundError` at runtime | `source .venv/bin/activate` was missed; `./scripts/run.sh` handles it. |
| Chat returns 503 "Model not found" | Run `./scripts/download_model.sh`. |
| Out-of-memory during chat | Switch to 0.5B model: re-run `download_model.sh` and choose option 2. |
| YO chat answers in English | Small models drift; use `lang=yo` consistently. |

---

## 🤝 Contributing

Pull requests welcome — see [`CONTRIBUTING.md`](CONTRIBUTING.md). For bigger ideas, open an issue first.

## 📜 License

Released under the [Apache License 2.0](LICENSE). © 2026 Agra contributors.

<div align="center">

_Made with 🌱 for the farmers who feed the continent._

</div>
