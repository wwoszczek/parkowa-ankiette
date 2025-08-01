# 🏆 Parkowa Ankieta - Cotygodniowe Gierki Piłkarskie

Aplikacja Streamlit do organizowania cotygodniowych gierek piłkarskich z automatycznym zarządzaniem zapisami, losowaniem składów i historią gier.

## ⚡ Funkcjonalności

### 🗓️ Automatyczne zarządzanie gierkami
- Gierki odbywają się w **środy o 18:30**
- Zapisy otwierają się automatycznie **w poniedziałki o 10:00**
- Gierki stają się nieaktywne po czasie rozpoczęcia

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
- Konto Supabase
- Konto Streamlit Cloud (opcjonalne, do deploymentu)

### 1. Klonowanie repozytorium
```bash
git clone https://github.com/wwoszczek/parkowa-ankiette.git
cd parkowa-ankiette
```

### 2. Instalacja zależności
```bash
pip install -r requirements.txt
```

### 3. Konfiguracja bazy danych Supabase

#### 3.1 Utworzenie projektu w Supabase
1. Idź na [supabase.com](https://supabase.com)
2. Utwórz nowy projekt
3. Skopiuj **URL** i **anon key** z ustawień projektu

#### 3.2 Utworzenie tabel
1. W Supabase przejdź do **SQL Editor**
2. Wykonaj skrypt z pliku `database_setup.sql`

### 4. Konfiguracja sekretów

#### Lokalne uruchomienie
Edytuj plik `.streamlit/secrets.toml`:
```toml
[supabase]
url = "your_supabase_project_url"
key = "your_supabase_anon_key"
```

#### Deploy na Streamlit Cloud
1. W ustawieniach aplikacji na Streamlit Cloud
2. Dodaj sekrety w sekcji **Secrets**:
```toml
[supabase]
url = "your_supabase_project_url"
key = "your_supabase_anon_key"
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
6. Dodaj sekrety Supabase w ustawieniach aplikacji
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
├── app.py                 # Główna aplikacja (tylko routing i inicjalizacja)
├── game_consts.yaml       # ⚙️ KONFIGURACJA CZASOWA (dni, godziny gierek)
├── requirements.txt       # Zależności Python
├── database_setup.sql     # Skrypt inicjalizujący bazę danych
├── .streamlit/
│   └── secrets.toml      # Konfiguracja sekretów (lokalnie)
├── src/                   # Kod źródłowy aplikacji
│   ├── __init__.py
│   ├── config.py         # Konfiguracja i inicjalizacja Supabase
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
│       └── teams_db.py   # Operacje na drużynach w bazie
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
- Inicjalizacja klienta Supabase
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
2. Zaimplementuj funkcję `new_page(supabase: Client)`
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

- Hasła są hashowane używając bcrypt
- Każdy gracz może wypisać się tylko znając swoje hasło
- Baza danych ma włączone Row Level Security
- Unikalne ograniczenia na nickname w ramach jednej gierki

## 📝 Licencja

MIT License - szczegóły w pliku LICENSE.

## 🤝 Kontakt

Wszelkie pytania i sugestie kieruj na GitHub Issues.
