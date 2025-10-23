# 🏆 Parkowa - Weekly Football Games

Application for organizing weekly football games with automatic signup management, team composition drawing, and game history.

## ⚡ Features

### 👥 Signup System
- Players sign up by providing **nickname** and **password**
- Passwords are securely hashed (bcrypt)
- Visible signup order
- Ability to unregister only with correct password

### 🎲 Team Drawing
- Automatic team division:
  - **12 or 14 people** → 2 teams (red, black)
  - **18 people** → 3 teams (white, red, black)
  - Other numbers → message about need for manual drawing
- Ability to redraw teams

### 💰 Payments (for treasurer)
- **Password protected**
- **Quick debtor overview** - summary of who owes how much
- **Payment management** - marking who paid for historical games

### 📚 Game History
- Full history of all games
- List of registered participants
- Team compositions after drawing

### 🗓️ Automatic Game Management
- **GitHub Actions Scheduler** ensures that the game list and their activity status are up to date

## 🚀 Installation and Setup

### Requirements
- Python 3.8+
- PostgreSQL database

📋 **Quick setup:**
1. Add secret in GitHub repo: `SUPABASE_DATABASE_URL`
2. Workflow is ready in `.github/workflows/scheduler.yml`
3. **Done!** - scheduler works automatically

### 1. Clone repository
```bash
git clone https://github.com/wwoszczek/parkowa-ankiette.git
cd parkowa-ankiette
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Database configuration


### 4. Run application
```bash
streamlit run app.py
```


## 📊 Database Structure

### Table `games`
- `id` (UUID) - Unique game identifier
- `start_time` (timestamp) - Start date and time
- `active` (boolean) - Whether the game is active

### Table `signups`
- `id` (UUID) - Unique signup identifier
- `game_id` (UUID) - Reference to game
- `nickname` (text) - Player nickname
- `password_hash` (text) - Hashed password
- `timestamp` (timestamp) - Signup time

### Table `teams`
- `id` (UUID) - Unique team identifier
- `game_id` (UUID) - Reference to game
- `team_color` (text) - Team color
- `players` (text[]) - List of players in team

### ⏰ Time Parameters
All time settings can be easily changed in the `game_consts.yaml` file:

```yaml
# Games take place on Wednesdays at 18:30
game:
  day: 2      # 2 = Wednesday
  hour: 18
  minute: 30

# Signups open on Mondays at 10:00
signup:
  day: 0      # 0 = Monday
  hour: 10
  minute: 0

# Drawing possible on Wednesdays from 15:00
draw:
  day: 2      # 2 = Wednesday
  hour: 15
  minute: 0
```

**Day mapping:** 0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 4=Friday, 5=Saturday, 6=Sunday

### 🎨 Team Composition Configuration
In the same file, you can add new configurations for different numbers of players:

```yaml
teams:
  12:
    count: 2
    colors: ["czerwona", "czarna"]
    players_per_team: [6, 6]
  16:  # New configuration
    count: 2
    colors: ["czerwona", "czarna"]
    players_per_team: [8, 8]
```

### Game Schedule
- **Game day**: Wednesday 18:30
- **Signups open**: Sunday 10:00
- **Drawing**: Wednesday from 8:00

## 🤝 Contact

Direct all questions and suggestions to GitHub Issues.
