# Przykłady konfiguracji czasowej

## 📋 Domyślna konfiguracja (obecna)
```python
# środy 18:30
GAME_DAY = 2
GAME_START_HOUR = 18
GAME_START_MINUTE = 30

# poniedziałki 10:00
SIGNUP_OPEN_DAY = 0
SIGNUP_OPEN_HOUR = 10
SIGNUP_OPEN_MINUTE = 0

# środy 15:00
DRAW_ALLOWED_DAY = 2
DRAW_ALLOWED_HOUR = 15
DRAW_ALLOWED_MINUTE = 0
```

## 🔄 Przykładowe alternatywne konfiguracje

### Gierki w piątki wieczorem
```python
# piątki 19:00
GAME_DAY = 4
GAME_START_HOUR = 19
GAME_START_MINUTE = 0

# środy 12:00 (zapisy otwierają się wcześniej)
SIGNUP_OPEN_DAY = 2
SIGNUP_OPEN_HOUR = 12
SIGNUP_OPEN_MINUTE = 0

# piątki 16:00 (losowanie 3h przed grą)
DRAW_ALLOWED_DAY = 4
DRAW_ALLOWED_HOUR = 16
DRAW_ALLOWED_MINUTE = 0
```

### Gierki weekendowe (soboty)
```python
# soboty 10:00 (rano)
GAME_DAY = 5
GAME_START_HOUR = 10
GAME_START_MINUTE = 0

# czwartki 18:00
SIGNUP_OPEN_DAY = 3
SIGNUP_OPEN_HOUR = 18
SIGNUP_OPEN_MINUTE = 0

# soboty 8:00 (losowanie rano przed grą)
DRAW_ALLOWED_DAY = 5
DRAW_ALLOWED_HOUR = 8
DRAW_ALLOWED_MINUTE = 0
```

### Gierki biznesowe (wtorki lunch)
```python
# wtorki 12:00 (lunch break)
GAME_DAY = 1
GAME_START_HOUR = 12
GAME_START_MINUTE = 0

# poniedziałki 9:00
SIGNUP_OPEN_DAY = 0
SIGNUP_OPEN_HOUR = 9
SIGNUP_OPEN_MINUTE = 0

# wtorki 11:00 (1h przed grą)
DRAW_ALLOWED_DAY = 1
DRAW_ALLOWED_HOUR = 11
DRAW_ALLOWED_MINUTE = 0
```

## 🎨 Konfiguracja składów drużyn

### Dodanie nowej konfiguracji (np. dla 16 graczy)
```python
TEAM_CONFIGS = {
    # ... istniejące konfiguracje ...
    16: {
        "teams": 2,
        "colors": ["czerwona", "czarna"],
        "players_per_team": [8, 8]
    }
}
```

### Konfiguracja z 4 drużynami (np. dla 20 graczy)
```python
TEAM_CONFIGS = {
    # ... istniejące konfiguracje ...
    20: {
        "teams": 4,
        "colors": ["czerwona", "czarna", "biała", "żółta"],
        "players_per_team": [5, 5, 5, 5]
    }
}
```

### Nierówne drużyny (np. dla 15 graczy)
```python
TEAM_CONFIGS = {
    # ... istniejące konfiguracje ...
    15: {
        "teams": 3,
        "colors": ["czerwona", "czarna", "biała"],
        "players_per_team": [5, 5, 5]  # Jedna osoba zostanie rezerwowym
    }
}
```

## 📅 Mapowanie dni tygodnia
```
0 = Poniedziałek
1 = Wtorek  
2 = Środa
3 = Czwartek
4 = Piątek
5 = Sobota
6 = Niedziela
```
