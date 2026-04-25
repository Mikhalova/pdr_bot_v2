"""База даних: питання ПДР + статистика користувачів."""

import sqlite3
import json
from typing import Optional, List
from config import DB_PATH


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS questions (
            id          INTEGER PRIMARY KEY,
            topic_id    INTEGER,
            topic_name  TEXT,
            ticket_id   INTEGER,
            question    TEXT NOT NULL,
            image_url   TEXT,
            answer_a    TEXT,
            answer_b    TEXT,
            answer_c    TEXT,
            answer_d    TEXT,
            answer_e    TEXT,
            correct     TEXT NOT NULL,
            explanation TEXT,
            source_url  TEXT
        );

        CREATE TABLE IF NOT EXISTS topics (
            id   INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS user_stats (
            user_id  INTEGER PRIMARY KEY,
            tests    INTEGER DEFAULT 0,
            correct  INTEGER DEFAULT 0,
            wrong    INTEGER DEFAULT 0,
            streak   INTEGER DEFAULT 0,
            mistakes TEXT DEFAULT '[]'
        );
    """)
    conn.commit()
    conn.close()


def load_from_json(path: str):
    """Завантажити питання з questions.json."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    conn = get_conn()
    for q in data:
        conn.execute("""
            INSERT OR REPLACE INTO questions
                (id, topic_id, topic_name, ticket_id, question, image_url,
                 answer_a, answer_b, answer_c, answer_d, answer_e,
                 correct, explanation)
            VALUES
                (:id, :topic_id, :topic_name, :ticket_id, :question, :image_url,
                 :answer_a, :answer_b, :answer_c, :answer_d, :answer_e,
                 :correct, :explanation)
        """, {
            "id":          q.get("id"),
            "topic_id":    q.get("topic_id"),
            "topic_name":  q.get("topic_name", ""),
            "ticket_id":   q.get("ticket_id"),
            "question":    q.get("question", ""),
            "image_url":   q.get("image_url"),
            "answer_a":    q.get("answer_a"),
            "answer_b":    q.get("answer_b"),
            "answer_c":    q.get("answer_c"),
            "answer_d":    q.get("answer_d"),
            "answer_e":    q.get("answer_e"),
            "correct":     q.get("correct", "a"),
            "explanation": q.get("explanation"),
        })

        topic_id = q.get("topic_id")
        topic_name = q.get("topic_name", "")
        if topic_id and topic_name:
            conn.execute(
                "INSERT OR IGNORE INTO topics (id, name) VALUES (?, ?)",
                (topic_id, topic_name)
            )

    conn.commit()
    conn.close()


def is_db_populated() -> bool:
    conn = get_conn()
    count = conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
    conn.close()
    return count > 0


def get_topics() -> List[dict]:
    conn = get_conn()
    rows = conn.execute("SELECT id, name FROM topics ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_tickets() -> List[int]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT DISTINCT ticket_id FROM questions WHERE ticket_id IS NOT NULL ORDER BY ticket_id"
    ).fetchall()
    conn.close()
    return [r[0] for r in rows]


def get_questions_by_topic(topic_id: int) -> List[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM questions WHERE topic_id=? ORDER BY id", (topic_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_questions_by_ticket(ticket_id: int) -> List[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM questions WHERE ticket_id=? ORDER BY id", (ticket_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_random_questions(count: int = 20) -> List[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM questions ORDER BY RANDOM() LIMIT ?", (count,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_mistake_questions(user_id: int) -> List[dict]:
    conn = get_conn()
    row = conn.execute(
        "SELECT mistakes FROM user_stats WHERE user_id=?", (user_id,)
    ).fetchone()
    conn.close()
    if not row:
        return []
    ids = json.loads(row["mistakes"])
    if not ids:
        return []
    conn = get_conn()
    placeholders = ",".join("?" * len(ids))
    rows = conn.execute(
        f"SELECT * FROM questions WHERE id IN ({placeholders})", ids
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_stats(user_id: int) -> dict:
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM user_stats WHERE user_id=?", (user_id,)
    ).fetchone()
    conn.close()
    if not row:
        return {"tests": 0, "correct": 0, "wrong": 0, "streak": 0, "percent": 0}
    d = dict(row)
    total = d["correct"] + d["wrong"]
    d["percent"] = round(d["correct"] / total * 100) if total else 0
    return d


def update_stats(user_id: int, correct: bool, question_id: Optional[int] = None):
    conn = get_conn()
    conn.execute("""
        INSERT INTO user_stats (user_id, tests, correct, wrong, streak, mistakes)
        VALUES (?, 0, 0, 0, 0, '[]')
        ON CONFLICT(user_id) DO NOTHING
    """, (user_id,))

    if correct:
        conn.execute("""
            UPDATE user_stats SET correct=correct+1, streak=streak+1 WHERE user_id=?
        """, (user_id,))
        if question_id:
            row = conn.execute("SELECT mistakes FROM user_stats WHERE user_id=?", (user_id,)).fetchone()
            mistakes = json.loads(row["mistakes"])
            if question_id in mistakes:
                mistakes.remove(question_id)
                conn.execute("UPDATE user_stats SET mistakes=? WHERE user_id=?",
                             (json.dumps(mistakes), user_id))
    else:
        conn.execute("""
            UPDATE user_stats SET wrong=wrong+1, streak=0 WHERE user_id=?
        """, (user_id,))
        if question_id:
            row = conn.execute("SELECT mistakes FROM user_stats WHERE user_id=?", (user_id,)).fetchone()
            mistakes = json.loads(row["mistakes"])
            if question_id not in mistakes:
                mistakes.append(question_id)
                conn.execute("UPDATE user_stats SET mistakes=? WHERE user_id=?",
                             (json.dumps(mistakes), user_id))

    conn.commit()
    conn.close()


def increment_tests(user_id: int):
    conn = get_conn()
    conn.execute("""
        INSERT INTO user_stats (user_id, tests, correct, wrong, streak, mistakes)
        VALUES (?, 1, 0, 0, 0, '[]')
        ON CONFLICT(user_id) DO UPDATE SET tests=tests+1
    """, (user_id,))
    conn.commit()
    conn.close()
