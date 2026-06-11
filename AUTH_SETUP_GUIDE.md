# Konfiguracja logowania (Google / Facebook)

Aplikacja używa natywnego logowania Streamlit (`st.login`) przez OpenID Connect.
Hasła zniknęły całkowicie — gracz loguje się kontem Google lub Facebook,
a znajomych bez konta dopisuje jako **gości**.

Wymagania: `streamlit >= 1.47` oraz `Authlib >= 1.3.2` (są w `requirements.txt`).

## 1. Wspólna sekcja `[auth]` w secrets

W Streamlit Cloud: **Settings → Secrets**. Lokalnie: `.streamlit/secrets.toml`.

```toml
admin_emails = ["twoj-email@gmail.com"]   # admini (usuwanie graczy, losowanie poza oknem)

[auth]
redirect_uri = "https://TWOJA-APKA.streamlit.app/oauth2callback"
cookie_secret = "DLUGI-LOSOWY-CIAG-ZNAKOW"
```

- `redirect_uri` lokalnie: `http://localhost:8501/oauth2callback`
- `cookie_secret` wygeneruj np. `python3 -c "import secrets; print(secrets.token_hex(32))"`
- **Uwaga (TOML):** `admin_emails` musi być nad pierwszą sekcją `[...]`,
  inaczej trafi do złej sekcji.

## 2. Google

1. Wejdź na [console.cloud.google.com](https://console.cloud.google.com) → utwórz projekt (np. `parkowa`).
2. **APIs & Services → OAuth consent screen**: typ **External**, uzupełnij nazwę
   i e-mail, scopes zostaw domyślne (email, profile, openid), opublikuj aplikację
   (Publishing status: **In production** — inaczej zaloguje się tylko 100 testerów).
3. **APIs & Services → Credentials → Create credentials → OAuth client ID**:
   - Application type: **Web application**
   - Authorized redirect URIs — dodaj **obydwa**:
     - `https://TWOJA-APKA.streamlit.app/oauth2callback`
     - `http://localhost:8501/oauth2callback`
4. Skopiuj Client ID i Client secret do secrets:

```toml
[auth.google]
client_id = "....apps.googleusercontent.com"
client_secret = "..."
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

## 3. Facebook

1. Wejdź na [developers.facebook.com](https://developers.facebook.com) → **Create App**
   → use case: **Authenticate and request data from users with Facebook Login**.
2. W produkcie **Facebook Login → Settings** dodaj **Valid OAuth Redirect URIs**:
   - `https://TWOJA-APKA.streamlit.app/oauth2callback`
   - `http://localhost:8501/oauth2callback`
3. **App settings → Basic**: skopiuj App ID i App secret. Przełącz aplikację w tryb
   **Live** (inaczej zalogują się tylko testerzy aplikacji).
4. Dodaj do secrets:

```toml
[auth.facebook]
client_id = "APP_ID"
client_secret = "APP_SECRET"
server_metadata_url = "https://www.facebook.com/.well-known/openid-configuration"
```

Przyciski logowania pojawiają się automatycznie dla każdego skonfigurowanego
providera — możesz zacząć od samego Google i dodać Facebooka później.

## 4. Migracja bazy

Jednorazowo uruchom `migrations/001_social_auth.sql` (Supabase → SQL Editor).
Migracja jest addytywna — stare zapisy zostają.

## 5. Lokalny development bez OAuth

Nie chcesz konfigurować OAuth lokalnie? Odkomentuj w `.streamlit/secrets.toml`:

```toml
[dev_user]
enabled = true
email = "dev@example.com"
name = "Dev Tester"
```

Aplikacja zachowa się tak, jakby ten użytkownik był zalogowany.
**Nigdy nie włączaj `dev_user` w produkcyjnych secrets.**

## 6. Jak działają uprawnienia

| Akcja | Kto może |
|---|---|
| Zapisanie się / wypisanie siebie | zalogowany użytkownik |
| Dodanie gościa (limit w `game_consts.yaml` → `guests.max_per_user`) | zalogowany użytkownik |
| Wypisanie gościa | osoba, która go dodała + admin |
| Usunięcie dowolnego wpisu | admin (`admin_emails`) |
| Losowanie składów | zalogowani w oknie losowania; admin zawsze |

Wpisy sprzed migracji (z czasów haseł) nie mają przypisanego konta —
może je wypisać tylko admin.
