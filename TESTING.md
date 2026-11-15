All these are adjusted in workout_logic.py (3 functions testing extracted) and tested in test_workout_logic.py

1. zero is no longer accepted, even though it should be (test_num_lower_boundary)
return value if type(value) is int and 0 <= value <= high else None
to
return value if type(value) is int and 0 < value <= high else None

    def test_num_lower_boundary():
>       assert num(0, 300) == 0
E       assert None == 0
E        +  where None = num(0, 300)

test_workout_logic.py:11: AssertionError
============================================== short test summary info ===============================================
FAILED test_workout_logic.py::test_num_lower_boundary - assert None == 0

2. reject the maximum - a value equal to the maximum is now rejecyed (test_num_upper_boundary)

return value if type(value) is int and 0 <= value <= high else None
to
return value if type(value) is int and 0 <= value < high else None

====================================================== FAILURES ======================================================
______________________________________________ test_num_upper_boundary _______________________________________________

    def test_num_upper_boundary():
>       assert num(300, 300) == 300
E       assert None == 300
E        +  where None = num(300, 300)

test_workout_logic.py:15: AssertionError
============================================== short test summary info ===============================================
FAILED test_workout_logic.py::test_num_upper_boundary - assert None == 300
============================================ 1 failed, 11 passed in 0.06s ============================================


3. allow impossible shooting stats: the function now rejects ordinary shooting results while allowing impossible results where made shots exceed attempted shots (test_clean_drills_valid_logged_session and test_clean_drills_rejects_more_makes_than_attempts)

if kind != "strength" and made > attempted:
to 
if kind != "strength" and made < attempted:


_______________________________________ test_clean_drills_valid_logged_session _______________________________________

    def test_clean_drills_valid_logged_session():
        raw = [{"title": "Form Shooting", "category": "Shooting", "minutes": 15, "shots_made": 35, "shots_attempted":50}]
        expected = [{"title": "Form Shooting", "category": "Shooting", "kind": "basketball", "minutes": 15, "shots_made": 35, "shots_attempted": 50}]
>       assert clean_drills(raw, logging=True) == expected
E       AssertionError: assert None == [{'category': 'Shooting', 'kind': 'basketball', 'minutes': 15, 'shots_attempted': 50, ...}]
E        +  where None = clean_drills([{'category': 'Shooting', 'minutes': 15, 'shots_attempted': 50, 'shots_made': 35, ...}], logging=True)

test_workout_logic.py:32: AssertionError
_________________________________ test_clean_drills_rejects_more_makes_than_attempts _________________________________

    def test_clean_drills_rejects_more_makes_than_attempts():
        raw = [{"title": "Form Shooting", "category": "Shooting", "minutes": 15, "shots_made": 60, "shots_attempted":50}]
>       assert clean_drills(raw, logging=True) is None
E       AssertionError: assert [{'category': 'Shooting', 'kind': 'basketball', 'minutes': 15, 'shots_attempted': 50, ...}] is None
E        +  where [{'category': 'Shooting', 'kind': 'basketball', 'minutes': 15, 'shots_attempted': 50, ...}] = clean_drills([{'category': 'Shooting', 'minutes': 15, 'shots_attempted': 50, 'shots_made': 60, ...}], logging=True)

test_workout_logic.py:37: AssertionError
============================================== short test summary info ===============================================
FAILED test_workout_logic.py::test_clean_drills_valid_logged_session - AssertionError: assert None == [{'category': 'Shooting', 'kind': 'basketball', 'minutes': 15, 'shots_attempted': ...
FAILED test_workout_logic.py::test_clean_drills_rejects_more_makes_than_attempts - AssertionError: assert [{'category': 'Shooting', 'kind': 'basketball', 'minutes': 15, 'shots_attempted': 50, ...}...
============================================ 2 failed, 10 passed in 0.06s ============================================

4. change the drill limit: a workout with exactly 20 drills is now incorrectly rejected (teat_clean_drills_list_size_boundaries)

if not isinstance(raw, list) or not 1 <= len(raw) <= 20:
to
if not isinstance(raw, list) or not 1 <= len(raw) <= 19:

_______________________________________ test_clean_drills_list_size_boundaries _______________________________________

    def test_clean_drills_list_size_boundaries():
        drill = {"title": "Drill", "category": "Shooting", "minutes": 10, "shots": 20}
        assert clean_drills([], logging=False) is None
>       assert clean_drills([drill] * 20, logging=False) == [
            {"title": "Drill", "category": "Shooting", "kind": "basketball", "minutes": 10, "shots": 20}
        ] * 20
E       AssertionError: assert None == ([{'category': 'Shooting', 'kind': 'basketball', 'minutes': 10, 'shots': 20, ...}] * 20)
E        +  where None = clean_drills(([{'category': 'Shooting', 'minutes': 10, 'shots': 20, 'title': 'Drill'}] * 20), logging=False)

test_workout_logic.py:43: AssertionError
============================================== short test summary info ===============================================
FAILED test_workout_logic.py::test_clean_drills_list_size_boundaries - AssertionError: assert None == ([{'category': 'Shooting', 'kind': 'basketball', 'minutes': 10, 'shots': 20, ...}]...
============================================ 1 failed, 11 passed in 0.03s ============================================

5. return only 4 exercises instead of 5 (test_clean_exercises_limits_to_first_five_entries)

for item in exercises[:5] if isinstance(item, dict)
to 
for item in exercises[:4] if isinstance(item, dict)

_________________________________ test_clean_exercises_limits_to_first_five_entries __________________________________

    def test_clean_exercises_limits_to_first_five_entries():
        raw = [{"name": f"Exercise {i}"} for i in range(7)]
        result = clean_exercises(raw)
>       assert [exercise["name"] for exercise in result] == [f"Exercise {i}" for i in range(5)]
E       AssertionError: assert ['Exercise 0'... 'Exercise 3'] == ['Exercise 0'... 'Exercise 4']
E         
E         Right contains one more item: 'Exercise 4'
E         
E         Full diff:
E           [
E               'Exercise 0',
E               'Exercise 1',...
E         
E         ...Full output truncated (4 lines hidden), use '-vv' to show

test_workout_logic.py:83: AssertionError
============================================== short test summary info ===============================================
FAILED test_workout_logic.py::test_clean_exercises_limits_to_first_five_entries - AssertionError: assert ['Exercise 0'... 'Exercise 3'] == ['Exercise 0'... 'Exercise 4']
============================================ 1 failed, 11 passed in 0.03s ============================================


Step 7: 

https://github.com/nicoletimko-rgb/TrainingAppBackend/actions/runs/43722868260

https://github.com/nicoletimko-rgb/TrainingAppBackend/actions/runs/43723004590


step 8: 

def num(value, high):
    return value if type(value) is int and 0 < value <= high else None


