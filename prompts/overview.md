# WarnABrotha - Agent Operational Rules

Read and follow these rules for every task in this project.

## Git & Version Control

- **Do not commit code.** I will inspect all changes before committing.
- **Do not push code to GitHub.** I will handle pull requests, merges, and remote operations manually.
- **Do not run destructive git commands** (`reset --hard`, `checkout .`, `clean -f`, `branch -D`) without explicit confirmation.

## File Integrity

- **Do not delete files** without asking first. If something looks unused, flag it — don't remove it.
- **Do not modify Gradle project files** (e.g., `settings.gradle.kts`, root `build.gradle.kts`) unless the task explicitly requires it. These are tricky to get right; ask if unsure.
- **Do not modify `app.yaml`** without confirmation — it controls production deployment.
- **Preserve existing features.** When adding new code, do not remove or refactor unrelated existing functionality.

## Android-Specific

- **Use Jetpack Compose for all UI.** Do not generate XML layouts. The app is 100% Compose with Material 3.
- **Follow the existing MVVM pattern.** State lives in `AppViewModel` via `MutableStateFlow<AppUiState>`. Do not introduce `LiveData`, new ViewModel classes, or alternative state patterns without discussing it first.
- **Use Hilt for dependency injection.** All injectable classes use `@Inject constructor`. Modules live in `di/AppModule.kt`.
- **Use Retrofit for API calls.** All endpoints are defined in `data/api/ApiService.kt` as suspend functions returning `Response<T>`.

## Backend-Specific

- **Follow the existing FastAPI async pattern.** All route handlers and services use `async/await` with SQLAlchemy async sessions.
- **Do not modify database schema** (add columns, tables) without confirming the migration approach. We use Supabase — schema changes require coordination.
- **Keep Pydantic schemas in sync.** If you change a model in `models/`, update the corresponding schema in `schemas/` and vice versa.

## Communication

- **Ask questions if something is unclear.** If instructions are ambiguous, ask rather than guess.
- **Flag risks before acting.** If an approach could break existing functionality, say so before implementing.
- **Show your work incrementally.** For multi-file changes, explain what you're changing and why before writing code.
