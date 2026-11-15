"""Pure workout validation and exercise formatting logic."""

DRILL_KINDS = {"basketball", "strength"}


# validate a number. it only allows whole integers from 0 through high
def num(value, high):
    """Return value if it is a whole number from 0 to high, otherwise None."""
    return value if type(value) is int and 0 <= value <= high else None

# validate drills before saving it in the database
def clean_drills(raw, logging):
    """Validate a list of drills from the browser. Returns clean rows or None.
    logging=False -> a plan (minutes + planned shots).
    logging=True  -> results (minutes + shots made + shots attempted)."""
    # data must be a list with 1-20 drills
    if not isinstance(raw, list) or not 1 <= len(raw) <= 20:
        return None
    rows = []
    # for each drill, it must be a dictionary with title and category and minutes must be integer between 0 and 300
    for item in raw:
        if not isinstance(item, dict):
            return None
        title = item.get("title")
        kind = item.get("kind", "basketball")
        # Strength API exercises can use the default "Strength" category;
        # basketball drills still need the category supplied by the frontend.
        category = item.get("category", "Strength" if kind == "strength" else None)
        minutes = num(item.get("minutes"), 300)
        if (not isinstance(title, str) or not title.strip() or kind not in DRILL_KINDS
                or not isinstance(category, str) or not category.strip() or minutes is None):
            return None
        row = {
            "title": title.strip()[:80],
            "category": category.strip()[:30],
            "kind": kind,
            "minutes": minutes
        }
        if logging:
            made, attempted = num(item.get("shots_made"), 10000), num(item.get("shots_attempted"), 10000)
            if made is None or attempted is None:
                return None

            if kind != "strength" and made > attempted:
                return None
            row.update(shots_made=made, shots_attempted=attempted)
        else: # logging false thn this is a saved plan, so check only planned shots
            shots = num(item.get("shots"), 10000)
            if shots is None:
                return None
            row["shots"] = shots
        rows.append(row)
    return rows


def clean_exercises(exercises):
    """Convert upstream exercise data into the existing API response format."""
    cleaned = [
        {
            "name": item.get("name", "Exercise"),
            "muscle": item.get("muscle", ""),
            "difficulty": item.get("difficulty", ""),
            "instructions": item.get("instructions", "No instructions provided."),
            "equipment": item.get("equipments") if isinstance(item.get("equipments"), list) else [],
            "safety_info": item.get("safety_info", ""),
            # These fields let the frontend add an API exercise directly to a
            # saved plan or a logged session without inventing shot statistics.
            "workout_drill": {
                "title": item.get("name", "Exercise"),
                "category": "Strength",
                "kind": "strength",
                "minutes": 10,
                "shots": 0,
                "shots_made": 0,
                "shots_attempted": 0,
            },
        }
        for item in exercises[:4] if isinstance(item, dict) # cleans first five exercises before giving them to the frontend
        # TODO - does this mean only allowed 5 exercises?
    ]
    return cleaned