# Parkowa - Weekly Football Games

Streamlit app for organizing weekly pickup football: signups, a squad builder
with a reserve bench, and game history. Polish UI, Supabase PostgreSQL,
free-tier friendly.

## Features

### Signups
- Login with **Google** (Streamlit native `st.login`, no passwords)
- One-click signup under an editable display name
- **Guests**: a signed-in user can add friends without an account
  (configurable limit per user); only the adder or an admin can remove them
- Self sign-out at any time; admins can remove any entry

### Squad builder
- Squads are set **by hand**: pick a team, tap players to put them in it
  (tap a player in a team to take them out). Placing someone by hand is also
  how shirt constraints work (a player who only owns one colour)
- **Losuj resztę** randomly fills the open places around the hand-picked
  core, balancing team sizes; clicked again (**Przelosuj**) it re-rolls only
  the random part. Nothing is saved until the setter clicks **Zatwierdź składy**
- **First come, first served**: the account that approves a game's squads
  owns them. Everyone sees them; only the owner (or an admin) can edit or
  delete them, and once deleted anyone can set new ones
- Formats come from `game_consts.yaml`: **2 teams** (czerwona, czarna,
  12–14 players) or **3 teams** (biała, czerwona, czarna, needs 18). The
  builder picks the most teams there are enough players for: 15–17 signups
  means 2 teams of 7 and the rest on the bench
- Can be set any time once signups are open, as soon as at least 12 players
  (the smallest lineup) are on the list - admins can set them with fewer;
  saved squads can always be edited

### Reserve bench
- Signups beyond the chosen format's limit wait on the **ławka rezerwowych**
  (one bench per game, not per team), in signup order - marked on the signup
  list and shown under the squads
- When a squad player signs out, the first reserve automatically takes the
  freed place (shown as "z ławki · za …") until the owner edits the squads
- Stats count reserves who stayed on the bench as signups, not games played

### History
- Archive of past games: pick a game, see players, squads and the bench
- Stat chips show player count and number of teams

### Automatic game management
- **GitHub Actions scheduler** (`.github/workflows/scheduler.yml`) creates the
  next game, opens signups and closes past games - no server needed
  (installs only `psycopg2-binary PyYAML pytz`, then runs `github_scheduler.py`)

## Pages

| URL | Page |
|---|---|
| `/` | signup form + live player list |
| `/teams` | squad builder + saved squads and bench |
| `/history` | past games archive |
| `/stats` | most active players by season — podium + full ranking |

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

Squad ownership needs one column on `teams` (run once in the SQL editor):

```sql
ALTER TABLE teams ADD COLUMN IF NOT EXISTS created_by_email TEXT;
```

### 3. Login (Google)

Create an OAuth client in Google Cloud Console (Web application, redirect
URI `https://<app>.streamlit.app/oauth2callback` and
`http://localhost:8501/oauth2callback`), then fill the secrets:

```toml
admin_emails = ["..."]            # admins: remove anyone, manage any squads any time

[auth]
redirect_uri = "https://<app>.streamlit.app/oauth2callback"
cookie_secret = "<random hex>"

# "google" handles signups, "signout" handles signouts - the SAME Google
# client in both. The provider name stored in the identity cookie carries
# the intended action across the OAuth redirect; prompt = "select_account"
# forces the account chooser on every click (players pick which account
# performs the action).
[auth.google]
client_id = "....apps.googleusercontent.com"
client_secret = "..."
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
client_kwargs = { prompt = "select_account" }

[auth.signout]
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

## Schedule configuration

All times live in `game_consts.yaml` (Python weekday: 0=Monday):

```yaml
game:                                     # Wednesday 18:30
  day: 2
  hour: 18
  minute: 30
  time_changes:                           # optional: new start time from a date on
    - { from: 2026-11-01, hour: 19, minute: 30 }
signup: { day: 6, hour: 10, minute: 0 }   # opens Sunday 10:00
guests: { max_per_user: 5 }
```

Times are Warsaw wall-clock times; summer/winter time is handled in code.
A `time_changes` entry only affects games created after it applies - games
already in the database keep their stored start time.
