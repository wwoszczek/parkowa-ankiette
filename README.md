# Parkowa - Weekly Football Games

Streamlit app for organizing weekly pickup football: signups, a squad builder
with a reserve bench, FUT-style player cards, and game history. Polish UI,
Supabase PostgreSQL, free-tier friendly.

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
  (one bench per game, not per team), in signup order. Until squads are
  saved, only signups beyond the biggest game (18) count as reserves, so the
  list never says "full" while a bigger format still needs players - marked on the signup
  list and shown under the squads
- When a squad player signs out, the first reserve automatically takes the
  freed place (shown as "z ławki · za …") until the owner edits the squads
- Stats count reserves who stayed on the bench as signups, not games played

### Player cards
- Every Google account gets a card in the style of FIFA 14-17 Ultimate Team:
  **bronze, silver, gold**, plus **W formie**, **TOTY** and **Legenda**. The
  designs are our own (CSS + inline SVG), not game artwork
- Rating (OVR) and six stats come **only from played games** since signups
  moved to Google accounts - nobody, not even an admin, sets them. The bench
  does not count. They measure commitment, not skill, so they never affect
  squads:
  - **TEM** signup speed after opening, **STR** attendance in the last 10
    games, **POD** guests brought, **DRY** longest run of games in a row,
    **OBR** tenure, **FIZ** games played
  - **OVR** is the player's rank in overall commitment (games, recent form,
    the current run, tenure, best run, speed, guests) mapped onto FUT bands:
    the least committed 35% bronze (50-64), the next 35% silver (65-74), the
    rest gold (75-95). New players start bronze: silver needs 3 played games,
    gold 8, however short the history. Long runs are rewarded twice (current
    run and best run)
  - **Legenda**: rating 90+ and at least 4 games in a row up to the last one;
    **TOTY**: the 3 golds with most games in the last 52 weeks; **W formie**:
    silver/gold on a run of 3+ whom the model gives 75%+ to play next week
- **Forma**: a small logistic regression (numpy) trained on the group's
  attendance history predicts each player's chance of playing the next game.
  The admin panel shows its time-split check against a simple baseline
- **Twoja karta** on `/cards`: the signed-in account's card, where the player
  sets a **position** (BR/OBR/POM/NAP - decoration only, never moves anyone)
  and uploads a **photo** (JPG/PNG/WebP up to 5 MB, re-encoded server-side to
  a small square WebP). Admins can set photos and positions for any account
  and see the full distribution with the model check
- Saved squads show on a **pitch** with mini cards (1-2-2-1 for 6, 1-2-3-1
  for 7, lineup order - the first player in goal); "Zwiń do listy" folds them
  back into the plain team lists
- Thresholds live in the `cards:` section of `game_consts.yaml`;
  `python card_report.py` prints the distribution from the real
  database (read-only) to tune them

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
| `/teams` | squad builder + saved squads (on the pitch or as lists) and bench |
| `/cards` | player cards, "Twoja karta" (position + photo) |
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

Player cards keep positions and photos in their own table (the cards work
without it - placeholders, no positions - until it exists):

```sql
CREATE TABLE IF NOT EXISTS player_cards (
    user_email        TEXT PRIMARY KEY,  -- lowercased Google e-mail
    position          TEXT CHECK (position IN ('BR', 'OBR', 'POM', 'NAP')),
    photo             BYTEA CHECK (photo IS NULL OR octet_length(photo) <= 200000),
    photo_updated_at  TIMESTAMPTZ,
    photo_uploaded_by TEXT,
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- The app connects as the table owner, which RLS does not affect; with no
-- policies, Supabase's public REST API cannot read or write the photos.
ALTER TABLE player_cards ENABLE ROW LEVEL SECURITY;
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

# Optional: "Pokaż moją kartę" on /cards - a plain login (no signup or
# signout) that brings the player back to the cards. Same values again.
[auth.card]
client_id = "....apps.googleusercontent.com"
client_secret = "..."
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
client_kwargs = { prompt = "select_account" }
```

Without `[auth.card]` a player still sees their card once they have signed
up or out with Google in that browser (the login cookie lasts 30 days).

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
