# Courtside backend

Flask API for the Courtside basketball training page. It has two features:

- `POST /api/workouts`: accepts `goal`, `minutes`, `level`, `space`, and `equipment`, validates them, and returns a timed basketball drill plan from a local drill library.
- `POST /api/exercises`: accepts `focus` (`legs`, `core`, `upper`) and `level` (`beginner`, `intermediate`, `advanced`), then calls the API Ninjas Exercises API with the server-side key. Returns up to five exercises with instructions, equipment, and safety information. The API calls the provider's `quadriceps`, `abdominals`, or `chest` muscle filter; `advanced` maps to provider difficulty `expert`.
- `GET /api/health`: returns `{"status":"ok"}` for a quick deployment check.

The browser uses `fetch()` to POST JSON to these endpoints and displays either the structured result or an error. Invalid input returns HTTP 400 with `{ "error": "..." }`. A missing key or external API failure returns a user-friendly error.

## Run locally

1. Install Python 3.10+ and from this folder run:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

   Windows activation: `.venv\Scripts\activate`.

2. Sign up at [API Ninjas](https://api-ninjas.com/api/exercises) and obtain your Exercises API key. Copy `.env.example` to `.env`, put your key after `API_NINJAS_KEY=`, and set `FRONTEND_ORIGINS` for your frontend. **Never commit `.env`.** The `.gitignore` excludes it. `python-dotenv` loads `.env` locally.
3. Start the server with `python app.py`. It runs at `http://localhost:5000`.

Example test (use the backend URL instead of localhost after deployment):

```bash
curl -X POST http://localhost:5000/api/exercises \
  -H 'Content-Type: application/json' \
  -d '{"focus":"legs","level":"beginner"}'
```

The key goes from `.env` or Render's Environment into Python's `os.getenv("API_NINJAS_KEY")`, then in the **server-side** `X-Api-Key` header to API Ninjas. The key never appears in the frontend, repository, or API JSON response. Only nonsecret exercise information is returned. API Ninjas can return an empty list for some combinations; the frontend explains that case.

## Deploy to Render

1. Push the contents of this folder to a **new public GitHub repo**. Verify `.env` is absent from GitHub.
2. Render dashboard → **New → Web Service** → connect the backend repo → select **Python 3** and **Free**.
3. **Build Command:** `pip install -r requirements.txt`.
4. **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT`.
5. Render service → **Environment** → **Add Environment Variable**:

   | Key | Value |
   | --- | --- |
   | `API_NINJAS_KEY` | Your actual API Ninjas key |
   | `FRONTEND_ORIGINS` | `https://nicoletimko-rgb.github.io` (optionally add `,http://localhost:5500` for local tests) |

6. Choose **Save, rebuild, and deploy**. After deployment, open `https://YOUR-SERVICE.onrender.com/api/health` to check it starts. Then test `POST /api/exercises` using the `curl` command above with your service URL. A browser address bar only makes a GET request, so it cannot test this POST endpoint.

GitHub Pages project URLs include a path, but a CORS *origin* contains only the protocol and domain. For a different domain, update `FRONTEND_ORIGINS` accordingly.

## Setup, errors, and secrets

- Never copy the key into HTML, JavaScript, `.env.example`, README, screenshots, or the prompt log.
- If `/api/health` works but exercise search returns 503, check that `API_NINJAS_KEY` is set on Render. A 502 means the provider request failed; check the server logs and whether your API key is valid.
- For a GitHub Pages frontend, update `API_BASE` in `frontend/app.js` to the Render service URL. See the frontend README.
- Free Render instances can sleep when idle; the first request after inactivity can take longer.

## AI use

See `prompt_log.md` for the development prompts.
