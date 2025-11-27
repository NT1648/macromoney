
import streamlit as st

# -------------------------------
# Page Setup
# -------------------------------
st.set_page_config(page_title="MacroMoney", layout="centered")

st.markdown("""

# 💹 MacroMoney – Intelligent Macro-Aware Portfolio Engine  
### _Demo Model (v2.1)_

This demo analyzes a news headline, evaluates macro relevance, scores impact, and recommends a portfolio rebalance.  
""")

st.markdown("---")

# -------------------------------
# Asset Inputs
# -------------------------------
st.markdown("## 🧮 Step 1: Build Your Base Portfolio")

st.info("Enter your custom portfolio weights. They must sum to **100%**.")

equity_w = st.number_input("Equities (%)", 0, 100, 20)
bond_w   = st.number_input("Bonds (%)", 0, 100, 20)
etf_w    = st.number_input("ETFs (%)", 0, 100, 20)
crypto_w = st.number_input("Cryptocurrency (%)", 0, 100, 20)
cmdty_w  = st.number_input("Commodities (%)", 0, 100, 20)

initial_weights = {
    "Equities": equity_w,
    "Bonds": bond_w,
    "ETFs": etf_w,
    "Crypto": crypto_w,
    "Commodities": cmdty_w
}

total_alloc = sum(initial_weights.values())

if total_alloc != 100:
    st.error(f"Current total allocation: {total_alloc}%. Please adjust to 100%.")
    st.stop()

st.markdown("---")

# -------------------------------
# Headline Input
# -------------------------------
st.markdown("## 📰 Step 2: Enter a Market Headline")

headline = st.text_input("Paste headline to analyze...", placeholder="e.g., Federal Reserve raises rates by 0.5%")

analyze_button = st.button("🔍 Analyze Headline")

# -------------------------------
# Classification Data
# -------------------------------
macro_themes = {
    "interest_rate": ["interest", "inflation", "cpi", "ppi", "fed", "ecb", "rate hike", "yields"],
    "energy": ["oil", "gas", "opec", "energy supply", "pipeline", "crude"],
    "tech": ["ai", "technology", "chip", "semiconductor", "software"],
    "geopolitical": ["conflict", "war", "border", "sanction", "missile", "tension"],
    "fiscal": ["stimulus", "government spending", "budget", "subsidy"],
    "currency": ["forex", "currency", "yen", "yuan", "liquidity", "dollar index"],
    "labor": ["unemployment", "jobs", "wage", "labor market"],
    "crypto": ["bitcoin", "crypto", "ethereum", "token", "blockchain"],
    "political_shock": ["assassination", "prime minister", "president", "resignation", "leader death"]
}

micro_themes = {
    "earnings": ["earnings", "quarterly", "revenue", "profit", "guidance"],
    "company_specific": ["launch", "ceo", "merger", "acquisition", "company"],
    "sector_only": ["retail sales", "chip demand", "housing data"]
}

irrelevant_keywords = [
    "accident", "celebrity", "movie", "festival", "sports", "award", "weather", "crime",
]

severity_weights = {
    "crisis": 30, "war": 30, "sanction": 25, "default": 30,
    "surge": 20, "collapse": 20, "emergency": 20,
    "hike": 15, "cut": 15, "inflation": 15,
    "mild": 5, "slight": 5
}

def classify_news(text):
    text = text.lower()

    for w in irrelevant_keywords:
        if w in text:
            return "irrelevant", "Not market-affecting"

    for key, words in micro_themes.items():
        for w in words:
            if w in text:
                return "micro", key

    for key, words in macro_themes.items():
        for w in words:
            if w in text:
                return "macro", key

    return "irrelevant", "No macro/micro signals detected"

def compute_impact_score(text):
    text = text.lower()
    score = 0
    for word, pts in severity_weights.items():
        if word in text:
            score += pts
    return min(score, 100)

macro_rebalance_rules = {
    "interest_rate": {"Equities": -10, "Bonds": +10},
    "energy": {"Commodities": +15, "Equities": -5},
    "tech": {"Equities": +10},
    "geopolitical": {"Bonds": +10, "Commodities": +5, "Equities": -10},
    "fiscal": {"Equities": +10},
    "currency": {"Bonds": +5, "Crypto": -10},
    "labor": {"Equities": -5, "Bonds": +5},
    "crypto": {"Crypto": +15},
    "political_shock": {"Bonds": +10, "Equities": -10}
}

def apply_rebalance(base, theme, intensity_factor):
    new = base.copy()
    if theme not in macro_rebalance_rules:
        return new
    for asset, shift in macro_rebalance_rules[theme].items():
        new[asset] += shift * intensity_factor
    total = sum(new.values())
    for k in new:
        new[k] = round(new[k] / total * 100, 2)
    return new

# -------------------------------
# Output
# -------------------------------
if analyze_button and headline:
    event_type, theme = classify_news(headline)
    impact = compute_impact_score(headline)

    st.markdown("## 🧠 Analysis Result")

    st.write(f"**Event Type:** `{event_type.upper()}`")
    st.write(f"**Detected Theme:** `{theme}`")
    st.write(f"**Impact Score:** `{impact}/100`")

    if event_type == "irrelevant":
        st.warning("This event is not market-relevant. No portfolio change recommended.")
        st.stop()

    if event_type == "micro":
        st.info("This is a *micro-level* event (earnings/sector news). No portfolio changes required.")
        st.stop()

    if impact < 25:
        st.info("Macro event detected, but impact is too low to justify rebalancing.")
        st.stop()

    st.markdown("## 🔄 Suggested Portfolio Rebalance")

    intensity_factor = impact / 100
    updated_port = apply_rebalance(initial_weights, theme, intensity_factor)

    st.success("Rebalance complete based on macro signal and impact score.")
    st.json(updated_port)

st.markdown("---")
st.caption("MacroMoney Demo v2.1 — Not financial advice. For research/testing only.")
