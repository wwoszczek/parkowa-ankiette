"""
Identity via Streamlit native OIDC login (st.login / st.user).

Secrets layout (see AUTH_SETUP_GUIDE.md):
    admin_emails = ["..."]          # root level, optional
    [auth]            redirect_uri, cookie_secret
    [auth.google]     client_id, client_secret, server_metadata_url
    [auth.facebook]   client_id, client_secret, server_metadata_url
    [dev_user]        enabled, email, name   # local development only
"""

import streamlit as st

_PROVIDER_LABELS = {
    "google": "Kontynuuj z Google",
    "facebook": "Kontynuuj z Facebookiem",
}


def auth_configured() -> bool:
    try:
        return "auth" in st.secrets
    except Exception:
        return False


def available_providers() -> list:
    """Providers that have a complete [auth.<provider>] section in secrets."""
    if not auth_configured():
        return []
    auth = st.secrets["auth"]
    return [p for p in _PROVIDER_LABELS if p in auth and "client_id" in auth[p]]


def _real_login() -> bool:
    return auth_configured() and bool(getattr(st.user, "is_logged_in", False))


def get_current_user():
    """Returns {'email', 'name'} for the signed-in user, else None."""
    if _real_login():
        email = st.user.email
        return {"email": email, "name": st.user.name or email}

    # Local development fallback - never enable in production secrets.
    dev = st.secrets.get("dev_user") if "dev_user" in st.secrets else None
    if dev and dev.get("enabled"):
        return {"email": dev["email"], "name": dev.get("name", dev["email"])}

    return None


def is_admin(user=None) -> bool:
    user = user or get_current_user()
    if not user:
        return False
    admins = [str(a).lower() for a in st.secrets.get("admin_emails", [])]
    return user["email"].lower() in admins


def login_panel():
    """Login buttons for every configured provider."""
    providers = available_providers()
    if not providers:
        st.info(
            "Zapisy wymagają zalogowania, ale logowanie nie jest jeszcze "
            "skonfigurowane na tym wdrożeniu. Instrukcja: AUTH_SETUP_GUIDE.md."
        )
        return
    st.caption("Zapisujesz się przez swoje konto — bez zakładania hasła.")
    for provider in providers:
        if st.button(_PROVIDER_LABELS[provider], key=f"login_{provider}", width="stretch"):
            st.login(provider)


def logout_control():
    """Sign-out button (or a dev-mode hint when using the fake dev user)."""
    if _real_login():
        if st.button("Wyloguj się", key="logout_btn", type="tertiary"):
            st.logout()
    elif get_current_user():
        st.caption("Tryb deweloperski (dev_user w secrets).")
