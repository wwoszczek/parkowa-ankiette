"""
Identity via Streamlit native OIDC login (st.login / st.user).

Secrets layout (Google OAuth setup is documented in README.md):
    admin_emails = ["..."]          # root level, optional
    [auth]            redirect_uri, cookie_secret
    [auth.google]     Google client + client_kwargs.prompt = "select_account"
    [auth.wypis]      SAME Google client - distinct provider name, see below
    [dev_user]        enabled, email, name   # local development only

Why two provider sections for one Google client: session state does not
survive the OAuth redirect, but Streamlit stores the *provider name* in the
identity cookie. Signing up logs in via provider "google", signing out via
provider "wypis" - after the redirect `st.user.provider` tells us exactly
which button started the flow, so the intended action completes reliably.
"""

import time

import streamlit as st

# action -> provider section used for its login flow
ACTION_PROVIDERS = {"signup": "google", "signout": "wypis"}


def auth_configured() -> bool:
    try:
        return "auth" in st.secrets
    except Exception:
        return False


def _provider_ready(name: str) -> bool:
    return auth_configured() and name in st.secrets["auth"] and "client_id" in st.secrets["auth"][name]


def auth_ready() -> bool:
    """Both action providers are configured."""
    return all(_provider_ready(p) for p in ACTION_PROVIDERS.values())


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


def is_dev_user() -> bool:
    """True when the identity comes from the dev_user fake, not real OAuth."""
    return get_current_user() is not None and not _real_login()


def is_admin(user=None) -> bool:
    user = user or get_current_user()
    if not user:
        return False
    admins = [str(a).lower() for a in st.secrets.get("admin_emails", [])]
    return user["email"].lower() in admins


def _seconds_since_login():
    """Seconds since the OAuth token was issued, or None when unknown.

    Streamlit copies all ID-token claims into the identity cookie, so `iat`
    marks the moment of the actual Google login. A small value means the user
    *just* came back from the account chooser - i.e. they pressed a button to
    get here - as opposed to carrying a days-old session cookie.
    """
    if not _real_login():
        return None
    iat = getattr(st.user, "iat", None)
    if not iat:
        return None
    try:
        return max(0.0, time.time() - float(iat))
    except (TypeError, ValueError):
        return None


@st.cache_resource
def _claimed_logins() -> set:
    """Server-side memory of already-handled logins, so reloading the page
    right after an action does not replay it (session state dies on reload)."""
    return set()


def claim_fresh_login(max_age_seconds: int = 45):
    """Return "signup"/"signout" exactly once for a just-completed OAuth login.

    None when: not logged in, the login is older than the window (a carried
    cookie session), the provider is unknown, or this login was already
    handled. Never returns an action for the dev_user fake.
    """
    age = _seconds_since_login()
    if age is None or age > max_age_seconds:
        return None
    provider = getattr(st.user, "provider", None)
    action = next((a for a, p in ACTION_PROVIDERS.items() if p == provider), None)
    if action is None:
        return None
    key = (st.user.email.lower(), str(provider), str(getattr(st.user, "iat", "")))
    claimed = _claimed_logins()
    if key in claimed:
        return None
    claimed.add(key)
    return action


def start_action_login(action: str):
    """Kick off the Google account chooser for the given action."""
    st.login(ACTION_PROVIDERS[action])


def logout_control():
    """Sign-out button (or a dev-mode hint when using the fake dev user)."""
    if _real_login():
        if st.button("Wyloguj się", key="logout_btn", type="tertiary"):
            st.logout()
    elif get_current_user():
        st.caption("Tryb deweloperski (dev_user w secrets)")
