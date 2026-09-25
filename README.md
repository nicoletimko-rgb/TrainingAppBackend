# Summer Training App Backend

A Flask API for Nicole Timko's basketball training website. It generates basketball workouts and uses the API Ninjas Exercises API to find strength exercises. The API key stays on the backend.

## Endpoints

### `GET /api/health`

Checks whether the service is running.

Returns:

```json
{"status": "ok"}
```

### `POST /api/exercises`

Accepts JSON with:

- `focus`: `legs`, `core`, or `upper`
- `level`: `beginner`, `intermediate`, or `advanced`

Example request:

```json
{"focus": "legs", "level": "intermediate"}
```

The backend validates the selections, requests matching exercises from API Ninjas, and returns JSON containing the selected `focus` and `level`, the data source, and up to five exercises. Each exercise can include its name, muscle, difficulty, equipment, instructions, and form or safety information. Invalid input returns a JSON error with HTTP status `400`.

**This is the endpoint used by the live frontend's Strength section.**

## Run locally

1. Create and activate a Python virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file **in the backend folder**:

   ```text
   API_NINJAS_KEY=your_api_ninjas_key_here
   FRONTEND_ORIGINS=http://localhost:5500,http://127.0.0.1:5500
   PORT=5001
   ```

4. Start the server:

   ```bash
   python app.py
   ```

5. Visit `http://localhost:5001/api/health`. A working server returns `{"status":"ok"}`.

To test the Strength endpoint:

```bash
curl -X POST http://localhost:5001/api/exercises \
  -H "Content-Type: application/json" \
  -d '{"focus":"legs","level":"intermediate"}'
```

## How the frontend uses the backend

The frontend is hosted on GitHub Pages at https://nicoletimko-rgb.github.io/TrainingAppFrontend/. When a visitor opens **Strength**, selects a muscle focus and difficulty, and clicks **Find exercises**, `app.js` sends a JSON request to `POST /api/exercises` on the Render service. It displays the returned exercises as cards or shows an error message if the request fails.

The frontend's `API_BASE` setting contains the **public Render URL**, not an API key. Basketball drill browsing and video playback do not require a backend request.

## Secrets and deployment

`API_NINJAS_KEY` is read from an environment variable by the Flask backend and sent to API Ninjas in a server-side request. It must not be placed in `app.js`, committed to GitHub, or exposed to the frontend.

Add `.env` to the backend repo's `.gitignore`. For the deployed service, set `API_NINJAS_KEY` in Render's environment settings. Set `FRONTEND_ORIGINS` to the frontend's origin, `https://nicoletimko-rgb.github.io`, to allow requests from GitHub Pages. Local origins can also be included as comma-separated values when needed.

## AI use

See `prompt_log.md` for the development prompts.
