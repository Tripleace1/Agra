"""Agra / ShambaAdvisor — offline Flask portal entry point."""
from __future__ import annotations

import logging
import os
import traceback
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory, Response, stream_with_context
from flask_cors import CORS

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(message)s")

from config import HOST, PORT
import soil as soil_mod
import traceability as trace_mod
import rag
import llm

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"

app = Flask(
    __name__,
    static_folder=str(FRONTEND / "static"),
    static_url_path="/static",
    template_folder=str(FRONTEND / "templates"),
)
CORS(app, resources={r"/api/*": {"origins": "http://127.0.0.1:*"}})


@app.errorhandler(Exception)
def _print_exception(e):
    traceback.print_exc()
    return jsonify({"error": f"{type(e).__name__}: {e}"}), 500


@app.route("/")
def index():
    return send_from_directory(FRONTEND / "templates", "index.html")


@app.route("/api/health")
def health():
    return jsonify({
        "ok": True,
        "model_present": llm.model_present(),
        "model_loaded": llm.is_loaded(),
    })


@app.route("/api/soil/diagnose", methods=["POST"])
def soil_diagnose():
    body = request.get_json(force=True) or {}
    try:
        inp = soil_mod.SoilInput(
            soil_type=str(body.get("soil_type", "loamy")),
            ph=float(body.get("ph", 6.5)),
            n=float(body.get("n", 30)),
            p=float(body.get("p", 25)),
            k=float(body.get("k", 100)),
            lang=str(body.get("lang", "en")),
        )
    except (TypeError, ValueError) as e:
        return jsonify({"error": f"invalid input: {e}"}), 400

    result = soil_mod.diagnose(inp)
    if body.get("summarize"):
        try:
            result["summary"] = llm.summarize_soil(result, lang=inp.lang)
        except Exception as e:
            result["summary"] = f"(LLM summary unavailable: {e})"
    return jsonify(result)


@app.route("/api/chat", methods=["POST"])
def chat():
    body = request.get_json(force=True) or {}
    prompt = str(body.get("prompt", "")).strip()
    lang = str(body.get("lang", "en"))
    history = body.get("history", [])
    if not prompt:
        return jsonify({"error": "prompt required"}), 400

    snippets = rag.retrieve(prompt, lang=lang)
    context = rag.format_context(snippets)

    try:
        answer = llm.chat(prompt, context, history, lang=lang)
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        return jsonify({"error": f"LLM error: {e}"}), 500

    return jsonify({
        "answer": answer,
        "sources": [
            {"title": s["title"], "category": s["category"]}
            for s in snippets
        ],
    })


@app.route("/api/chat/stream", methods=["POST"])
def chat_stream():
    body = request.get_json(force=True) or {}
    prompt = str(body.get("prompt", "")).strip()
    lang = str(body.get("lang", "en"))
    history = body.get("history", [])
    if not prompt:
        return jsonify({"error": "prompt required"}), 400

    snippets = rag.retrieve(prompt, lang=lang)
    context = rag.format_context(snippets)

    def gen():
        for tok in llm.chat_stream(prompt, context, history, lang=lang):
            yield tok

    return Response(stream_with_context(gen()), mimetype="text/plain")


@app.route("/api/chat/sources", methods=["POST"])
def chat_sources():
    body = request.get_json(force=True) or {}
    prompt = str(body.get("prompt", "")).strip()
    lang = str(body.get("lang", "en"))
    snippets = rag.retrieve(prompt, lang=lang)
    return jsonify({
        "sources": [
            {"title": s["title"], "category": s["category"]}
            for s in snippets
        ]
    })


@app.route("/api/trace/register", methods=["POST"])
def trace_register():
    body = request.get_json(force=True) or {}
    required = ["farmer_name", "location", "crop_type", "harvest_date", "weight_kg", "quality_grade"]
    for k in required:
        if k not in body:
            return jsonify({"error": f"missing field: {k}"}), 400
    try:
        b = trace_mod.BatchInput(
            farmer_name=str(body["farmer_name"]),
            location=str(body["location"]),
            crop_type=str(body["crop_type"]),
            harvest_date=str(body["harvest_date"]),
            weight_kg=float(body["weight_kg"]),
            quality_grade=str(body["quality_grade"]).upper()[:1],
            notes=str(body.get("notes", "")) or None,
        )
    except (TypeError, ValueError) as e:
        return jsonify({"error": f"invalid input: {e}"}), 400
    return jsonify(trace_mod.register(b))


@app.route("/api/trace/list", methods=["GET"])
def trace_list():
    q = request.args.get("q", "").strip()
    return jsonify({"batches": trace_mod.list_batches(search=q)})


@app.route("/api/trace/<trace_id>", methods=["GET"])
def trace_get(trace_id):
    b = trace_mod.get_batch(trace_id)
    if not b:
        return jsonify({"error": "not found"}), 404
    return jsonify(b)


if __name__ == "__main__":
    # Force local binding — no external network exposure.
    app.run(host=HOST, port=PORT, debug=False, threaded=True)
