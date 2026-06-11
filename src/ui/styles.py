"""
Global stylesheet injected once per page render.
"""

import streamlit as st

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');

/* Typography - restore icon fonts after the global override */
* { font-family: 'Manrope', -apple-system, 'Segoe UI', sans-serif; }
[data-testid="stIconMaterial"], [class*="material-symbols"] {
    font-family: 'Material Symbols Rounded' !important;
}
code, pre, kbd { font-family: ui-monospace, 'SF Mono', Menlo, monospace !important; }

h1, h2, h3, h4 { letter-spacing: -0.02em; font-weight: 800 !important; }

[data-testid="stAppViewContainer"] .block-container {
    max-width: 900px;
    padding-top: 1.6rem;
}

[data-testid="stAppDeployButton"] { display: none; }
footer { visibility: hidden; }

/* Widgets */
.stButton > button, [data-testid="stFormSubmitButton"] > button {
    border-radius: 12px;
    font-weight: 700;
}
[data-testid="stForm"] {
    border: 1px solid #E6E9E1;
    border-radius: 16px;
    background: #FFFFFF;
    padding: 1.1rem 1.2rem;
}
[data-testid="stAlert"] { border-radius: 14px; }
[data-testid="stExpander"] details { border-radius: 14px; }
.stTextInput input { border-radius: 10px; }

/* Branded login buttons (matched by widget key) */
.st-key-login_google button {
    background: #FFFFFF; color: #3C4043; border: 1.5px solid #DADCE0;
}
.st-key-login_google button:hover { border-color: #1E7A46; color: #1E7A46; }
.st-key-login_facebook button {
    background: #1877F2; color: #FFFFFF; border: none;
}
.st-key-login_facebook button:hover { background: #0F63D6; color: #FFFFFF; }

/* Destructive (sign-out / remove) buttons */
[class*="st-key-remove"] button {
    background: #FFFFFF; color: #B3261E; border: 1px solid #ECC8C5;
}
[class*="st-key-remove"] button:hover {
    background: #FBEDEC; color: #B3261E; border-color: #B3261E;
}

/* Page header */
.pk-h1 { font-size: 1.85rem; font-weight: 800; letter-spacing: -0.02em; color: #15301F; margin: 0; }
.pk-sub { color: #7A8578; font-weight: 500; margin: 0.15rem 0 1.1rem; }

/* Hero card */
.pk-hero {
    background: linear-gradient(135deg, #1E7A46 0%, #135A33 100%);
    border-radius: 20px;
    padding: 1.5rem 1.7rem;
    color: #FFFFFF;
    margin-bottom: 1.2rem;
    box-shadow: 0 10px 30px rgba(19, 90, 51, 0.18);
}
.pk-hero-label {
    font-size: 0.78rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.12em; opacity: 0.75;
}
.pk-hero-date { font-size: 1.65rem; font-weight: 800; letter-spacing: -0.02em; margin: 0.15rem 0 0.05rem; }
.pk-hero-meta { font-size: 1rem; font-weight: 600; opacity: 0.92; }
.pk-hero-chips { margin-top: 0.85rem; display: flex; gap: 0.5rem; flex-wrap: wrap; }
.pk-chip {
    display: inline-block;
    background: rgba(255, 255, 255, 0.16);
    border: 1px solid rgba(255, 255, 255, 0.25);
    padding: 0.22rem 0.7rem;
    border-radius: 999px;
    font-size: 0.85rem; font-weight: 700;
}

/* Section heading */
.pk-section { font-size: 1.12rem; font-weight: 800; letter-spacing: -0.01em; color: #15301F; margin: 1.1rem 0 0.5rem; }

/* Cards & player table */
.pk-card {
    background: #FFFFFF;
    border: 1px solid #E6E9E1;
    border-radius: 16px;
    padding: 0.5rem 0.9rem;
    box-shadow: 0 1px 2px rgba(20, 32, 26, 0.04);
}
.pk-table { width: 100%; border-collapse: collapse; font-size: 0.95rem; }
.pk-table th {
    text-align: left; padding: 0.5rem 0.6rem;
    font-size: 0.72rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.08em; color: #7A8578;
    border-bottom: 1px solid #E6E9E1;
}
.pk-table td {
    padding: 0.55rem 0.6rem;
    border-bottom: 1px solid #F0F2EB;
    font-weight: 600; color: #22302A;
}
.pk-table tr:last-child td { border-bottom: none; }
.pk-table td.pk-num { color: #9AA597; font-weight: 700; width: 2.2rem; }
.pk-table td.pk-time { color: #8B968A; font-weight: 500; white-space: nowrap; text-align: right; }
.pk-row-me td { background: #F0F8F2; }
.pk-row-me td:first-child { box-shadow: inset 3px 0 0 #1E7A46; }

/* Badges */
.pk-badge {
    display: inline-block; vertical-align: middle;
    margin-left: 0.45rem; padding: 0.08rem 0.5rem;
    border-radius: 999px; font-size: 0.72rem; font-weight: 700;
    background: #EEF1E9; color: #67705F;
}
.pk-badge-you { background: #DCEFE2; color: #176A3E; }
.pk-badge-guest { background: #FBF3DD; color: #8A6D1D; }

/* Team cards */
.pk-teams {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 0.9rem;
    margin: 0.4rem 0 0.8rem;
}
.pk-team {
    background: #FFFFFF;
    border: 1px solid #E6E9E1;
    border-top: 4px solid var(--team, #1E7A46);
    border-radius: 14px;
    padding: 0.9rem 1.1rem;
}
.pk-team-head {
    display: flex; align-items: center; gap: 0.5rem;
    font-weight: 800; font-size: 1rem; letter-spacing: -0.01em;
    margin-bottom: 0.5rem; color: #15301F;
}
.pk-team-dot {
    width: 0.8rem; height: 0.8rem; border-radius: 50%;
    background: var(--team); border: 1px solid rgba(0, 0, 0, 0.15);
}
.pk-team ol { margin: 0; padding-left: 1.3rem; }
.pk-team li { padding: 0.13rem 0; font-weight: 600; color: #22302A; }

/* Stat chips */
.pk-stats { display: flex; gap: 0.6rem; flex-wrap: wrap; margin: 0.2rem 0 0.9rem; }
.pk-stat {
    background: #FFFFFF; border: 1px solid #E6E9E1;
    border-radius: 14px; padding: 0.55rem 1rem; min-width: 110px;
}
.pk-stat-num { font-size: 1.3rem; font-weight: 800; color: #15301F; }
.pk-stat-label {
    font-size: 0.72rem; font-weight: 700; color: #7A8578;
    text-transform: uppercase; letter-spacing: 0.06em;
}

/* Empty state */
.pk-empty {
    text-align: center;
    padding: 2.4rem 1rem;
    border: 1.5px dashed #D7DCCF;
    border-radius: 16px;
    background: #FCFCFA;
}
.pk-empty-title { font-weight: 800; font-size: 1.05rem; color: #3A463E; }
.pk-empty-hint { color: #7A8578; font-size: 0.92rem; margin-top: 0.25rem; }

/* Account strip on the signup page */
.pk-account { color: #51604F; font-size: 0.9rem; font-weight: 600; margin-bottom: 0.4rem; }
.pk-account b { color: #15301F; }
</style>
"""


def inject_styles():
    """Inject the global stylesheet (call once per render, before page content)."""
    st.markdown(_CSS, unsafe_allow_html=True)
