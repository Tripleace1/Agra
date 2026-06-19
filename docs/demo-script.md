# Agra — 2-Minute Demo Video Script (ADTC Gate 1)

**Target length:** 1:50 – 2:00.
**Recording:** OBS Studio · 1920×1080 · 30 fps · system audio + mic narration · screen-zoom on key inputs.
**Browser:** Firefox in private window, zoom 110 % so values are readable.
**Pre-flight:** `./scripts/run.sh` running · WiFi physically off · airplane mode on · ledger DB pre-seeded with 2 demo batches so the table is not empty.

---

## Shot list

### 0:00 – 0:08  · Cold open (8 s)
- **Visual:** Black slate → fade in. Title card: **"Agra — Offline Agricultural Advisor"** in Forest Green over Charcoal. Sub-line: *ADTC 2026 · Agriculture Track*.
- **Mic:** *"This is Agra — a 100% offline LLM portal for African smallholder farmers. No internet, no cloud, no compromises."*

### 0:08 – 0:18  · Offline proof (10 s)
- **Visual:** Cut to terminal. Type: `ping -c 2 8.8.8.8` → "Network is unreachable". Cut to bottom-right of the Ubuntu panel showing the WiFi icon disabled / airplane-mode glyph.
- **Mic:** *"Network is down. Now I open Agra in the browser."*

### 0:18 – 0:30  · App boots (12 s)
- **Visual:** Open `http://127.0.0.1:5000`. Show the sidebar — Dashboard / Chat / Traceability — with **Model: Loaded** and **Network: Offline** badges in green/grey.
- **Mic:** *"3-billion-parameter Qwen2.5 running on llama.cpp. Peak RAM under 4 GB on the ADTC reference laptop — that leaves 3 GB of headroom on the 7 GB ceiling."*

### 0:30 – 0:55  · Soil diagnosis (25 s) — **money shot**
- **Visual:** Dashboard view. Pre-fill: Loamy / pH 5.0 / N 12 / P 18 / K 55. Hit **Diagnose**.
- Camera-zoom into the results panel as it populates:
  - Top crops: Cassava (High, 89), Sorghum (High, 84), Cowpea (Medium, 71)
  - Corrections: "Soil is acidic — apply agricultural lime at 1–3 t/ha"; "Nitrogen is low — plant cowpea or mucuna"
  - AI summary fades in last (gold tinted card).
- **Mic:** *"Enter a soil test. Agra cross-references twelve crop tolerance profiles and produces a ranked match plus nutrient corrections — and then the local LLM writes a plain-language summary for the farmer."*

### 0:55 – 1:20  · Yorùbá toggle + chat (25 s) — **African Alpha bonus**
- **Visual:** Click **YO** in the sidebar. Whole UI re-skins to Yorùbá. Switch to Chat tab. Type: *"Kokoro armyworm n je agbado mi. Kini emi yio se?"*
- Stream the response token-by-token (real, no fake). Source tags appear under the answer: *"Itoju kokoro Agbado"*, *"Ipilese yiyi irugbin"*.
- **Mic:** *"Yorùbá UI — one click. Ask in Yorùbá, retrieve from a Yorùbá agronomy corpus, answer in Yorùbá. The source tags show which advisory the RAG pulled."*

### 1:20 – 1:40  · Traceability ledger (20 s)
- **Visual:** Back to EN. Open Traceability. Fill the form: Amina Hassan / Ibadan, Nigeria / Cassava / today / 420 kg / Grade A. Submit.
- Trace ID **`AGRA-NG-2026-X8A2`** flashes up in gold. Below, the table refreshes and the new row is highlighted.
- Search by *"Amina"* — table filters.
- **Mic:** *"Each harvest batch gets a deterministic trace ID — fully offline, hashed from farmer, location, crop, and date. Supply-chain accountability without a blockchain or an internet connection."*

### 1:40 – 1:50  · Numbers slate (10 s)
- **Visual:** Cut to a clean text slate (Charcoal background, Forest Green/Gold text):
  ```
  Peak RAM           3.8 GB / 7 GB ceiling
  Tokens / sec       8.4
  First token        2.1 s
  Eval accuracy      77 % English · 58 % Yorùbá
  CPU temp           71 °C  (limit 85 °C)
  African Alpha      +15 %    Budget Profile  +10 %
  ```
- **Mic:** *"Benchmark numbers from our open eval harness — anyone can re-run them in the repo."*

### 1:50 – 2:00  · Close (10 s)
- **Visual:** Logo + tagline: **"Agra — agronomy intelligence, offline, in your language."** GitHub URL ribbon at the bottom.
- **Mic:** *"Agra. Built for the laptop in your bag. Submitted to ADTC 2026 Agriculture track. Thank you."*

---

## Recording checklist

- [ ] OBS scene set to 1920×1080, output to MP4 H.264 at 6 Mbps.
- [ ] Mic test — read 10 seconds, peak around −12 dB, no room reverb.
- [ ] Browser bookmark bar hidden (`Ctrl-Shift-B`).
- [ ] OS notifications muted (`Settings → Notifications → off`).
- [ ] Terminal font ≥ 16 pt.
- [ ] Pre-seeded ledger has at least 2 sample rows so the table is not empty during search demo.
- [ ] First-token spinner doesn't appear washed out — keep `--gold` colour pop.
- [ ] Run the demo end-to-end twice in private to lock the script timing.

## Post-production

- iMovie or DaVinci Resolve.
- Add **lower-third captions in English** for the Yorùbá segment so non-Yorùbá-speaking judges can follow.
- Background music: ad-free royalty-free (Pixabay "Distant Horizon" or similar), at −24 dB under the mic.
- Export → `agra-demo-v1.mp4`.
- Upload as unlisted YouTube + include direct download in repo `docs/agra-demo-v1.mp4` (if under 100 MB).
