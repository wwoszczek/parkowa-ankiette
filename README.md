# Parkowa - Weekly Football Games

Streamlit app for organizing weekly pickup football: signups, random team
drawing and game history. Polish UI, Supabase PostgreSQL, free-tier friendly.

## Features

### Signups
- Login with **Google** (Streamlit native `st.login`, no passwords)
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
  (installs only `psycopg2-binary PyYAML pytz`, then runs `github_scheduler.py`)

## Pages

| URL | Page |
|---|---|
| `/zapisy` | signup form + live player list |
| `/sklady` | drawn teams + draw controls |
| `/historia` | past games archive |
| `/statystyki` | most active players, by season |

## Setup

### 1. Install & run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

`requirements.txt` holds the direct dependencies; Streamlit Community Cloud
installs from it.

### 2. Database (Supabase)

The schema already lives in the production Supabase project. Connection
string goes to `.env` (`SUPABASE_DATABASE_URL=...`) or
`.streamlit/secrets.toml` (`[supabase] database_url`).

### 3. Login (Google)

Create an OAuth client in Google Cloud Console (Web application, redirect
URI `https://<app>.streamlit.app/oauth2callback` and
`http://localhost:8501/oauth2callback`), then fill the secrets:

```toml
admin_emails = ["..."]            # admins: remove anyone, draw any time

[auth]
redirect_uri = "https://<app>.streamlit.app/oauth2callback"
cookie_secret = "<random hex>"

# "google" handles signups, "wypis" handles signouts - the SAME Google
# client in both. The provider name stored in the identity cookie carries
# the intended action across the OAuth redirect; prompt = "select_account"
# forces the account chooser on every click (players pick which account
# performs the action).
[auth.google]
client_id = "....apps.googleusercontent.com"
client_secret = "..."
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
client_kwargs = { prompt = "select_account" }

[auth.wypis]
client_id = "....apps.googleusercontent.com"   # same values as above
client_secret = "..."
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
client_kwargs = { prompt = "select_account" }
```

For local development without OAuth, a `[dev_user]` secrets section
(`enabled`, `email`, `name`) fakes a logged-in user.

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
