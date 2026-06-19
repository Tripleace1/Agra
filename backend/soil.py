"""Soil diagnosis engine — pure-Python NPK/pH matching against crop tolerance."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import List

from config import DB_PATH


@dataclass
class SoilInput:
    soil_type: str       # sandy | loamy | clay | silt
    ph: float
    n: float             # mg/kg
    p: float
    k: float
    lang: str = "en"


@dataclass
class CropMatch:
    name: str
    name_yo: str
    suitability: str     # High | Medium | Low
    score: int           # 0-100
    reasons: List[str]
    season_notes: str


def _band(value: float, lo: float, hi: float) -> tuple[int, str]:
    """Return (score 0-100, deficit label) for a nutrient band."""
    if lo <= value <= hi:
        return 100, "ok"
    if value < lo:
        gap = (lo - value) / lo if lo > 0 else 1.0
        score = max(0, int(100 - gap * 100))
        return score, "low"
    gap = (value - hi) / hi if hi > 0 else 1.0
    score = max(0, int(100 - gap * 100))
    return score, "high"


def diagnose(inp: SoilInput) -> dict:
    soil_type = inp.soil_type.strip().lower()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM crops").fetchall()
    conn.close()

    results: list[CropMatch] = []
    for r in rows:
        reasons: list[str] = []

        soil_ok = soil_type in r["soil_types"].split(",")
        if not soil_ok:
            reasons.append(
                f"Prefers {r['soil_types']} soil"
                if inp.lang == "en"
                else f"Fẹran ilẹ {r['soil_types']}"
            )

        ph_score, ph_state = _band(inp.ph, r["ph_min"], r["ph_max"])
        if ph_state == "low":
            reasons.append(
                f"pH too acidic (target {r['ph_min']}-{r['ph_max']})"
                if inp.lang == "en"
                else f"pH ti ekan ju (ami: {r['ph_min']}-{r['ph_max']})"
            )
        elif ph_state == "high":
            reasons.append(
                f"pH too alkaline (target {r['ph_min']}-{r['ph_max']})"
                if inp.lang == "en"
                else f"pH ti mimo ju (ami: {r['ph_min']}-{r['ph_max']})"
            )

        n_score, n_state = _band(inp.n, r["n_min"], r["n_max"])
        if n_state == "low":
            reasons.append("Nitrogen low" if inp.lang == "en" else "Nitrogen ko peye")
        elif n_state == "high":
            reasons.append("Nitrogen excessive" if inp.lang == "en" else "Nitrogen ti po ju")

        p_score, p_state = _band(inp.p, r["p_min"], r["p_max"])
        if p_state == "low":
            reasons.append("Phosphorus low" if inp.lang == "en" else "Phosphorus ko peye")
        elif p_state == "high":
            reasons.append("Phosphorus excessive" if inp.lang == "en" else "Phosphorus ti po ju")

        k_score, k_state = _band(inp.k, r["k_min"], r["k_max"])
        if k_state == "low":
            reasons.append("Potassium low" if inp.lang == "en" else "Potassium ko peye")
        elif k_state == "high":
            reasons.append("Potassium excessive" if inp.lang == "en" else "Potassium ti po ju")

        total = int(
            (ph_score * 0.25)
            + (n_score * 0.20)
            + (p_score * 0.20)
            + (k_score * 0.20)
            + ((100 if soil_ok else 30) * 0.15)
        )
        if total >= 80:
            suit = "High"
        elif total >= 55:
            suit = "Medium"
        else:
            suit = "Low"

        results.append(
            CropMatch(
                name=r["name"],
                name_yo=r["name_yo"] or r["name"],
                suitability=suit,
                score=total,
                reasons=reasons or (["All parameters within range"] if inp.lang == "en" else ["Gbogbo wa ni iwon"]),
                season_notes=(r["season_notes_yo"] if inp.lang == "yo" else r["season_notes"]) or "",
            )
        )

    results.sort(key=lambda x: x.score, reverse=True)
    corrections = _corrections(inp)

    return {
        "input": {
            "soil_type": soil_type,
            "ph": inp.ph,
            "n": inp.n,
            "p": inp.p,
            "k": inp.k,
            "lang": inp.lang,
        },
        "crops": [c.__dict__ for c in results],
        "corrections": corrections,
    }


def _corrections(inp: SoilInput) -> list[str]:
    yo = inp.lang == "yo"
    out: list[str] = []

    if inp.ph < 5.5:
        out.append("Soil is acidic. Apply agricultural lime at 1-3 t/ha and incorporate well." if not yo
                   else "Ilẹ ti ekan. Lo orombo oko ni 1-3 t/ha kí o sì pa á pọ̀ dáadáa.")
    elif inp.ph > 7.5:
        out.append("Soil is alkaline. Add composted organic matter or elemental sulfur to lower pH." if not yo
                   else "Ilẹ ti mimo. Fi compost tàbí sulfur kún kí pH lè dín kù.")

    if inp.n < 20:
        out.append("Nitrogen is low. Apply well-rotted compost, plant nitrogen-fixing legumes (cowpea, mucuna), or use urea at 50-80 kg/ha split-applied." if not yo
                   else "Nitrogen kò pé. Lo compost ti o ti pọ́n, gbin èwà tàbí mucuna, tàbí urea ni 50-80 kg/ha.")
    if inp.p < 15:
        out.append("Phosphorus is low. Apply rock phosphate or bone meal and incorporate into top 15 cm." if not yo
                   else "Phosphorus kò pé. Lo rock phosphate tàbí iyẹ̀ egungun, kí o sì pa á sí ilẹ̀ centimita 15 òkè.")
    if inp.k < 60:
        out.append("Potassium is low. Apply wood ash sparingly or muriate of potash at 50-80 kg/ha." if not yo
                   else "Potassium kò pé. Lo eeru igi díẹ̀díẹ̀ tàbí muriate of potash ni 50-80 kg/ha.")

    if not out:
        out.append("Nutrient levels are within typical recommended ranges. Maintain with compost rotation." if not yo
                   else "Ìwọ̀n ohun-èlò pẹ̀lú àpẹrẹ ìṣòro. Pa á mọ́ pẹ̀lú compost yíyí.")
    return out
