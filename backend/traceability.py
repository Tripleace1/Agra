"""Harvest batch ledger with deterministic local trace IDs."""
from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from config import DB_PATH


@dataclass
class BatchInput:
    farmer_name: str
    location: str
    crop_type: str
    harvest_date: str   # YYYY-MM-DD
    weight_kg: float
    quality_grade: str  # A|B|C
    notes: Optional[str] = None


def _country_code(location: str) -> str:
    loc = location.lower()
    if any(k in loc for k in ("nigeria", "lagos", "ibadan", "kano", "abuja", "naij")):
        return "NG"
    if any(k in loc for k in ("tanzania", "dar es", "arusha")):
        return "TZ"
    if any(k in loc for k in ("kenya", "nairobi", "mombasa")):
        return "KE"
    if any(k in loc for k in ("ghana", "accra", "kumasi")):
        return "GH"
    if any(k in loc for k in ("uganda", "kampala")):
        return "UG"
    return "AF"


def _trace_id(batch: BatchInput) -> str:
    year = datetime.utcnow().year
    seed = f"{batch.farmer_name}|{batch.location}|{batch.crop_type}|{batch.harvest_date}|{batch.weight_kg}"
    h = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:4].upper()
    return f"AGRA-{_country_code(batch.location)}-{year}-{h}"


def register(batch: BatchInput) -> dict:
    trace_id = _trace_id(batch)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute(
            """INSERT INTO harvest_batches
               (trace_id, farmer_name, location, crop_type, harvest_date,
                weight_kg, quality_grade, notes)
               VALUES (?,?,?,?,?,?,?,?)""",
            (trace_id, batch.farmer_name, batch.location, batch.crop_type,
             batch.harvest_date, batch.weight_kg, batch.quality_grade, batch.notes),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM harvest_batches WHERE trace_id = ?", (trace_id,)
        ).fetchone()
        return dict(row)
    except sqlite3.IntegrityError:
        row = conn.execute(
            "SELECT * FROM harvest_batches WHERE trace_id = ?", (trace_id,)
        ).fetchone()
        return dict(row)
    finally:
        conn.close()


def list_batches(search: str = "", limit: int = 50) -> List[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    if search:
        like = f"%{search}%"
        rows = conn.execute(
            """SELECT * FROM harvest_batches
               WHERE trace_id LIKE ? OR farmer_name LIKE ?
                  OR location LIKE ? OR crop_type LIKE ?
               ORDER BY id DESC LIMIT ?""",
            (like, like, like, like, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM harvest_batches ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_batch(trace_id: str) -> Optional[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM harvest_batches WHERE trace_id = ?", (trace_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None
