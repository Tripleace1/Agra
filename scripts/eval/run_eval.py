"""Agra evaluation harness.

Runs the golden Q+A set through the local Flask API (so it tests the SAME
RAG + LLM path the judges will hit), measures:

  - accuracy   : weighted keyword-overlap score per item
  - tokens/sec : measured from end-to-end response time
  - peak RAM   : VmRSS of the backend Python process
  - cpu temp   : highest core temp during the run (if lm-sensors installed)

Writes a JSON + Markdown report to scripts/eval/results/.

Usage:
  # In terminal A:
  ./scripts/run.sh
  # In terminal B:
  python scripts/eval/run_eval.py
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from urllib import request as urlreq

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
GOLDEN = HERE / "golden.json"
OUT_DIR = HERE / "results"
OUT_DIR.mkdir(exist_ok=True)

API = os.environ.get("AGRA_API", "http://127.0.0.1:5000")


def http_post(path: str, payload: dict, timeout: int = 120) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urlreq.Request(
        f"{API}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    with urlreq.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def http_get(path: str) -> dict:
    with urlreq.urlopen(f"{API}{path}", timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))


def find_backend_pid() -> int | None:
    # run.sh execs `python app.py` from inside backend/, so the cmdline is just
    # "python app.py" with no path prefix.  Match that, then verify cwd.
    for pat in ("python.*app\\.py", "backend/app.py", "app.py"):
        try:
            out = subprocess.check_output(["pgrep", "-f", pat]).decode().strip()
            for pid in out.splitlines():
                try:
                    cwd = os.readlink(f"/proc/{pid}/cwd")
                    if "Agra" in cwd or "agra" in cwd:
                        return int(pid)
                except (FileNotFoundError, PermissionError):
                    continue
            if out:
                return int(out.splitlines()[0])
        except subprocess.CalledProcessError:
            continue
    return None


def rss_mb(pid: int) -> float:
    try:
        with open(f"/proc/{pid}/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    kb = int(line.split()[1])
                    return kb / 1024.0
    except FileNotFoundError:
        pass
    return 0.0


def max_core_temp() -> float | None:
    try:
        out = subprocess.check_output(["sensors"], stderr=subprocess.DEVNULL).decode()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    best = 0.0
    for m in re.finditer(r"\+([0-9]+(?:\.[0-9]+)?)°C", out):
        v = float(m.group(1))
        if v > best:
            best = v
    return best or None


def score_item(item: dict, answer: str) -> tuple[float, list[str]]:
    txt = answer.lower()
    notes = []
    hits = 0
    for kw in item["must_include"]:
        if kw.lower() in txt:
            hits += 1
        else:
            notes.append(f"missed '{kw}'")
    inc_score = hits / max(1, len(item["must_include"]))
    pen = 0
    for kw in item.get("must_not_include", []):
        if kw.lower() in txt:
            pen += 1
            notes.append(f"banned '{kw}' present")
    score = max(0.0, inc_score - 0.5 * pen)
    return score, notes


def main():
    print("== Agra evaluation ==")
    golden = json.loads(GOLDEN.read_text())
    items = golden["items"]
    print(f"Loaded {len(items)} items")

    try:
        health = http_get("/api/health")
    except Exception as e:
        print(f"FATAL: backend unreachable at {API}: {e}")
        sys.exit(1)
    print(f"Backend health: {health}")
    if not health.get("model_present"):
        print("FATAL: model not present. Run scripts/download_model.sh first.")
        sys.exit(1)

    pid = find_backend_pid()
    print(f"Backend PID: {pid}")

    print("Warming up the model…")
    try:
        http_post("/api/chat", {"prompt": "hello", "lang": "en", "history": []}, timeout=180)
    except Exception as e:
        print(f"Warm-up failed: {e}")
        sys.exit(1)

    results = []
    cat_scores: dict[str, list[float]] = {}
    lang_scores: dict[str, list[float]] = {}
    total_tokens = 0
    total_secs = 0.0
    peak_rss = 0.0
    peak_temp = 0.0

    for i, item in enumerate(items, 1):
        t0 = time.time()
        try:
            resp = http_post(
                "/api/chat",
                {"prompt": item["prompt"], "lang": item["lang"], "history": []},
                timeout=180,
            )
            answer = resp.get("answer", "")
        except Exception as e:
            answer = f"[ERROR: {e}]"
        dt = time.time() - t0
        tok = max(1, int(len(answer.split()) * 1.3))
        total_tokens += tok
        total_secs += dt

        score, notes = score_item(item, answer)
        cat_scores.setdefault(item["category"], []).append(score)
        lang_scores.setdefault(item["lang"], []).append(score)

        if pid:
            r = rss_mb(pid)
            if r > peak_rss:
                peak_rss = r
        t = max_core_temp()
        if t and t > peak_temp:
            peak_temp = t

        marker = "✓" if score >= 0.75 else ("~" if score >= 0.4 else "✗")
        print(f"  [{i:02d}/{len(items)}] {marker} {item['id']:10s} score={score:.2f}  {dt:5.1f}s  {tok:3d} tok  "
              f"rss={peak_rss:5.0f}MB  notes={'; '.join(notes) if notes else 'ok'}")

        results.append({
            "id": item["id"],
            "lang": item["lang"],
            "category": item["category"],
            "prompt": item["prompt"],
            "answer": answer,
            "score": score,
            "notes": notes,
            "latency_s": round(dt, 2),
            "tokens_est": tok,
        })

    overall = sum(r["score"] for r in results) / len(results)
    tps = total_tokens / total_secs if total_secs > 0 else 0
    cat_avg = {k: round(sum(v) / len(v), 3) for k, v in cat_scores.items()}
    lang_avg = {k: round(sum(v) / len(v), 3) for k, v in lang_scores.items()}

    summary = {
        "model": os.environ.get("AGRA_MODEL", "(default)"),
        "items": len(items),
        "overall_accuracy": round(overall, 3),
        "tokens_per_second": round(tps, 2),
        "peak_rss_mb": round(peak_rss, 1),
        "peak_cpu_temp_c": peak_temp or None,
        "by_category": cat_avg,
        "by_language": lang_avg,
    }

    stamp = time.strftime("%Y%m%d-%H%M%S")
    (OUT_DIR / f"eval-{stamp}.json").write_text(json.dumps(
        {"summary": summary, "results": results}, indent=2, ensure_ascii=False))

    md = [
        "# Agra Evaluation Report",
        f"_Generated {time.strftime('%Y-%m-%d %H:%M:%S')}_",
        "",
        f"- **Model:** `{summary['model']}`",
        f"- **Overall accuracy:** **{summary['overall_accuracy'] * 100:.1f}%** ({summary['items']} items)",
        f"- **Tokens/sec (avg):** {summary['tokens_per_second']}",
        f"- **Peak RSS:** {summary['peak_rss_mb']} MB  →  ADTC efficiency points = "
        f"`{(7000 - summary['peak_rss_mb']) / 7000 * 100:.1f}` × 0.20 = "
        f"{(7000 - summary['peak_rss_mb']) / 7000 * 100 * 0.20:.1f}",
        f"- **Peak CPU temp:** {summary['peak_cpu_temp_c']} °C  "
        f"({'OK' if (summary['peak_cpu_temp_c'] or 0) < 82 else 'WARN'})",
        "",
        "## Accuracy by category",
        "| Category | Accuracy |",
        "|---|---|",
    ]
    for k, v in sorted(cat_avg.items(), key=lambda x: -x[1]):
        md.append(f"| {k} | {v * 100:.0f}% |")
    md += ["", "## Accuracy by language", "| Lang | Accuracy |", "|---|---|"]
    for k, v in lang_avg.items():
        md.append(f"| {k} | {v * 100:.0f}% |")

    (OUT_DIR / f"eval-{stamp}.md").write_text("\n".join(md))

    print()
    print("== SUMMARY ==")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    print(f"\nReports → {OUT_DIR}/eval-{stamp}.{{json,md}}")


if __name__ == "__main__":
    main()
