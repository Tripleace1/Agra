# Contributing to Agra

Thank you for considering a contribution. Agra is built for the **Africa Deep Tech Challenge 2026** and beyond, so contributions that make the offline experience faster, more accurate, or more accessible to African languages are the most valuable.

## Ground rules

1. **Stay offline.** We know that code path may call an external network during runtime. PRs that add cloud APIs, telemetry, or CDN-loaded assets will be closed.
2. **Stay within the RAM budget.** Peak resident set must remain comfortably under 7 GB on the ADTC reference laptop. Benchmark before and after with `scripts/eval/run_eval.py` and include the deltas in the PR description.
3. **Stay in llama.cpp.** GGUF + `llama-cpp-python` is the only inference path. PRs that swap in a different runtime will not be merged for this contest cycle.
4. **Add tests or eval items, not assumptions.** If you change the soil engine or the RAG retrieval, extend `scripts/eval/golden.json` with at least one item that proves the change.

## How to set up

```bash
git clone <fork-url>
cd Agra
chmod +x scripts/*.sh
./scripts/install.sh
./scripts/download_model.sh        # pick option 1 (Qwen2.5-3B)
./scripts/run.sh                   # http://127.0.0.1:5000
```

## How to make a change

1. Branch from `main`:
   ```bash
   git checkout -b feat/<short-name>
   ```
2. Run the eval **before** your change and save the JSON:
   ```bash
   python scripts/eval/run_eval.py
   mv scripts/eval/results/eval-*.json scripts/eval/results/baseline.json
   ```
3. Make your change. Keep it tightly scoped.
4. Run the eval **after**:
   ```bash
   python scripts/eval/run_eval.py
   ```
5. Open a PR that includes:
   - One-paragraph description of what changed and why.
   - Diff of accuracy / tokens-per-second / peak RSS vs. baseline.
   - Screenshot of the UI if the change is visible.

## What we want most

- **More African languages.** Hausa, Swahili, Wolof, Igbo, Amharic — each needs a parallel advisory set in `backend/db/seed.py`. Aim for the same 13 topics as the English/Yorùbá set so retrieval stays balanced.
- **More crops.** Cocoa, oil palm, plantain varieties, soybean, sesame. Extend the `CROPS` list in `backend/db/seed.py` with realistic NPK and pH bands sourced from a published agronomy reference. Cite the source in the PR.
- **Better Yorùbá fluency.** If you're a fluent Yorùbá speaker and notice stilted output, propose template-string rewrites in `frontend/static/i18n/yo.json` and corpus rewrites in `seed.py`.
- **Speed wins.** KV-cache tweaks, prompt template trimming, prompt cache reuse across calls — anything that moves tokens-per-second up without raising peak RSS.

## What we will not accept (for the contest cycle)

- Refactors for their own sake. Wait until after Gate 3 (September 15, 2026).
- New JavaScript frameworks. Vanilla JS keeps the browser footprint small.
- Embedding-model-based retrieval. FTS5 is intentionally chosen for its zero-RAM-cost profile.
- Telemetry, analytics, or any "phone home" feature, even opt-in.

## Code style

- **Python:** 4-space indent, type hints on public functions, no print-debugging left in.
- **JavaScript:** 2-space indent, vanilla ES2020, no transpiler.
- **CSS:** custom properties (`--var`) at `:root`. No utility-class frameworks.
- **SQL:** keep schema migrations additive; never drop columns inside a release.

## Reporting bugs

Open a GitHub issue with:

1. **OS + RAM** of the machine you tested on.
2. **Model file** (`ls -lh backend/models/`).
3. **Steps to reproduce** — exact form values or chat prompt.
4. **What you expected** vs. **what happened**.
5. Output of `curl -s http://127.0.0.1:5000/api/health`.

## License

By contributing, you agree that your contributions are licensed under the Apache License 2.0, same as the project.
