"""llama-cpp-python wrapper. Lazy-loads model on first use to keep boot fast."""
from __future__ import annotations

import threading
import time
from typing import Iterator, List

from config import (
    MODEL_PATH, N_CTX, N_THREADS, N_BATCH,
    MAX_TOKENS, TEMPERATURE, TOP_P, CHAT_HISTORY_TURNS,
    CACHE_TYPE_K, CACHE_TYPE_V, COOLDOWN_S,
)

_llm = None
_llm_lock = threading.Lock()


def _load():
    global _llm
    if _llm is not None:
        return _llm
    with _llm_lock:
        if _llm is not None:
            return _llm
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Model not found: {MODEL_PATH}. "
                f"Run scripts/download_model.sh first."
            )
        from llama_cpp import Llama
        kwargs = dict(
            model_path=str(MODEL_PATH),
            n_ctx=N_CTX,
            n_threads=N_THREADS,
            n_batch=N_BATCH,
            use_mmap=True,
            use_mlock=False,
            verbose=False,
        )
        # KV-cache quantisation cuts RAM ~40%; supported in newer llama-cpp-python.
        # Fall back to plain load on ANY failure so a quant-incompatible build
        # never blocks inference.
        try:
            _llm = Llama(type_k=8, type_v=8, **kwargs)  # 8 = GGML_TYPE_Q4_0
        except Exception as e:
            print(f"[llm] KV quant unavailable ({type(e).__name__}: {e}); loading without it.")
            _llm = Llama(**kwargs)
        return _llm


SYSTEM_EN = (
    "You are Agra, an offline agricultural advisor for African smallholder farmers. "
    "Answer in clear, practical English. Use the provided context when relevant; "
    "if context does not cover the question, answer from general agricultural knowledge "
    "and clearly say so. Keep answers under 200 words."
)

SYSTEM_YO = (
    "Iwo ni Agra, oluranlowo ogbin ti ko nilo internet fun awon agbe Afrika. "
    "Dahun ni Yoruba ti o yebiye, ni ona ti o rorun. Lo ohun ti a fun o nigbati o ye, "
    "ti ko ba ye, dahun lati imo ogbin gbogbogbo ki o so o han. Dahun ni isalẹ ọrọ 200."
)


def _trim_history(history: List[dict]) -> List[dict]:
    """Cap chat history at CHAT_HISTORY_TURNS (user+assistant pairs)."""
    if not history:
        return []
    pairs = []
    cur = []
    for msg in history:
        cur.append(msg)
        if msg.get("role") == "assistant":
            pairs.append(cur)
            cur = []
    if cur:
        pairs.append(cur)
    pairs = pairs[-CHAT_HISTORY_TURNS:]
    out = []
    for p in pairs:
        out.extend(p)
    return out


def chat(prompt: str, context: str, history: List[dict], lang: str = "en") -> str:
    """Non-streaming single-shot completion."""
    llm = _load()
    system = SYSTEM_YO if lang == "yo" else SYSTEM_EN
    if context:
        system += "\n\nContext:\n" + context

    messages = [{"role": "system", "content": system}]
    messages.extend(_trim_history(history))
    messages.append({"role": "user", "content": prompt})

    out = llm.create_chat_completion(
        messages=messages,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        top_p=TOP_P,
        stream=False,
    )
    return out["choices"][0]["message"]["content"].strip()


def chat_stream(prompt: str, context: str, history: List[dict], lang: str = "en") -> Iterator[str]:
    llm = _load()
    system = SYSTEM_YO if lang == "yo" else SYSTEM_EN
    if context:
        system += "\n\nContext:\n" + context
    messages = [{"role": "system", "content": system}]
    messages.extend(_trim_history(history))
    messages.append({"role": "user", "content": prompt})

    for chunk in llm.create_chat_completion(
        messages=messages,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        top_p=TOP_P,
        stream=True,
    ):
        delta = chunk["choices"][0].get("delta", {}).get("content")
        if delta:
            yield delta
            if COOLDOWN_S > 0:
                time.sleep(COOLDOWN_S)


def summarize_soil(diagnosis: dict, lang: str = "en") -> str:
    """Short LLM-generated summary of soil diagnosis. Falls back to template if model unavailable."""
    try:
        llm = _load()
    except FileNotFoundError:
        return _fallback_summary(diagnosis, lang)

    top = diagnosis["crops"][:3]
    crop_lines = "\n".join(
        f"- {c['name']} ({c['suitability']}, score {c['score']}): {'; '.join(c['reasons'][:2])}"
        for c in top
    )
    corr = "\n".join(f"- {c}" for c in diagnosis["corrections"])
    inp = diagnosis["input"]
    prompt = (
        f"Soil test: type={inp['soil_type']} pH={inp['ph']} N={inp['n']} P={inp['p']} K={inp['k']} mg/kg.\n"
        f"Top 3 crops:\n{crop_lines}\n\nCorrections:\n{corr}\n\n"
        "Write a 3-4 sentence practical summary for the farmer."
    )
    system = SYSTEM_YO if lang == "yo" else SYSTEM_EN
    out = llm.create_chat_completion(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        max_tokens=220,
        temperature=0.3,
        top_p=0.9,
        stream=False,
    )
    return out["choices"][0]["message"]["content"].strip()


def _fallback_summary(diagnosis: dict, lang: str) -> str:
    top = [c["name"] for c in diagnosis["crops"][:3]]
    corr = diagnosis["corrections"][0] if diagnosis["corrections"] else ""
    if lang == "yo":
        return f"Awọn irugbin ti o dara julọ: {', '.join(top)}. {corr}"
    return f"Best-suited crops: {', '.join(top)}. {corr}"


def is_loaded() -> bool:
    return _llm is not None


def model_present() -> bool:
    return MODEL_PATH.exists()
