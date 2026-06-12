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
    padding-top: 4.5rem !important;  /* clear the fixed top nav/toolbar */
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

/* Google account buttons: same multicolor "G" logo, colour-coded by action
   (green = join, red = leave) so it's obvious which is which. */
[class*="st-key-gbtn_"] button {
    display: inline-flex; align-items: center; justify-content: center; gap: 0.6rem;
    font-weight: 700; border-radius: 12px;
}
[class*="st-key-gbtn_"] button::before {
    content: ""; width: 1.2rem; height: 1.2rem; flex: 0 0 auto;
    background-repeat: no-repeat; background-position: center; background-size: contain;
    background-image: url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'><path fill='%23EA4335' d='M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z'/><path fill='%234285F4' d='M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z'/><path fill='%23FBBC05' d='M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z'/><path fill='%2334A853' d='M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z'/></svg>");
}
/* Join = soft green */
.st-key-gbtn_signup button {
    background: #F3F8F4; color: #2F6A47; border: 1.5px solid #CFE3D5;
}
.st-key-gbtn_signup button:hover {
    background: #EAF3ED; color: #235439; border-color: #A9D0B6;
}
/* Leave = soft red */
.st-key-gbtn_signout button {
    background: #FBF3F2; color: #A4554E; border: 1.5px solid #ECCFCB;
}
.st-key-gbtn_signout button:hover {
    background: #F6E7E4; color: #8F4640; border-color: #DDB1AB;
}

/* Destructive (sign-out / remove) buttons */
[class*="st-key-remove"] button {
    background: #FFFFFF; color: #B3261E; border: 1px solid #ECC8C5;
}
[class*="st-key-remove"] button:hover {
    background: #FBEDEC; color: #B3261E; border-color: #B3261E;
}

/* Brand wordmark (doubles as the page header on the signups page) */
.pk-brand { display: flex; align-items: center; gap: 0.6rem; margin: 0 0 0.15rem; flex-wrap: wrap; }
.pk-brand-mark { display: inline-flex; }
.pk-brand-mark svg { display: block; }
.pk-brand-text { font-size: 1.8rem; font-weight: 800; letter-spacing: -0.03em; color: #15301F; }
.pk-brand-tag {
    font-size: 0.74rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em;
    color: #8B968A; padding-top: 0.5rem;
}

/* Page header */
.pk-h1 { font-size: 1.85rem; font-weight: 800; letter-spacing: -0.02em; color: #15301F; margin: 0; }
.pk-sub { color: #7A8578; font-weight: 500; margin: 0.15rem 0 1.1rem; }

/* Hero card */
.pk-hero {
    position: relative;
    overflow: hidden;
    background: linear-gradient(135deg, #1E7A46 0%, #135A33 100%);
    border-radius: 20px;
    padding: 1.5rem 1.7rem;
    color: #FFFFFF;
    margin-bottom: 1.2rem;
    box-shadow: 0 10px 30px rgba(19, 90, 51, 0.18);
}
.pk-hero-body { position: relative; z-index: 1; }
.pk-hero-deco {
    position: absolute; top: 0; bottom: 0; right: 18px;
    height: 100%; width: auto; pointer-events: none; z-index: 0;
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
.pk-table th:last-child { text-align: right; }
.pk-table td {
    padding: 0.55rem 0.6rem;
    border-bottom: 1px solid #F0F2EB;
    font-weight: 600; color: #22302A;
}
.pk-table tr:last-child td { border-bottom: none; }
.pk-table tbody tr:nth-child(even) td { background: #F7F9F3; }
.pk-table td.pk-num { color: #9AA597; font-weight: 700; width: 2.2rem; }
.pk-table td.pk-time {
    color: #22302A; font-weight: 700; white-space: nowrap; text-align: right;
    width: 1%; font-variant-numeric: tabular-nums;
}
.pk-time-clock { color: #9AA597; font-weight: 500; font-size: 0.86em; }
.pk-table tr.pk-row-me td { background: #F0F8F2; }
.pk-table tr.pk-row-me td:first-child { box-shadow: inset 3px 0 0 #1E7A46; }

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
    margin-bottom: 0.6rem; color: #15301F;
}
.pk-team-jersey { display: inline-flex; }
.pk-team-jersey svg { display: block; }
.pk-team-count {
    margin-left: auto; min-width: 1.5rem; text-align: center;
    background: #EEF1E9; color: #67705F; border-radius: 999px;
    font-size: 0.78rem; font-weight: 800; padding: 0.1rem 0.5rem;
}
.pk-team-players { display: flex; flex-direction: column; gap: 0.05rem; }
.pk-player {
    display: flex; align-items: center; gap: 0.55rem;
    padding: 0.2rem 0; border-bottom: 1px solid #F2F4ED;
}
.pk-player:last-child { border-bottom: none; }
.pk-jersey { display: inline-flex; flex: 0 0 auto; }
.pk-jersey svg { display: block; }
.pk-player-name { font-weight: 600; color: #22302A; }

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
    padding: 1.8rem 1rem 2.2rem;
    border: 1.5px dashed #D7DCCF;
    border-radius: 16px;
    background: #FCFCFA;
}
.pk-empty-illust { width: 132px; height: auto; margin: 0 auto 0.6rem; display: block; }
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
