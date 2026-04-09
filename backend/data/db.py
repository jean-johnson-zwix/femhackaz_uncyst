"""
SQLite memory store for PCOS Classifier.

Tables
------
users           — one row per user; tracks current subtype + onboarding date
subtype_history — every classification result (enables drift detection)
lab_history     — every bloodwork upload / manual entry
goal_log        — daily goal check-ins
xp_ledger       — XP total + earned badges per user
"""

import json
import sqlite3
import os
from contextlib import contextmanager
from datetime import date, datetime
from typing import Optional

DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "pcos.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id             TEXT PRIMARY KEY,
    subtype             TEXT,
    onboarding_date     TEXT NOT NULL,
    -- profile fields (nullable until onboarding is completed)
    name                TEXT,
    age                 INTEGER,
    diagnosed_pcos      TEXT,     -- 'yes' | 'no' | 'unsure'
    goals               TEXT,     -- JSON array of goal strings
    cycle_length_days   INTEGER,
    trying_to_conceive  INTEGER,  -- 0 | 1
    physician_aware     INTEGER   -- 0 | 1
);

CREATE TABLE IF NOT EXISTS subtype_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     TEXT    NOT NULL,
    subtype     TEXT    NOT NULL,
    confidence  TEXT    NOT NULL,
    scores      TEXT    NOT NULL,  -- JSON
    timestamp   TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS lab_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     TEXT    NOT NULL,
    bloodwork   TEXT    NOT NULL,  -- JSON
    timestamp   TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS goal_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     TEXT    NOT NULL,
    goal_id     TEXT    NOT NULL,
    goal_date   TEXT    NOT NULL,  -- ISO date YYYY-MM-DD
    completed   INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS xp_ledger (
    user_id     TEXT PRIMARY KEY,
    xp_total    INTEGER NOT NULL DEFAULT 0,
    badges      TEXT    NOT NULL DEFAULT '[]'  -- JSON array of badge names
);
"""


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(SCHEMA)
        conn.commit()


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── Users ──────────────────────────────────────────────────────────────────────

def upsert_user(user_id: str, subtype: str) -> None:
    today = date.today().isoformat()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO users (user_id, subtype, onboarding_date)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET subtype = excluded.subtype
            """,
            (user_id, subtype, today),
        )


def get_user(user_id: str) -> Optional[dict]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
    if not row:
        return None
    d = dict(row)
    if d.get("goals"):
        d["goals"] = json.loads(d["goals"])
    return d


def upsert_profile(
    user_id: str,
    name: Optional[str],
    age: Optional[int],
    diagnosed_pcos: Optional[str],
    goals: Optional[list],
    cycle_length_days: Optional[int],
    trying_to_conceive: Optional[bool],
    physician_aware: Optional[bool],
) -> None:
    today = date.today().isoformat()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO users (
                user_id, onboarding_date,
                name, age, diagnosed_pcos, goals,
                cycle_length_days, trying_to_conceive, physician_aware
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                name               = excluded.name,
                age                = excluded.age,
                diagnosed_pcos     = excluded.diagnosed_pcos,
                goals              = excluded.goals,
                cycle_length_days  = excluded.cycle_length_days,
                trying_to_conceive = excluded.trying_to_conceive,
                physician_aware    = excluded.physician_aware
            """,
            (
                user_id,
                today,
                name,
                age,
                diagnosed_pcos,
                json.dumps(goals) if goals is not None else None,
                cycle_length_days,
                int(trying_to_conceive) if trying_to_conceive is not None else None,
                int(physician_aware) if physician_aware is not None else None,
            ),
        )


# ── Subtype history ────────────────────────────────────────────────────────────

def add_subtype_history(user_id: str, subtype: str, confidence: str, scores: dict) -> bool:
    """
    Persists a classification result. Returns True if the subtype changed
    from the previous record (drift detected).
    """
    ts = datetime.utcnow().isoformat()
    with get_conn() as conn:
        prev = conn.execute(
            "SELECT subtype FROM subtype_history WHERE user_id = ? ORDER BY id DESC LIMIT 1",
            (user_id,),
        ).fetchone()
        drift = bool(prev and prev["subtype"] != subtype)

        conn.execute(
            """
            INSERT INTO subtype_history (user_id, subtype, confidence, scores, timestamp)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, subtype, confidence, json.dumps(scores), ts),
        )
    return drift


def get_subtype_history(user_id: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM subtype_history WHERE user_id = ? ORDER BY id DESC",
            (user_id,),
        ).fetchall()
    return [dict(r) for r in rows]


# ── Lab history ────────────────────────────────────────────────────────────────

def add_lab_history(user_id: str, bloodwork: dict) -> None:
    ts = datetime.utcnow().isoformat()
    non_null = {k: v for k, v in bloodwork.items() if v is not None}
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO lab_history (user_id, bloodwork, timestamp) VALUES (?, ?, ?)",
            (user_id, json.dumps(non_null), ts),
        )


def get_lab_history(user_id: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM lab_history WHERE user_id = ? ORDER BY id DESC",
            (user_id,),
        ).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d["bloodwork"] = json.loads(d["bloodwork"])
        result.append(d)
    return result


# ── Goal log ───────────────────────────────────────────────────────────────────

def log_goal(user_id: str, goal_id: str, goal_date: str, completed: bool) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO goal_log (user_id, goal_id, goal_date, completed)
            VALUES (?, ?, ?, ?)
            ON CONFLICT DO NOTHING
            """,
            (user_id, goal_id, goal_date, int(completed)),
        )


def update_goal(user_id: str, goal_id: str, goal_date: str, completed: bool) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO goal_log (user_id, goal_id, goal_date, completed)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, goal_id, goal_date) DO UPDATE SET completed = excluded.completed
            """,
            (user_id, goal_id, goal_date, int(completed)),
        )


def get_goal_log(user_id: str, since_date: Optional[str] = None) -> list[dict]:
    with get_conn() as conn:
        if since_date:
            rows = conn.execute(
                "SELECT * FROM goal_log WHERE user_id = ? AND goal_date >= ? ORDER BY goal_date DESC",
                (user_id, since_date),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM goal_log WHERE user_id = ? ORDER BY goal_date DESC",
                (user_id,),
            ).fetchall()
    return [dict(r) for r in rows]


def get_streak(user_id: str) -> int:
    """
    Returns the current consecutive-day completion streak.
    A day counts if at least one goal was completed on that date.
    """
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT goal_date
            FROM goal_log
            WHERE user_id = ? AND completed = 1
            GROUP BY goal_date
            ORDER BY goal_date DESC
            """,
            (user_id,),
        ).fetchall()

    if not rows:
        return 0

    dates = [date.fromisoformat(r["goal_date"]) for r in rows]
    streak = 1
    for i in range(1, len(dates)):
        if (dates[i - 1] - dates[i]).days == 1:
            streak += 1
        else:
            break
    return streak


# ── XP ledger ──────────────────────────────────────────────────────────────────

def get_xp(user_id: str) -> dict:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT xp_total, badges FROM xp_ledger WHERE user_id = ?", (user_id,)
        ).fetchone()
    if row:
        return {"xp_total": row["xp_total"], "badges": json.loads(row["badges"])}
    return {"xp_total": 0, "badges": []}


def add_xp(user_id: str, delta: int, new_badges: Optional[list[str]] = None) -> dict:
    """
    Adds XP and optionally appends badges. Returns updated XP state.
    """
    current = get_xp(user_id)
    new_xp = current["xp_total"] + delta
    merged_badges = list(set(current["badges"]) | set(new_badges or []))

    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO xp_ledger (user_id, xp_total, badges)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                xp_total = excluded.xp_total,
                badges   = excluded.badges
            """,
            (user_id, new_xp, json.dumps(merged_badges)),
        )
    return {"xp_total": new_xp, "badges": merged_badges}
