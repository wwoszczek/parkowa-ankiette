# 🏆 Parkowa Ankieta - Cotygodniowe Gierki Piłkarskie

Aplikacja Streamlit do organizowania cotygodniowych gierek piłkarskich z automatycznym zarządzaniem zapisami, losowaniem składów i historią gier.

## ⚡ Funkcjonalności

### 🗓️ Automatyczne zarządzanie gierkami
- - `signup.py` - Formularz zapisów i wypisów
- `list_players.py` - Wyświetlanie listy zapisanych graczy
- `draw_teams.py` - Interface losowania składów
- `history.py` - Przeglądanie historii gierek

#### 🛠️ **src/utils/** - Funkcje pomocniczeb Actions Sche- `signup.py` - Formularz zapisów i wypisów
- `list_players.py` - Wyświetlanie listy zapisanych graczy
- `draw_teams.py` - Interface losowania składów
- `history.py` - Przeglądanie historii gierek** - 🤖 **CAŁKOWICIE NIEZALEŻNY** od UI
- Gierki tworzone są **4 tygodnie do przodu** automatycznie **3 razy dziennie**
- **Zero zależności** od odwiedzin użytkowników - działa w chmurze GitHub
- **Odporność na awarie** - system automatycznie nadrabia zaległości
- **Monitoring** - pełne logi w GitHub Actions (8:00, 14:00, 20:00)

### 👥 System zapisów
- Gracze zapisują się podając **nickname** i **hasło**
- Hasła są bezpiecznie hashowane (bcrypt)
- Widoczna kolejność zgłoszeń
- Możliwość wypisania się tylko z prawidłowym hasłem
- Ochrona przed duplikatami nicków w tej samej gierce

### 🎲 Losowanie składów
- Dostępne w środy od 15:00
- Automatyczne dzielenie na drużyny:
  - **12 lub 14 osób** → 2 drużyny (czerwona, czarna)
  - **18 osób** → 3 drużyny (biała, czerwona, czarna)
  - Inna liczba → komunikat o konieczności ręcznego losowania
- Możliwość ponownego losowania

### 📚 Historia gierek
- Pełna historia wszystkich gierek
- Lista zapisanych uczestników
- Składy drużyn po losowaniu

## 🚀 Instalacja i uruchomienie

### Wymagania
- Python 3.8+
- Konto Neon PostgreSQL (darmowe)
- Konto Streamlit Cloud (opcjonalne, do deploymentu)

### ⚡ NAJWAŻNIEJSZE: GitHub Actions Scheduler

**Gierki są tworzone AUTOMATYCZNIE przez GitHub Actions** - całkowicie niezależnie od aplikacji Streamlit!

🤖 **Jak to działa:**
1. **GitHub Actions** uruchamia scheduler **3 razy dziennie** (8:00, 14:00, 20:00)
2. **Nie wymaga** odwiedzin użytkowników ani aktywnej aplikacji  
3. **Streamlit może "spać"** - scheduler działa nadal
4. **Darmowe** - 90 minut/miesiąc vs 2000 limit (1800 minut zapasu!)

📋 **Szybka konfiguracja:**
1. Dodaj sekret w GitHub repo: `NEON_DATABASE_URL`
2. Workflow jest już gotowy w `.github/workflows/scheduler.yml`
3. **Gotowe!** - scheduler pracuje automatycznie

**Rozwiązania (jeśli nie chcesz GitHub Actions):**
1. **Regularne odwiedziny** - ktoś z zespołu sprawdza aplikację raz na tydzień

### 1. Klonowanie repozytorium
```bash
git clone https://github.com/wwoszczek/parkowa-ankiette.git
cd parkowa-ankiette
```

### 2. Instalacja zależności
```bash
pip install -r requirements.txt
```

### 3. Konfiguracja bazy danych Neon PostgreSQL

#### 3.1 Utworzenie projektu w Neon
1. Idź na [neon.tech](https://neon.tech)
2. Zaloguj się przez GitHub
3. Utwórz nowy projekt
4. Skopiuj **Connection String** z dashboard

#### 3.2 Utworzenie tabel
1. Dodaj connection string do `.env`:
   ```env
   NEON_DATABASE_URL=postgresql://username:password@ep-xyz.neon.tech/neondb?sslmode=require
   ```
2. Uruchom setup bazy danych:
   ```bash
   python setup_database.py
   ```

### 4. Konfiguracja sekretów

#### Lokalne uruchomienie
Edytuj plik `.streamlit/secrets.toml`:
```toml
[neon]
database_url = "postgresql://username:password@ep-xyz.neon.tech/neondb?sslmode=require"
```

#### Deploy na Streamlit Cloud
1. W ustawieniach aplikacji na Streamlit Cloud
2. Dodaj sekrety w sekcji **Secrets**:
```toml
[neon]
database_url = "postgresql://username:password@ep-xyz.neon.tech/neondb?sslmode=require"
```

### 5. Uruchomienie aplikacji
```bash
streamlit run app.py
```

## 🌐 Deploy na Streamlit Cloud

1. **Fork** tego repozytorium na swoje konto GitHub
2. Idź na [share.streamlit.io](https://share.streamlit.io)
3. Połącz swoje konto GitHub
4. Wybierz zforkowane repozytorium
5. Ustaw:
   - **Main file path**: `app.py`
   - **Python version**: 3.8+
6. Dodaj connection string Neon w ustawieniach aplikacji
7. Kliknij **Deploy**

## 📊 Struktura bazy danych

### Tabela `games`
- `id` (UUID) - Unikalny identyfikator gierki
- `start_time` (timestamp) - Data i czas rozpoczęcia
- `active` (boolean) - Czy gierka jest aktywna

### Tabela `signups`
- `id` (UUID) - Unikalny identyfikator zapisu
- `game_id` (UUID) - Odniesienie do gierki
- `nickname` (text) - Nickname gracza
- `password_hash` (text) - Zahashowane hasło
- `timestamp` (timestamp) - Czas zapisu

### Tabela `teams`
- `id` (UUID) - Unikalny identyfikator drużyny
- `game_id` (UUID) - Odniesienie do gierki
- `team_color` (text) - Kolor drużyny
- `players` (text[]) - Lista graczy w drużynie

## 🔧 Konfiguracja

### 🤖 Automatyzacja schedulera

#### ⭐ Opcja 1: GitHub Actions (ZALECANA)
```yaml
# Automatycznie skonfigurowane w .github/workflows/scheduler.yml
# Uruchamia się 3 razy dziennie: 8:00, 14:00, 20:00
# ZERO konserwacji, ZERO kosztów, ZERO zależności od UI
```

**Konfiguracja:**
1. W GitHub repo: `Settings > Secrets and variables > Actions`
2. Dodaj: `NEON_DATABASE_URL`  
3. **Gotowe!** - scheduler działa automatycznie 3x dziennie

**Szczegóły:** Zobacz `GITHUB_ACTIONS_SETUP.md`

### ⏰ Parametry czasowe
Wszystkie ustawienia czasowe można łatwo zmienić w pliku `game_consts.yaml`:

```yaml
# Gierki odbywają się w środy o 18:30
game:
  day: 2      # 2 = środa
  hour: 18
  minute: 30

# Zapisy otwierają się w poniedziałki o 10:00
signup:
  day: 0      # 0 = poniedziałek
  hour: 10
  minute: 0

# Losowanie możliwe w środy od 15:00
draw:
  day: 2      # 2 = środa
  hour: 15
  minute: 0
```

**Mapowanie dni:** 0=poniedziałek, 1=wtorek, 2=środa, 3=czwartek, 4=piątek, 5=sobota, 6=niedziela

### 🎨 Konfiguracja składów drużyn
W tym samym pliku można dodać nowe konfiguracje dla różnych liczb graczy:

```yaml
teams:
  12:
    count: 2
    colors: ["czerwona", "czarna"]
    players_per_team: [6, 6]
  16:  # Nowa konfiguracja
    count: 2
    colors: ["czerwona", "czarna"]
    players_per_team: [8, 8]
```

### Strefa czasowa
Aplikacja używa strefy czasowej `Europe/Warsaw`. Można zmienić w `src/config.py`:
```python
TIMEZONE = pytz.timezone('Europe/Warsaw')
```

### Harmonogram gierek (przykład)
- **Dzień gierki**: Środa 18:30
- **Otwarcie zapisów**: Poniedziałek 10:00
- **Losowanie**: Środa od 15:00

## 🛠️ Rozwój aplikacji

### Struktura plików
```
parkowa-ankiette/
├── app.py                 # Główna aplikacja (tylko routing)
├── github_scheduler.py    # 🤖 GITHUB ACTIONS SCHEDULER (niezależny!)
├── game_consts.yaml       # ⚙️ KONFIGURACJA CZASOWA (dni, godziny gierek)
├── requirements.txt       # Zależności Python
├── database_setup.sql     # Skrypt inicjalizujący bazę danych
├── GITHUB_ACTIONS_SETUP.md # 📖 Instrukcja konfiguracji GitHub Actions
├── .github/
│   └── workflows/
│       └── scheduler.yml  # ⚡ Workflow GitHub Actions (3x dziennie)
├── .streamlit/
│   └── secrets.toml      # Konfiguracja sekretów (lokalnie)
├── src/                   # Kod źródłowy aplikacji
│   ├── __init__.py
│   ├── config.py         # Konfiguracja i inicjalizacja Neon DB
│   ├── game_config.py    # Wczytywanie konfiguracji z YAML
│   ├── pages/            # Strony aplikacji
│   │   ├── __init__.py
│   │   ├── signup.py     # Strona zapisów na gierki
│   │   ├── list_players.py # Lista zapisanych graczy
│   │   ├── draw_teams.py # Losowanie składów drużyn
│   │   └── history.py    # Historia gierek
│   └── utils/            # Funkcje pomocnicze
│       ├── __init__.py
│       ├── auth.py       # Hashowanie i weryfikacja haseł
│       ├── datetime_utils.py # Obsługa dat i czasu
│       ├── game_utils.py # Operacje na gierkach w bazie
│       ├── signup_utils.py # Operacje na zapisach graczy
│       ├── team_utils.py # Logika losowania drużyn
│       ├── teams_db.py   # Operacje na drużynach w bazie
│       └── security.py   # 🛡️ Rate limiting i zabezpieczenia
└── README.md             # Dokumentacja
```

### Architektura modułowa

#### 🏠 **app.py** - Punkt wejścia
- Główna funkcja aplikacji
- Routing między stronami
- Sidebar nawigacji
- Importuje wszystkie potrzebne moduły

#### ⚙️ **src/config.py** - Konfiguracja podstawowa
- Ustawienia Streamlit (`page_config`)
- Inicjalizacja połączenia z Neon PostgreSQL
- Konfiguracja strefy czasowej

#### ⚙️ **game_consts.yaml** - Konfiguracja czasowa
- **Plik YAML w głównym katalogu**
- Wszystkie parametry czasowe w jednym miejscu
- Łatwa edycja bez znajomości programowania
- Dni tygodnia, godziny, komunikaty
- Konfiguracja składów drużyn

#### 📄 **src/pages/** - Strony aplikacji
Każda strona ma własny plik z logiką interfejsu:
- `signup.py` - Formularz zapisów i wypisów
- `list_players.py` - Wyświetlanie listy zapisanych graczy
- `draw_teams.py` - Interface losowania składów
- `history.py` - Przeglądanie historii gierek
- `system_status.py` - � Monitoring systemu i automatyki

#### 🛠️ **src/utils/** - Funkcje pomocnicze
Podzielone tematycznie dla łatwości utrzymania:
- `auth.py` - Bezpieczeństwo (bcrypt)
- `datetime_utils.py` - Obliczenia dat (środy, poniedziałki)
- `game_utils.py` - CRUD dla gierek
- `signup_utils.py` - CRUD dla zapisów
- `team_utils.py` - Algorytmy losowania
- `teams_db.py` - CRUD dla drużyn

### Dodawanie nowych funkcji

#### 🆕 Nowa strona
1. Utwórz plik w `src/pages/new_page.py`
2. Zaimplementuj funkcję `new_page(db: NeonDB)`
3. Dodaj import w `app.py`
4. Dodaj opcję w `st.sidebar.radio()`
5. Dodaj routing w funkcji `main()`

#### 🔧 Nowe funkcje pomocnicze
1. Dodaj funkcję do odpowiedniego pliku w `src/utils/`
2. Lub utwórz nowy plik jeśli to nowa kategoria
3. Importuj w potrzebnych miejscach

#### 🗄️ Nowe operacje bazodanowe
1. Dodaj funkcję do odpowiedniego pliku utils (np. `game_utils.py`)
2. Używaj spójnych konwencji nazewnictwa
3. Dodaj obsługę błędów z `try/except`

## 🔒 Bezpieczeństwo

### 🛡️ Zabezpieczenia aplikacji:
- **Hasła hashowane** - używamy bcrypt z salt
- **Bezpieczeństwo połączenia** - SSL wymagany dla wszystkich połączeń z Neon  
- **Rate limiting** - maksymalnie 3 zapisy/5 minut, 5 wypisów/5 minut
- **Walidacja danych** - sanityzacja i walidacja wszystkich inputów
- **Spam protection** - maksymalnie 50 zapisów na gierkę
- **Zabronione nazwy** - ochrona przed zastrzeżonymi nickami
- **Security logging** - logowanie podejrzanych aktywności

### 🔐 Konfiguracja security:
- **Database triggers** - automatyczna walidacja na poziomie bazy
- **Input sanitization** - oczyszczanie danych wejściowych
- **Error masking** - ukrywanie wrażliwych informacji w błędach
- **Secret masking** - ukrywanie tokenów w logach GitHub Actions

### ⚠️ Ograniczenia darmowych planów:
- **Neon**: 0.5GB storage, 3GB transfer/miesiąc, auto-suspend po 5 minutach
- **GitHub Actions**: 2000 minut/miesiąc (używamy ~90)
- **Streamlit Cloud**: 1 aplikacja, hibernacja po nieaktywności

## 📝 Licencja

MIT License - szczegóły w pliku LICENSE.

## 🤝 Kontakt

Wszelkie pytania i sugestie kieruj na GitHub Issues.
