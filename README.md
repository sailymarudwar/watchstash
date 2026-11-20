# WatchStash

Paste a reel's caption and WatchStash pulls out every movie and TV title,
then shows each one with its genres, IMDb rating, and where to stream it in
your region. Every person gets their own stash, with a watched mark on each title.

## How it works

1. Claude reads the pasted text and returns a clean list of titles.
2. TMDB provides genres and streaming availability. OMDb provides IMDb ratings.
3. Results are saved per person in a database, so the stash survives refreshes.

## Project layout

```
app/
  main.py            app setup and startup checks
  config.py          all settings, read from environment variables
  auth.py            access-code login
  models.py          database tables
  database.py        database connection
  schemas.py         request and response shapes
  routes/            web endpoints only
  services/          Claude extraction, TMDB and OMDb lookups
  repositories/      all database access
static/index.html    the web page
tests/               automated tests
```

Routes call services and repositories. Services never touch the database,
and repositories never touch the web layer.

## Run it locally

1. Install dependencies: `py -m pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and fill in your keys and access codes.
3. Start the app: `py -m uvicorn app.main:app --reload`
4. Open http://127.0.0.1:8000 and enter your access code.

## Run the tests

```
py -m pip install -r requirements-dev.txt
py -m pytest
```

The tests use fakes instead of the real APIs, so they cost nothing.

## Settings

| Variable | Purpose |
|---|---|
| ANTHROPIC_API_KEY | Claude API key (reads the captions) |
| TMDB_API_KEY | Genres and streaming availability |
| OMDB_API_KEY | IMDb ratings |
| ACCESS_CODES | `name:code` pairs, comma separated |
| REGION | Country code for streaming results (default US) |
| DATABASE_URL | Database location (default: local SQLite file) |

## Notes

- Only the "Find titles" button calls Claude, which is the only paid step.
- Never commit `.env`. It is listed in `.gitignore`.