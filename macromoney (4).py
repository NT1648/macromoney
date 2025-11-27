import streamlit as st
import pandas as pd
import numpy as np
import openai
import os
from typing import Dict
from math import sqrt

# =============================
#   STREAMLIT PAGE CONFIG
# =============================
st.set_page_config(
    page_title="MacroMoney v2.4",
    layout="wide",
)

# Custom Neon Gradient Styles
st.markdown("""
<style>
html, body, [class*="css"]  {
    font-family: 'Inter', sans-serif;
}
h1 {
    background: -webkit-linear-gradient(90deg, #3affff, #b600ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 900;
}
.section-card {
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #33333355;
    background: rgba(20,20,20,0.5);
    backdrop-filter: blur(8px);
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

# Title
st.markdown("<h1>MacroMoney – v2.4</h1>", unsafe_allow_html=True)
st.caption("Embedding-powered macro-aware portfolio engine (Demo Model)")

# =============================
#    API KEY FROM SECRETS
# =============================
api_key = st.secrets.get("OPENAI_API_KEY", None)
if api_key is None:
    st.error("No API key found. Set OPENAI_API_KEY in Streamlit Secrets.")
    st.stop()

openai.api_key = api_key

# =============================
#   SIDEBAR INPUTS
# =============================
with st.sidebar:
    st.header("Portfolio Inputs")

    capital = st.number_input("Capital Amount ($)", min_value=100.0, value=10000.0)

    st.subheader("Weights (%)")
    equity_w = st.number_input("Equities", 0, 100, 20)
    bond_w   = st.number_input("Bonds", 0, 100, 20)
    etf_w    = st.number_input("ETFs", 0, 100, 20)
    crypto_w = st.number_input("Cryptocurrency", 0, 100, 20)
    cmdty_w  = st.number_input("Commodities", 0, 100, 20)

    weights = {
        "Equities": equity_w,
        "Bonds": bond_w,
        "ETFs": etf_w,
        "Crypto": crypto_w,
        "Commodities": cmdty_w,
    }

    if sum(weights.values()) != 100:
        st.error("Weights must sum to 100%")
        st.stop()

    st.subheader("Investment Horizon")
    horizon_years = st.number_input("Years", min_value=0.1, max_value=30.0, value=1.0, step=0.1)

    st.subheader("Headline Input")
    headline = st.text_input("Enter a news headline:", "")

    analyze = st.button("Analyze Headline 🔍")


# =============================
#   THEMATIC DEFINITIONS
# =============================
# Hybrid comments: minimal explanations for clarity
THEMES = {
    "interest_rates": "Monetary policy, inflation, CPI, PPI, rate decisions, yields",
    "energy": "Oil, gas, commodities, OPEC, supply shocks",
    "tech": "Technology sector, AI, chips, semiconductors",
    "geopolitical": "Conflicts, wars, sanctions, cross-border tension",
    "fiscal": "Government spending, budgets, stimulus, deficits",
    "currency_fx": "Dollar index, forex, yen, yuan movements",
    "labor": "Jobs, unemployment, wages, labor conditions",
    "crypto": "Bitcoin, Ethereum, crypto markets, digital assets",
    "political_shock": "Assassinations, coups, leadership changes",
    "commodities": "Gold, metals, silver, precious metals"
}

# Short textual labels for better chart titles
DISPLAY_NAMES = {
    k: k.replace("_", " ").title() for k in THEMES
}

# =============================
#   EMBEDDING FUNCTION
# =============================
def get_embedding(text: str):
    """Generate embedding vector using OpenAI API."""
    response = openai.embeddings.create(
        model="text-embedding-3-large",
        input=text
    )
    return response.data[0].embedding


def cosine_sim(a, b):
    """Cosine similarity between vectors."""
    dot = sum(x*y for x, y in zip(a, b))
    norm_a = sqrt(sum(x*x for x in a))
    norm_b = sqrt(sum(x*x for x in b))
    return dot / (norm_a * norm_b)


# Pre-embed theme descriptions (so repeated queries are faster)
theme_embeddings = {t: get_embedding(desc) for t, desc in THEMES.items()}


# =============================
#   IMPACT + SEVERITY LOGIC
# =============================
def classify_headline(headline: str):
    """Embedding-based theme detection with multi-theme enhancement."""

    headline_emb = get_embedding(headline)

    sims = {}
    for theme, emb in theme_embeddings.items():
        sims[theme] = cosine_sim(headline_emb, emb)

    # Primary theme
    primary = max(sims, key=sims.get)
    primary_score = sims[primary]

    # Secondary theme if significantly strong
    secondary = None
    secondary_score = 0
    for t, val in sims.items():
        if t != primary and val > 0.75 * primary_score:
            secondary = t
            secondary_score = val

    return primary, primary_score, secondary, secondary_score


def compute_sentiment(headline: str):
    """Use embedding polarity to gauge risk-on / risk-off behavior."""
    pos_words = ["rallies", "optimism", "growth", "record high"]
    neg_words = ["crisis", "collapse", "fell", "war", "attack", "assassinated"]

    pos_score = sum([1 for w in pos_words if w in headline.lower()])
    neg_score = sum([1 for w in neg_words if w in headline.lower()])

    sentiment = pos_score - neg_score  # + = risk-on, - = risk-off

    return sentiment


def compute_severity(primary_score, secondary_score, sentiment, horizon_years):
    """Severity uses semantic strength + sentiment + horizon context."""

    severity = primary_score * 100  # Scale similarity to 0–100

    if secondary_score > 0:
        severity *= 1.15  # boost for multi-theme events

    if sentiment < 0:
        severity *= 1.2  # negative news tends to have stronger market impact

    if horizon_years > 3:
        severity *= 0.75  # long horizon → de-emphasize noise
    elif horizon_years < 1:
        severity *= 1.15  # short horizon → increase sensitivity

    return min(100, max(20, severity))


def horizon_threshold(severity, horizon_years):
    """Dynamic threshold for rebalancing necessity."""
    if horizon_years <= 1:
        return severity >= 20
    elif horizon_years <= 3:
        return severity >= 40
    return severity >= 70


# =============================
#   REBALANCING RULES
# =============================
rebalance_rules = {
    "interest_rates": {"Equities": -10, "Bonds": +15},
    "energy": {"Commodities": +15},
    "tech": {"Equities": +12},
    "geopolitical": {"Bonds": +10, "Commodities": +8, "Equities": -10},
    "fiscal": {"Equities": +10},
    "currency_fx": {"Crypto": -10, "Bonds": +5},
    "labor": {"Equities": -5, "Bonds": +5},
    "crypto": {"Crypto": +15},
    "political_shock": {"Bonds": +12, "Equities": -12},
    "commodities": {"Commodities": +15}
}


def apply_rebalance(weights: Dict[str, float], theme: str, severity: float):
    """Apply scaled rebalancing weights and renormalize."""
    new = weights.copy()
    intensity = severity / 100  # Scale to 0–1

    if theme in rebalance_rules:
        for asset, shift in rebalance_rules[theme].items():
            new[asset] += shift * intensity

    total = sum(new.values())
    for k in new:
        new[k] = round((new[k] / total) * 100, 2)

    return new


# =============================
#   MAIN ANALYSIS ENGINE
# =============================
if analyze and headline.strip():

    with st.spinner("Analyzing headline using embeddings…"):

        primary, p_score, secondary, s_score = classify_headline(headline)
        sentiment = compute_sentiment(headline)
        severity = compute_severity(p_score, s_score, sentiment, horizon_years)

    # Output UI Section
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.subheader("🧠 Headline Analysis")
    st.write(f"**Primary Theme:** {DISPLAY_NAMES[primary]}")
    if secondary:
        st.write(f"**Secondary Theme:** {DISPLAY_NAMES[secondary]} (boosted)")

    st.write(f"**Similarity Score:** {round(p_score,3)}")
    st.write(f"**Sentiment Factor:** {sentiment}")
    st.write(f"**Composite Severity:** {round(severity,2)} / 100")

    st.markdown("</div>", unsafe_allow_html=True)

    # Horizon filtering
    if not horizon_threshold(severity, horizon_years):
        st.info("Event not strong enough for rebalancing based on your horizon.")
        st.stop()

    # Rebalance
    new_weights = apply_rebalance(weights, primary, severity)

    # Dollar conversions
    current_vals = {k: round(v/100 * capital, 2) for k, v in weights.items()}
    new_vals     = {k: round(v/100 * capital, 2) for k, v in new_weights.items()}

    # Explanation
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.subheader("📈 Suggested Rebalancing")
    st.write(
        f"Based on **{DISPLAY_NAMES[primary]}** conditions and a severity of **{round(severity,1)}**, "
        "the model recommends adjusting allocations as shown below."
    )

    df = pd.DataFrame({
        "Current %": pd.Series(weights),
        "Suggested %": pd.Series(new_weights),
        "Current $": pd.Series(current_vals),
        "Suggested $": pd.Series(new_vals)
    })

    st.dataframe(df.style.format("{:.2f}"))
    st.markdown("</div>", unsafe_allow_html=True)

    # Chart
    st.bar_chart(df[["Current %", "Suggested %"]])




