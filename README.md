# Gemini Web

This repo is split for deployment:

- `backend/` - Flask API for Render
- `frontend/` - static frontend for Vercel

## Backend on Render

1. Create a new Render Web Service from this repo.
2. Set the root directory to `backend`.
3. Use:
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app`
4. Add environment variables:
   - `GEMINI_API_KEY`
   - `SECRET_KEY`
   - `FLASK_DEBUG=False`
   - `CORS_ORIGINS=https://your-vercel-app.vercel.app`

You can also deploy with the root `render.yaml` blueprint. It defines a persistent disk for SQLite chat history and uploaded files, plus `DATABASE_PATH` and `UPLOAD_FOLDER` values that point at that disk.

## Frontend on Vercel

1. Create a new Vercel project from this repo.
2. Set the root directory to `frontend`.
3. Framework preset: `Other`.
4. Build command can be empty, or use `npm run build`.
5. Output directory: `.`.
6. Edit `frontend/config.js` and set `window.GEMINI_API_BASE_URL` to your Render URL.

Example:

```js
window.GEMINI_API_BASE_URL = "https://gemini-backend.onrender.com";
```

## Local Development

Run the backend:

```bash
cd backend
pip install -r requirements.txt
python app.py\n```\n\nThe backend runs at `http://localhost:5001` by default.

Open `frontend/index.html` in a browser. When opened as a local file, it defaults to `http://localhost:5001` for API calls.

