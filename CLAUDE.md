# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Streamlit web app (Polish-language UI) for organizing weekly pickup football games: player signups (Google/Facebook login via `st.login`), random team drawing and game history. Backed by Supabase PostgreSQL. There are no tests and no linter configured.

## Commands

Managed with **uv** (`pyproject.toml` + `uv.lock`):

```bash
uv run streamlit run app.py                                  # run the app locally
uv run --only-group scheduler python github_scheduler.py     # run scheduler (needs SUPABASE_DATABASE_URL)
uv lock                                                       # after editing deps
uv export --no-hashes --no-emit-project --no-default-groups -o requirements.txt
```

`requirements.txt` is a **generated artifact** (exported from `uv.lock`) kept only because Streamlit Community Cloud installs from it — never hand-edit it; change `pyproject.toml` and re-export. The project is non-packaged (`[tool.uv] package = false`); `src` is imported directly. The scheduler needs only the `scheduler` dependency group (no Streamlit).

Database connection requires either `SUPABASE_DATABASE_URL` in `.env` (checked first) or `st.secrets["supabase"]["database_url"]`. Schema setup is manual: `database_setup.sql` + `migrations/*.sql` in the Supabase SQL editor. For local runs against a non-SSL Postgres set `DB_SSLMODE=disable`.

## Architecture

Two independent entry points share one config file, `game_consts.yaml`:

1. **Streamlit UI** (`app.py` + `src/`) — user-facing app.
2. **`github_scheduler.py`** — standalone script run by GitHub Actions (`.github/workflows/scheduler.yml`, cron at 9/14/19 UTC). It deliberately does **not** import from `src/` so it can run without Streamlit installed; it duplicates the YAML loading and time logic. If you change scheduling logic or `game_consts.yaml` structure, update both sides.

### Game lifecycle

The scheduler drives a state machine on the `games.active` flag: games are created **inactive** for the upcoming game day → **activated** when the signup window opens → **deactivated** once the game time passes. The UI shows active games for signups/drawing; inactive *past* games are the history page (`get_past_games` filters `start_time < now` to exclude future pre-created games). All schedule parameters (game day/time, signup opening, draw window, guest limit, team configurations per player count) live in `game_consts.yaml`.

### Identity & permissions

No passwords. `src/utils/auth.py` wraps Streamlit native OIDC (`st.login`/`st.user`) with providers read from `[auth.google]`/`[auth.facebook]` secret sections — login buttons appear only for configured providers. A `[dev_user]` secrets section fakes a logged-in user for local development. Admins are e-mails listed in the root-level `admin_emails` secret; they can remove any signup and (re)draw teams outside the time window. **Guests**: signed-in users add named entries (`is_guest=TRUE`, `added_by_email`); removal is allowed for the adder and admins only. Legacy password-era rows have `user_email IS NULL` and can only be removed by admins. See `AUTH_SETUP_GUIDE.md`.

### Page navigation

`app.py` uses `st.navigation`/`st.Page` with top-position nav; pages are plain zero-arg functions in `src/pages/` (signup, teams, history) with own URL paths (`/zapisy`, `/sklady`, `/historia`). Each page fetches the cached DB handle itself via `init_database()`.

### UI layer

`src/ui/styles.py` injects the global stylesheet (Manrope font, `pk-*` component classes); `src/ui/components.py` renders presentational HTML (hero card, players table, team cards, stat chips, empty states) — always `html.escape` user content there. Buttons are styled per-widget via `st-key-<key>` CSS classes (e.g. keys starting with `remove` get the destructive red style, `login_google`/`login_facebook` get branded styles). Avoid emoji; use `:material/...:` icons.

### Database layer

`src/database.py` defines `SupabaseDB`: raw psycopg2 with a new connection opened and closed per query (no pooling — Supabase free-tier friendly). `execute_query` returns a list of dicts for SELECTs and a rowcount otherwise. Tables: `games`, `signups`, `teams`. The `teams.players` column is a TEXT JSON string; `src/utils/teams_db.py:get_teams_for_game` normalizes legacy formats when reading. `database_setup.sql` installs DB-side triggers (nickname validation, 50-signup cap), so some validation lives in the database, not just in `src/utils/validation.py`.

### Conventions

- All datetime logic uses `Europe/Warsaw` (`src/constants.py:TIMEZONE`); weekday numbering follows Python `weekday()` (0=Monday). The GitHub Actions cron is in UTC — keep the offset in mind when editing it.
- UI strings are Polish (note `day_names` vs `day_names_accusative` in `game_consts.yaml` for "w środę"-style phrases); code, comments and docstrings are English.
- Game lists are cached with `st.cache_data` (60s/300s TTL); signups are always fetched fresh. After mutations pages set a `flash` session-state message and `st.rerun()`.
