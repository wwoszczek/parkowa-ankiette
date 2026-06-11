# Parkowa - Weekly Football Games

Streamlit app for organizing weekly pickup football: signups, random team
drawing and game history. Polish UI, Supabase PostgreSQL, free-tier friendly.

## Features

### Signups
- Login with **Google or Facebook** (Streamlit native `st.login`, no passwords)
- One-click signup under an editable display name
- **Guests**: a signed-in user can add friends without an account
  (configurable limit per user); only the adder or an admin can remove them
- Self sign-out at any time; admins can remove any entry

### Team drawing
- Automatic split based on player count (configured in `game_consts.yaml`):
  - **12 / 14 players** → 2 teams (czerwona, czarna)
  - **18 players** → 3 teams (biała, czerwona, czarna)
- Drawing opens at a configured time window; admins can (re)draw any time
- Other counts → manual draw message

### History
- Archive of past games: pick a game, see players and drawn teams instantly

### Automatic game management
- **GitHub Actions scheduler** (`.github/workflows/scheduler.yml`) creates the
  next game, opens signups and closes past games - no server needed
  (`uv run --only-group scheduler python github_scheduler.py`)

## Pages

| URL | Page |
|---|---|
| `/zapisy` | signup form + live player list |
| `/sklady` | drawn teams + draw controls |
| `/historia` | past games archive |

## Setup

### 1. Install & run

The project is managed with [uv](https://docs.astral.sh/uv/):

```bash
uv run streamlit run app.py     # syncs deps from uv.lock, then runs
```

`requirements.txt` is generated from the lockfile (`uv export`) and kept only
for Streamlit Community Cloud, which installs from it. After changing
dependencies in `pyproject.toml`, refresh both:

```bash
uv lock
uv export --no-hashes --no-emit-project --no-default-groups -o requirements.txt
```

### 2. Database (Supabase)

See `SUPABASE_SETUP_GUIDE.md`. Fresh database: run `database_setup.sql`,
then `migrations/001_social_auth.sql`. Existing database: run only the
migration.

Connection string goes to `.env` (`SUPABASE_DATABASE_URL=...`) or
`.streamlit/secrets.toml` (`[supabase] database_url`).

### 3. Login (Google / Facebook)

See `AUTH_SETUP_GUIDE.md` - OAuth clients, secrets layout, admin list and
the local `dev_user` mode.

### 4. Scheduler

Add the `SUPABASE_DATABASE_URL` secret in the GitHub repo - the workflow in
`.github/workflows/scheduler.yml` does the rest.

## Database structure

- `games` - `id`, `start_time`, `active`
- `signups` - `id`, `game_id`, `nickname`, `user_email`, `is_guest`,
  `added_by_email`, `timestamp` (`password_hash` kept for legacy rows)
- `teams` - `id`, `game_id`, `team_color`, `players` (JSON)

## Schedule configuration

All times live in `game_consts.yaml` (Python weekday: 0=Monday):

```yaml
game:   { day: 2, hour: 18, minute: 30 }  # Wednesday 18:30
signup: { day: 6, hour: 10, minute: 0 }   # opens Sunday 10:00
draw:   { day: 2, hour: 8,  minute: 0 }   # draw from Wednesday 8:00
guests: { max_per_user: 2 }
```
