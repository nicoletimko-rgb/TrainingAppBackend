"""Basketball workout API. Run locally with `python app.py`."""

import os
import sqlite3                      # Built-in database, so no new install is needed
from contextlib import contextmanager
from datetime import date, timedelta

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

load_dotenv()
app = Flask(__name__)

# Set FRONTEND_ORIGINS on Render to the exact origin(s) serving the frontend.
origins = [origin.strip() for origin in os.getenv(
    "FRONTEND_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500"
).split(",") if origin.strip()]
CORS(app, resources={r"/api/*": {"origins": origins}})

GOALS = {
    "shooting": "Shooting",
    "handling": "Ball handling",
    "finishing": "Finishing",
    "defense": "Defense",
    "conditioning": "Conditioning",
}
LEVELS = {"beginner", "intermediate", "advanced"}
SPACES = {"court", "small"}
STRENGTH_FOCUS = {"legs": "quadriceps", "core": "abdominals", "upper": "chest"}

# Each drill specifies what it needs. The selector only returns feasible drills.
DRILLS = {
    "shooting": [
        {"name": "Form shooting", "instruction": "Start close to the basket. Shoot with one hand, hold your follow-through, then add your guide hand.", "needs": ["ball", "hoop"]},
        {"name": "Five-spot catch and shoot", "instruction": "Take shots from five spots. Rebound your shot and track makes at each spot.", "needs": ["ball", "hoop", "court"]},
        {"name": "One-dribble pull-ups", "instruction": "From each wing, attack left and right for a balanced pull-up. Reset between reps.", "needs": ["ball", "hoop", "court"]},
        {"name": "Air-shot mechanics", "instruction": "Practice your shooting stance, upward motion, and follow-through toward a wall target. No basket required.", "needs": []},
        {"name": "Footwork into a shot pocket", "instruction": "Step into an imaginary pass, square your feet, and bring the ball into your shot pocket.", "needs": ["ball"]},
    ],
    "handling": [
        {"name": "Pound dribbles", "instruction": "Dribble low and firmly with each hand; keep your eyes up.", "needs": ["ball"]},
        {"name": "Crossovers and between-the-legs", "instruction": "Alternate moves at a controlled pace, then increase speed while keeping the ball close.", "needs": ["ball"]},
        {"name": "Change-of-pace attacks", "instruction": "Use a slow setup dribble, then accelerate for two dribbles; practice both hands.", "needs": ["ball", "court"]},
        {"name": "Shadow dribble footwork", "instruction": "Move through crossovers and retreat steps without a ball, keeping your stance low.", "needs": []},
    ],
    "finishing": [
        {"name": "Right- and left-hand layups", "instruction": "Alternate sides and focus on the correct two-step rhythm and soft touch.", "needs": ["ball", "hoop"]},
        {"name": "Reverse finish series", "instruction": "Approach from each baseline and use the far side of the rim as protection.", "needs": ["ball", "hoop", "court"]},
        {"name": "Two-step finishing footwork", "instruction": "Practice a controlled gather and two steps from both sides; finish with an imaginary layup.", "needs": []},
        {"name": "Gather and balance", "instruction": "Take one controlled dribble, gather, and stop on balance. Repeat on both sides.", "needs": ["ball"]},
    ],
    "defense": [
        {"name": "Defensive slides", "instruction": "Stay low, push off the trailing foot, and avoid crossing your feet.", "needs": []},
        {"name": "Closeout and contain", "instruction": "Run toward a marker, shorten your steps, raise a hand, and settle into a defensive stance.", "needs": []},
        {"name": "Slide-to-sprint transitions", "instruction": "Slide laterally, turn your hips, and sprint to the next marker.", "needs": ["court"]},
        {"name": "Mirror footwork", "instruction": "Alternate quick reactions to imaginary offensive moves, staying balanced.", "needs": []},
    ],
    "conditioning": [
        {"name": "Interval shuttles", "instruction": "Move between two markers at a strong pace, then walk to recover. Repeat.", "needs": ["court"]},
        {"name": "Jump rope simulation", "instruction": "Use light, quick steps and relaxed shoulders; a rope is optional.", "needs": []},
        {"name": "Lateral movement intervals", "instruction": "Alternate slides and easy recovery steps. Keep your chest upright.", "needs": []},
        {"name": "Tempo movement", "instruction": "Alternate brisk movement with easy walking in a small area.", "needs": []},
    ],
}


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/api/exercises")
def find_exercises():
    """Fetch real strength exercises without exposing the upstream API key."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Send a JSON object with focus and level."}), 400
    focus, level = data.get("focus"), data.get("level")
    if not isinstance(focus, str) or focus not in STRENGTH_FOCUS:
        return jsonify({"error": "Choose legs, core, or upper body."}), 400
    if not isinstance(level, str) or level not in LEVELS:
        return jsonify({"error": "Choose beginner, intermediate, or advanced."}), 400

    api_key = os.getenv("API_NINJAS_KEY")
    if not api_key:
        return jsonify({"error": "Exercise search is not configured yet. Add the API key on the backend."}), 503

    try:
        upstream = requests.get(
            "https://api.api-ninjas.com/v1/exercises",
            params={"muscle": STRENGTH_FOCUS[focus], "difficulty": "expert" if level == "advanced" else level},
            headers={"X-Api-Key": api_key},
            timeout=10,
        )
        if upstream.status_code == 429:
            return jsonify({"error": "The exercise service has reached its request limit. Try again later."}), 503
        if not upstream.ok:
            return jsonify({"error": "The exercise service could not complete this request. Check the server's API key and try again."}), 502
        exercises = upstream.json()
    except (requests.RequestException, ValueError):
        return jsonify({"error": "The exercise service is temporarily unavailable. Try again later."}), 502

    if not isinstance(exercises, list):
        return jsonify({"error": "The exercise service returned an unexpected response."}), 502
    cleaned = [
        {
            "name": item.get("name", "Exercise"),
            "muscle": item.get("muscle", ""),
            "difficulty": item.get("difficulty", ""),
            "instructions": item.get("instructions", "No instructions provided."),
            "equipment": item.get("equipments") if isinstance(item.get("equipments"), list) else [],
            "safety_info": item.get("safety_info", ""),
        }
        for item in exercises[:5] if isinstance(item, dict)
    ]
    return jsonify({"focus": focus, "level": level, "source": "API Ninjas Exercises API", "exercises": cleaned})


@app.post("/api/workouts")
def create_workout():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Send a JSON object with goal, minutes, level, space, and equipment."}), 400

    goal, level, space, minutes = (data.get(key) for key in ("goal", "level", "space", "minutes"))
    equipment = data.get("equipment")
    if not isinstance(goal, str) or goal not in GOALS:
        return jsonify({"error": "Choose a valid training goal."}), 400
    if type(minutes) is not int or minutes not in (20, 30, 45, 60):
        return jsonify({"error": "Choose 20, 30, 45, or 60 minutes."}), 400
    if not isinstance(level, str) or not isinstance(space, str) or level not in LEVELS or space not in SPACES:
        return jsonify({"error": "Choose a valid level and space."}), 400
    if not isinstance(equipment, list) or any(item not in ("ball", "hoop") for item in equipment):
        return jsonify({"error": "Equipment must be a list containing only ball and/or hoop."}), 400

    available = set(equipment)
    if space == "court":
        available.add("court")
    pool = [drill for drill in DRILLS[goal] if set(drill["needs"]).issubset(available)]
    # Every goal has a no-equipment fallback; keep a varied session if needed.
    supplementary = [drill for drill in DRILLS["defense"] if set(drill["needs"]).issubset(available)]
    selected = (pool + [d for d in supplementary if d not in pool])[:4]

    warmup = 4 if minutes == 20 else 5
    cooldown = 3 if minutes == 20 else 5
    work = minutes - warmup - cooldown
    base, remainder = divmod(work, len(selected))
    drills = [
        {"name": drill["name"], "minutes": base + (i < remainder), "instruction": drill["instruction"]}
        for i, drill in enumerate(selected)
    ]
    tips = {
        "beginner": "Go slowly enough to keep clean technique. Rest when needed.",
        "intermediate": "Track completed reps and build speed without losing control.",
        "advanced": "Maintain game pace and record makes, reps, or work intervals.",
    }
    return jsonify({
        "title": f"{GOALS[goal]} session",
        "total_minutes": minutes,
        "level": level,
        "sections": [
            {"name": "Warm-up", "minutes": warmup, "instruction": "Easy movement, dynamic stretches, and a few practice reps."},
            {"name": "Skill work", "minutes": work, "drills": drills},
            {"name": "Cool-down", "minutes": cooldown, "instruction": "Walk, breathe, and stretch comfortably."},
        ],
        "coach_note": tips[level],
    })


# =====================================================================
# DATABASE: saved workouts (plans) and logged sessions (what you did)
# =====================================================================

# Where the SQLite file lives. NOTE: Render's free tier wipes local files on
# each deploy. Attach a Render persistent disk and set DATABASE_PATH to it
# (e.g. /var/data/training.db), or move to Postgres, to keep data long-term.
DB_PATH = os.getenv("DATABASE_PATH", "training.db")

SCHEMA = """
-- A saved workout "template": a named list of drills the user built.
CREATE TABLE IF NOT EXISTS workouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,                       -- anonymous per-device id
    name TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
-- The drills inside a template, in order, with planned minutes and shots.
CREATE TABLE IF NOT EXISTS workout_drills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workout_id INTEGER NOT NULL REFERENCES workouts(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    minutes INTEGER NOT NULL,
    shots INTEGER NOT NULL                       -- planned shots (0 = not a shooting drill)
);
-- A logged session: one day the user actually trained.
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    performed_on TEXT NOT NULL,                  -- YYYY-MM-DD
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
-- Results for each drill in a session: time spent and shots made / attempted.
CREATE TABLE IF NOT EXISTS session_drills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    minutes INTEGER NOT NULL,
    shots_made INTEGER NOT NULL,
    shots_attempted INTEGER NOT NULL
);
"""


@contextmanager
def connect():
    """Open a connection, commit on success, and always close it."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row                # rows behave like dicts
    conn.execute("PRAGMA foreign_keys = ON")      # makes ON DELETE CASCADE work
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


with connect() as _conn:                          # create tables on startup
    _conn.executescript(SCHEMA)


def current_user():
    """The frontend sends a random id (X-User-Id header) that it stores in the
    browser. It separates one person's data from another's. It is NOT a login:
    anyone who knows an id can read that data. Add real accounts later if needed."""
    uid = request.headers.get("X-User-Id", "").strip()
    return uid if 8 <= len(uid) <= 64 else None


NO_USER = ({"error": "Missing user id."}, 400)


def num(value, high):
    """Return value if it is a whole number from 0 to high, otherwise None."""
    return value if type(value) is int and 0 <= value <= high else None


def clean_drills(raw, logging):
    """Validate a list of drills from the browser. Returns clean rows or None.
    logging=False -> a plan (minutes + planned shots).
    logging=True  -> results (minutes + shots made + shots attempted)."""
    if not isinstance(raw, list) or not 1 <= len(raw) <= 20:
        return None
    rows = []
    for item in raw:
        if not isinstance(item, dict):
            return None
        title, category = item.get("title"), item.get("category")
        minutes = num(item.get("minutes"), 300)
        if not isinstance(title, str) or not title.strip() or not isinstance(category, str) or minutes is None:
            return None
        row = {"title": title.strip()[:80], "category": category[:30], "minutes": minutes}
        if logging:
            made, attempted = num(item.get("shots_made"), 10000), num(item.get("shots_attempted"), 10000)
            if made is None or attempted is None or made > attempted:   # can't make more than you take
                return None
            row.update(shots_made=made, shots_attempted=attempted)
        else:
            shots = num(item.get("shots"), 10000)
            if shots is None:
                return None
            row["shots"] = shots
        rows.append(row)
    return rows


# NOTE: /api/workouts (POST) above already generates a suggested workout, so
# the user's own saved workouts live under /api/saved-workouts.

@app.get("/api/saved-workouts")
def list_saved_workouts():
    """Return every workout template this user has saved, newest first."""
    uid = current_user()
    if not uid:
        return jsonify(NO_USER[0]), NO_USER[1]
    with connect() as conn:
        workouts = []
        for w in conn.execute("SELECT id, name, created_at FROM workouts WHERE user_id = ? ORDER BY id DESC", (uid,)):
            drills = conn.execute(
                "SELECT title, category, minutes, shots FROM workout_drills WHERE workout_id = ? ORDER BY position",
                (w["id"],)).fetchall()
            workouts.append({**dict(w), "drills": [dict(x) for x in drills]})
    return jsonify({"workouts": workouts})


@app.post("/api/saved-workouts")
def save_workout():
    """Save a named workout template: {name, drills:[{title, category, minutes, shots}]}."""
    uid = current_user()
    if not uid:
        return jsonify(NO_USER[0]), NO_USER[1]
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Send a JSON object with name and drills."}), 400
    name = data.get("name")
    drills = clean_drills(data.get("drills"), logging=False)
    if not isinstance(name, str) or not name.strip():
        return jsonify({"error": "Give the workout a name."}), 400
    if drills is None:
        return jsonify({"error": "Add 1 to 20 valid drills."}), 400
    with connect() as conn:
        workout_id = conn.execute("INSERT INTO workouts (user_id, name) VALUES (?, ?)", (uid, name.strip()[:60])).lastrowid
        conn.executemany(
            "INSERT INTO workout_drills (workout_id, position, title, category, minutes, shots) VALUES (?, ?, ?, ?, ?, ?)",
            [(workout_id, i, d["title"], d["category"], d["minutes"], d["shots"]) for i, d in enumerate(drills)])
    return jsonify({"id": workout_id}), 201


@app.delete("/api/saved-workouts/<int:workout_id>")
def delete_workout(workout_id):
    """Delete one of this user's templates (its drills are removed by CASCADE)."""
    uid = current_user()
    if not uid:
        return jsonify(NO_USER[0]), NO_USER[1]
    with connect() as conn:
        conn.execute("DELETE FROM workouts WHERE id = ? AND user_id = ?", (workout_id, uid))
    return jsonify({"deleted": workout_id})


@app.post("/api/sessions")
def log_session():
    """Log a finished session: {name, performed_on:'YYYY-MM-DD', drills:[{title, category, minutes, shots_made, shots_attempted}]}."""
    uid = current_user()
    if not uid:
        return jsonify(NO_USER[0]), NO_USER[1]
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Send a JSON object with name, performed_on, and drills."}), 400
    name = data.get("name")
    try:
        day = date.fromisoformat(data.get("performed_on", ""))
    except (TypeError, ValueError):
        return jsonify({"error": "Choose a valid date."}), 400
    drills = clean_drills(data.get("drills"), logging=True)
    if not isinstance(name, str) or not name.strip():
        return jsonify({"error": "The session needs a name."}), 400
    if drills is None:
        return jsonify({"error": "Check your drills. Shots made cannot be more than shots attempted."}), 400
    with connect() as conn:
        session_id = conn.execute(
            "INSERT INTO sessions (user_id, name, performed_on) VALUES (?, ?, ?)",
            (uid, name.strip()[:60], day.isoformat())).lastrowid
        conn.executemany(
            "INSERT INTO session_drills (session_id, title, category, minutes, shots_made, shots_attempted) VALUES (?, ?, ?, ?, ?, ?)",
            [(session_id, d["title"], d["category"], d["minutes"], d["shots_made"], d["shots_attempted"]) for d in drills])
    return jsonify({"id": session_id}), 201


@app.get("/api/sessions")
def week_summary():
    """Sessions for the 7 days starting at ?week_start=YYYY-MM-DD, plus totals."""
    uid = current_user()
    if not uid:
        return jsonify(NO_USER[0]), NO_USER[1]
    try:
        start = date.fromisoformat(request.args.get("week_start", ""))
    except ValueError:
        return jsonify({"error": "week_start must look like 2025-06-02."}), 400
    end = start + timedelta(days=6)
    sessions, totals = [], {"sessions": 0, "minutes": 0, "shots_made": 0, "shots_attempted": 0}
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, name, performed_on FROM sessions WHERE user_id = ? AND performed_on BETWEEN ? AND ? "
            "ORDER BY performed_on, id", (uid, start.isoformat(), end.isoformat())).fetchall()
        for s in rows:
            drills = [dict(x) for x in conn.execute(
                "SELECT title, category, minutes, shots_made, shots_attempted FROM session_drills WHERE session_id = ? ORDER BY id",
                (s["id"],))]
            sessions.append({**dict(s), "drills": drills})
            totals["sessions"] += 1
            for d in drills:                      # add this drill into the weekly totals
                totals["minutes"] += d["minutes"]
                totals["shots_made"] += d["shots_made"]
                totals["shots_attempted"] += d["shots_attempted"]
    return jsonify({"week_start": start.isoformat(), "week_end": end.isoformat(), "totals": totals, "sessions": sessions})


@app.delete("/api/sessions/<int:session_id>")
def delete_session(session_id):
    """Delete one logged session belonging to this user."""
    uid = current_user()
    if not uid:
        return jsonify(NO_USER[0]), NO_USER[1]
    with connect() as conn:
        conn.execute("DELETE FROM sessions WHERE id = ? AND user_id = ?", (session_id, uid))
    return jsonify({"deleted": session_id})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
