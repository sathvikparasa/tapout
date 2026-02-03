# Backend Cleanup: Supabase Migration
## Constraints               
1. Do NOT delete files without confirmation
2. Do NOT run git commands without confirmation
## Scope
Files in `backend/` only.

## Task 1: Remove Docker/Alembic remnants
  The backend has migrated from Docker/Alembic to Supabase. Remove or update references to the old setup:
  - Remove Alembic migration files/config if present
  - Remove Docker-related files (Dockerfile, docker-compose.yml) if present
  - Update any SQLAlchemy config that still references local DB setup instead of Supabase     
  - Remove unused dependencies from requirements.txt

## Task 2: Project structure cleanup
  Ensure `backend/` follows a standard FastAPI layout:
  - `app/` contains routers, models, services, schemas
  - No dead code or unused imports
  - Config/secrets read from environment variables                 
  Refer to `docs/` and `prompts/` for Supabase connection details.