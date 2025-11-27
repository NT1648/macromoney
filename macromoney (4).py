import streamlit as st
import pandas as pd
import numpy as np
import openai
openai.api_key = st.secrets["OPENAI_API_KEY"]
# -------------------------------
# Page Setup
# -------------------------------
st.set_page_config(page_title="MacroMoney v2.4", layout="centered")

st.markdown("""
# 💹 MacroMoney – Horizon-Aware Macro Portfolio Engine  
### _Demo Model (v2.4)_

Analyze a news headline, score macro relevance, apply horizon-aware rebalancing, and view suggested portfolio allocation.
""")

st.markdown("---")

# -------------------------------
# User Inputs
# -------------------------------
st.markdown("## 🧮 Step 1: Define Portfolio & Horizon")

capital = st.number_input("Capital Amount ($)", min_value=1000, value=10000, step=500)
st.info("Enter manual weights. Total must sum to 100%.")

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
    st.error(f"Total allocation is {total_alloc}%. Please adjust to 100%.")
    st.stop()

horizon_years = st.number_input("Investment Horizon (years)", min_value=0.1, max_value=30.0, value=1.0, step=0.1)

st.markdown("---")

# -------------------------------
# Headline Input
# -------------------------------
st.markdown("## 📰 Step 2: Enter a Market Headline")
headline = st.text_input("Paste headline to analyze...", placeholder="e.g., Gold prices hit all-time high")
analyze_button = st.button("🔍 Analyze Headline")

# -------------------------------
# Macro / Micro Classification
# -------------------------------
macro_themes = {
    "interest_rate": ["interest", "inflation", "cpi", "ppi", "fed", "ecb", "rate hike", "yields"],
    "energy": ["oil", "gas", "opec", "energy supply", "pipeline", "crude"],
    "tech": ["ai", "technology", "chip", "semiconductor", "software"],
    "geopolitical": ["conflict", "war", "border", "sanction", "missile", "tension"],
    "fiscal": ["stimulus", "government spending", "budget", "subsidy"],
    "currency": ["forex", "currency", "yen", "yuan", "dollar index"],
    "labor": ["unemployment", "jobs", "wage", "labor market"],
    "crypto": ["bitcoin", "crypto", "ethereum", "token", "blockchain"],
    "political_shock": ["assassination", "prime minister", "president", "resignation", "leader death"]
}

micro_themes = {
    "earnings": ["earnings", "quarterly", "revenue", "profit", "guidance"],
    "company_specific": ["launch", "ceo", "merger", "acquisition", "company"],
    "sector_only": ["retail sales", "chip demand", "housing data"]
}

irrelevant_keywords = ["accident", "celebrity", "movie", "festival", "sports", "award", "weather", "crime"]

# Severity multiplier table
severity_weights = {
    "crisis": 1.5, "war": 1.5, "sanction": 1.3, "default": 1.5,
    "surge": 1.2, "collapse": 1.2, "emergency": 1.2,
    "hike": 1.1, "cut": 1.1, "inflation": 1.1,
    "mild": 1.0, "slight": 1.0
}

def classify_news(text):
    text_lower = text.lower()
    for w in irrelevant_keywords:
        if w in text_lower:
            return "irrelevant", "Local / Irrelevant News"
    for key, words in micro_themes.items():
        if any(w in text_lower for w in words):
            return "micro", key
    for key, words in macro_themes.items():
        if any(w in text_lower for w in words):
            return "macro", key
    return "irrelevant", "No macro/micro signals detected"

def compute_impact_score(text):
    score = 0
    for word, mult in severity_weights.items():
        if word in text.lower():
            score += 20 * (mult - 1 + 1)  # base 20 * multiplier
    return min(max(score, 20), 100)  # ensure minimum 20 for demo

def horizon_threshold(event_score, horizon_years):
    if horizon_years <= 1:
        return event_score >= 20
    elif horizon_years <= 3:
        return event_score >= 40
    else:
        return event_score >= 70

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

def apply_rebalance(base_weights, theme, intensity_factor):
    new_weights = base_weights.copy()
    if theme not in macro_rebalance_rules:
        return new_weights
    for asset, change in macro_rebalance_rules[theme].items():
        if asset in new_weights:
            new_weights[asset] += change * intensity_factor
    # normalize to sum to 100
    total = sum(new_weights.values())
    for k in new_weights:
        new_weights[k] = round(new_weights[k] / total * 100, 2)
    return new_weights

# -------------------------------
# Output / UI Logic
# -------------------------------
if analyze_button and headline:
    event_type, theme = classify_news(headline)
    impact_score = compute_impact_score(headline)
    st.markdown("## 🧠 Analysis Result")
    st.write(f"**Event Type:** `{event_type.upper()}`")
    st.write(f"**Detected Theme:** `{theme}`")
    st.write(f"**Impact Score:** `{impact_score}/100`")
    
    if event_type == "irrelevant":
        st.warning("This event is not market-relevant. No portfolio change recommended.")
        st.stop()
    if event_type == "micro":
        st.info("Micro-level event detected. For demo, minor rebalancing rules may apply.")
    
    if not horizon_threshold(impact_score, horizon_years):
        st.info("Event severity is below horizon-aware threshold. No rebalance needed.")
        st.stop()
    
    st.markdown("## 🔄 Suggested Portfolio Rebalance")
    intensity_factor = impact_score / 100
    updated_portfolio = apply_rebalance(initial_weights, theme, intensity_factor)
    
    # Display bar charts
    st.bar_chart(pd.DataFrame({
        "Current Portfolio": pd.Series(initial_weights),
        "Suggested Portfolio": pd.Series(updated_portfolio)
    }))
    
    col1, col2 = st.columns(2)
    if col1.button("📩 Send Alert (Simulated)"):
        st.info("Alert sent to user (simulated).")
    if col2.button("✔ Approve Rebalance (Demo Only)"):
        st.success("Rebalance approved and applied (simulated).")

st.markdown("---")
st.caption("MacroMoney Demo v2.4 — Not financial advice. For research/testing only.")





