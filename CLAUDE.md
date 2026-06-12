# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Streamlit web app (Polish-language UI) for organizing weekly pickup football games: player signups (Google login via `st.login`), random team drawing and game history. Backed by Supabase PostgreSQL. There are no tests and no linter configured.

## Commands

Plain pip + `requirements.txt` (this is what Streamlit Community Cloud installs from):

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py                       # run the app locally
python github_scheduler.py                 # run scheduler (needs SUPABASE_DATABASE_URL)
```

`requirements.txt` is hand-maintained with the **direct** dependencies only. `src` is imported directly (the app runs via `streamlit run app.py`, not as an installed package). The GitHub Actions scheduler installs just its subset (`psycopg2-binary PyYAML pytz`, no Streamlit).

Database connection requires either `SUPABASE_DATABASE_URL` in `.env` (checked first) or `st.secrets["supabase"]["database_url"]`. The schema lives only in the production Supabase project (no SQL files in the repo — `signups` has `user_email`, `is_guest`, `added_by_email`, legacy nullable `password_hash`, plus a partial unique index on `(game_id, user_email) WHERE is_guest = FALSE`); schema changes are applied manually in the Supabase SQL editor. For local runs against a non-SSL Postgres set `DB_SSLMODE=disable`.

## Architecture

Two independent entry points share one config file, `game_consts.yaml`:

1. **Streamlit UI** (`app.py` + `src/`) — user-facing app.
2. **`github_scheduler.py`** — standalone script run by GitHub Actions (`.github/workflows/scheduler.yml`, cron at 9/14/19 UTC). It deliberately does **not** import from `src/` so it can run without Streamlit installed; it duplicates the YAML loading and time logic. If you change scheduling logic or `game_consts.yaml` structure, update both sides.

### Game lifecycle

The scheduler drives a state machine on the `games.active` flag: games are created **inactive** for the upcoming game day → **activated** when the signup window opens → **deactivated** once the game time passes. The UI shows active games for signups/drawing; inactive *past* games are the history page (`get_past_games` filters `start_time < now` to exclude future pre-created games). All schedule parameters (game day/time, signup opening, draw window, guest limit, team configurations per player count) live in `game_consts.yaml`.

### Identity & permissions

No passwords. `src/utils/auth.py` wraps Streamlit native OIDC (`st.login`/`st.user`) with providers read from `[auth.<provider>]` secret sections — login buttons appear only for configured providers. Google is deliberately the only provider (Facebook needs business verification for public login; GitHub/Discord aren't OIDC; Apple is paid) — don't add others without checking those constraints. A `[dev_user]` secrets section fakes a logged-in user for local development. Admins are e-mails listed in the root-level `admin_emails` secret; they can remove any signup and (re)draw teams outside the time window. **Guests**: signed-in users add named entries (`is_guest=TRUE`, `added_by_email`); removal is allowed for the adder and admins only. Legacy password-era rows have `user_email IS NULL` and can only be removed by admins. Google OAuth setup (consent screen, redirect URIs, secrets layout) is documented in README.md.

**The Google session is deliberately invisible** — the signup panel shows only two always-visible buttons ("Zapisz się kontem Google" / "Wypisz się kontem Google", keys `gbtn_*`); there is no "Zalogowano jako" strip and no logout outside the admin expander. **Every real click goes through the Google account chooser** (`prompt = "select_account"` in `client_kwargs`), so players pick which account performs the action — switching accounts needs no logout. Intent is carried across the OAuth redirect by the **provider name**: two secret sections point at the same Google client — `[auth.google]` (signup) and `[auth.wypis]` (signout) — and Streamlit stores the provider in the identity cookie, so `st.user.provider` tells which button started the flow. `claim_fresh_login()` (src/utils/auth.py) returns the action exactly once, only for a seconds-old login (`iat` claim < 45 s) and dedupes via a server-side `st.cache_resource` set — a days-old cookie or page reload never replays an action. Session state does NOT survive the OAuth redirect; never rely on it across `st.login`. Only the `dev_user` fake acts directly without the chooser. Feedback messages name the account ("Jesteś już zapisany… (konto: e-mail)", "Nie jesteś zapisany… (konto: e-mail)"). No nickname input; the display name comes from the account (`_base_nickname`: full name → e-mail local part → "Gracz"), deduplicated with a numeric suffix (`Wojtek 2`).

### Page navigation

`app.py` uses `st.navigation`/`st.Page` with top-position nav; pages are plain zero-arg functions in `src/pages/` (signup, teams, history) with own URL paths (`/zapisy`, `/sklady`, `/historia`). Each page fetches the cached DB handle itself via `init_database()`.

### UI layer

`src/ui/styles.py` injects the global stylesheet (Manrope font, `pk-*` component classes); `src/ui/components.py` renders presentational HTML (hero card, players table, team cards, stat chips, empty states) — always `html.escape` user content there. Buttons are styled per-widget via `st-key-<key>` CSS classes (e.g. keys starting with `remove` get the destructive red style, `login_google` gets the branded Google style). Avoid emoji; use `:material/...:` icons.

### Database layer

`src/database.py` defines `SupabaseDB`: raw psycopg2 with a new connection opened and closed per query (no pooling — Supabase free-tier friendly). `execute_query` returns a list of dicts for SELECTs and a rowcount otherwise. Tables: `games`, `signups`, `teams`. The `teams.players` column is a TEXT JSON string; `src/utils/teams_db.py:get_teams_for_game` normalizes legacy formats when reading. The production database has DB-side triggers installed historically (nickname validation, 50-signup cap), so some validation lives in the database, not just in `src/utils/validation.py`.

### Conventions

- All datetime logic uses `Europe/Warsaw` (`src/constants.py:TIMEZONE`); weekday numbering follows Python `weekday()` (0=Monday). The GitHub Actions cron is in UTC — keep the offset in mind when editing it.
- UI strings are Polish (note `day_names` vs `day_names_accusative` in `game_consts.yaml` for "w środę"-style phrases); code, comments and docstrings are English.
- Game lists are cached with `st.cache_data` (60s/300s TTL); signups are always fetched fresh. After mutations pages set a `flash` session-state message and `st.rerun()`.
