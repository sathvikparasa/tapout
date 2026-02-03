# Backend Organization Issues

## Medium Priority

1. **Empty `app/ml/` directory** — Exists with no files, no `__init__.py`. Serves no purpose currently.

2. **Unused ML dependencies in `requirements.txt`** — `scikit-learn`, `numpy`, and `pandas` are listed but never imported anywhere in the codebase.

3. **Unused `database_url_sync` config field** (`app/config.py:23`) — Defined in Settings but never referenced anywhere in the code. The app only uses async database operations.

4. **Unused import in `app/api/feed.py:14`** — `selectinload` is imported from `sqlalchemy.orm` but never used.

## Low Priority

5. **CORS `allow_origins=["*"]`** (`app/main.py`) — Wide open. There's a comment acknowledging it should be restricted for production, but it's still worth noting.

6. **Directory naming: `api/` vs `routers/`** — FastAPI docs conventionally use `routers/`. Not wrong, just non-standard.
