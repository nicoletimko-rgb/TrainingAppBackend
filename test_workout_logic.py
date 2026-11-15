"""Tests for the existing pure workout logic (no implementation changes)."""

from workout_logic import num, clean_drills, clean_exercises

# valid integer
def test_num_valid_integer():
    assert num(15, 300) == 15

# lower boundary
def test_num_lower_boundary():
    assert num(0, 300) == 0

# upper boundary
def test_num_upper_boundary():
    assert num(300, 300) == 300

# invalid inputs return None
def test_num_invalid_inputs():
    for value in (-1, 301, 10.5, "10", True):
        assert num(value, 300) is None

# basketball drill with valid minutes and planned shots
def test_clean_drills_valid_plan():
    raw = [{"title": "  Form Shooting  ", "category": "  Shooting  ", "minutes": 15, "shots": 50}]
    expected = [{"title": "Form Shooting", "category": "Shooting", "kind": "basketball", "minutes": 15, "shots": 50}]
    assert clean_drills(raw, logging=False) == expected

# a valid completed drill with 35 makes and 50 attempts
def test_clean_drills_valid_logged_session():
    raw = [{"title": "Form Shooting", "category": "Shooting", "minutes": 15, "shots_made": 35, "shots_attempted": 50}]
    expected = [{"title": "Form Shooting", "category": "Shooting", "kind": "basketball", "minutes": 15, "shots_made": 35, "shots_attempted": 50}]
    assert clean_drills(raw, logging=True) == expected

# impossible shooting stats is None (shots_made > shots_attempted)
def test_clean_drills_rejects_more_makes_than_attempts():
    raw = [{"title": "Form Shooting", "category": "Shooting", "minutes": 15, "shots_made": 60, "shots_attempted": 50}]
    assert clean_drills(raw, logging=True) is None

# invalid drill "title" return None
def test_clean_drills_list_size_boundaries():
    drill = {"title": "Drill", "category": "Shooting", "minutes": 10, "shots": 20}
    assert clean_drills([], logging=False) is None
    assert clean_drills([drill] * 20, logging=False) == [
        {"title": "Drill", "category": "Shooting", "kind": "basketball", "minutes": 10, "shots": 20}
    ] * 20
    assert clean_drills([drill] * 21, logging=False) is None

# missing title, invalid minutes, or invalid "kind" return None
def test_clean_drills_rejects_invalid_fields():
    valid = {"title": "Drill", "category": "Shooting", "minutes": 10, "shots": 20}
    for changes in ({"title": "  "}, {"minutes": -1}, {"kind": "unknown"}):
        invalid = {**valid, **changes}
        assert clean_drills([invalid], logging=False) is None

# valid API exercise
def test_clean_exercises_formats_valid_exercise():
    raw = [{"name": "Squat", "muscle": "quadriceps", "difficulty": "beginner", "instructions": "Keep your chest up.", "equipments": ["barbell"], "safety_info": "Use proper form."}]
    expected = [{
        "name": "Squat", "muscle": "quadriceps", "difficulty": "beginner",
        "instructions": "Keep your chest up.", "equipment": ["barbell"],
        "safety_info": "Use proper form.",
        "workout_drill": {"title": "Squat", "category": "Strength", "kind": "strength", "minutes": 10, "shots": 0, "shots_made": 0, "shots_attempted": 0},
    }]
    assert clean_exercises(raw) == expected

# exercise dictionary missing optional information should return default values
def test_clean_exercises_missing_fields_defaults():
    expected = [{
        "name": "Exercise", "muscle": "", "difficulty": "",
        "instructions": "No instructions provided.", "equipment": [],
        "safety_info": "",
        "workout_drill": {"title": "Exercise", "category": "Strength", "kind": "strength", "minutes": 10, "shots": 0, "shots_made": 0, "shots_attempted": 0},
    }]
    # no optional info added
    assert clean_exercises([{}]) == expected
    # equipments supposed to be a list, not a string
    assert clean_exercises([{"equipments": "barbell"}]) == expected

# make sure the function returns no more than the first five exercises from the API
def test_clean_exercises_limits_to_first_five_entries():
    raw = [{"name": f"Exercise {i}"} for i in range(7)]
    result = clean_exercises(raw)
    assert [exercise["name"] for exercise in result] == [f"Exercise {i}" for i in range(5)]