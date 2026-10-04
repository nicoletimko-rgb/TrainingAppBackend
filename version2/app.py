"""Basketball workout API. Run locally with `python app.py`."""

import os

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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
