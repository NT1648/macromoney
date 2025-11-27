
import streamlit as st
import numpy as np
import pandas as pd

st.set_page_config(page_title="MacroMoney v0.1", layout="wide")

st.title("💼 MacroMoney v0.1 — Macro-Aware AI Portfolio Demo")
st.write("A minimal, professional demo of your AI-driven investment assistant.")

st.sidebar.header("User Settings")

capital = st.sidebar.number_input(
    "Total Capital ($)", min_value=1000, max_value=10000000, value=10000, step=500
)

risk_tolerance = st.sidebar.selectbox(
    "Risk Tolerance", ["Low", "Medium", "High"]
)

allowed_assets = st.sidebar.multiselect(
    "Allowed Asset Classes",
    ["Equities (SPY)", "Bonds (IEF)", "Crypto (BTC)",
     "ETF (QQQ)", "Options (SPY-Option)", "Futures (ES)", "Commodities (GLD)"],
    default=["Equities (SPY)", "Bonds (IEF)", "Crypto (BTC)",
             "ETF (QQQ)", "Commodities (GLD)"]
)

st.sidebar.write("---")
st.sidebar.write("Mode: **Advisory Only** (no auto-trading)")

asset_mapping = {
    "Equities (SPY)": "SPY",
    "Bonds (IEF)": "IEF",
    "Crypto (BTC)": "BTC",
    "ETF (QQQ)": "QQQ",
    "Options (SPY-Option)": "SPY_Option",
    "Futures (ES)": "ES",
    "Commodities (GLD)": "GLD",
}

instruments = [asset_mapping[a] for a in allowed_assets]

def create_equal_weight_portfolio(assets, capital):
    n = len(assets)
    weight = 1 / n
    df = pd.DataFrame({
        "Asset": assets,
        "Weight": [weight] * n,
        "Allocation ($)": [capital * weight] * n
    })
    return df

current_portfolio = create_equal_weight_portfolio(instruments, capital)

def simulate_macro_cluster(text):
    keywords = {
        0: ["inflation", "prices", "cpi", "pmi"],
        1: ["oil", "energy", "gas", "opec"],
        2: ["war", "conflict", "geopolitics", "sanctions"],
        3: ["tech", "ai", "chips", "innovation"],
        4: ["dollar", "currency", "forex", "fed"],
        5: ["recession", "slowdown", "unemployment"],
        6: ["crypto", "bitcoin", "blockchain"],
        7: ["rates", "hikes", "treasury", "yields"],
    }

    text = text.lower()

    for cluster_id, words in keywords.items():
        if any(w in text for w in words):
            return cluster_id

    return np.random.randint(0, 8)

cluster_names = {
    0: "Inflation / Price Pressure",
    1: "Energy Supply / Oil Shock",
    2: "Geopolitical Tension",
    3: "Tech Growth / Innovation",
    4: "USD / Currency Shifts",
    5: "Economic Slowdown",
    6: "Crypto Market Pressure",
    7: "Interest Rate / Yield Pressure",
}

def create_sensitivity_matrix():
    return {
        "SPY":      [ -1, -1, -1, +1, -1, -1,  0, -1 ],
        "IEF":      [ -1,  0, +1, -1, +1, +1,  0, +1 ],
        "BTC":      [  0, -1, -1, +1, -1, -1, -1, -1 ],
        "QQQ":      [ -1,  0, -1, +1, -1, -1,  0, -1 ],
        "SPY_Option":[+1, -1, -1, +1, -1, -1, +1, -1 ],
        "ES":       [ -1, -1, -1, +1, -1, -1,  0, -1 ],
        "GLD":      [ +1, +1, +1, -1, +1, +1,  0, +1 ],
    }

sensitivity = create_sensitivity_matrix()

def generate_suggested_portfolio(cluster_id, df):
    df = df.copy()
    effect_strength = 0.03

    for i, row in df.iterrows():
        asset = row["Asset"]
        if asset in sensitivity:
            direction = sensitivity[asset][cluster_id]
            df.at[i, "Weight"] += direction * effect_strength

    df["Weight"] = df["Weight"].clip(lower=0)
    df["Weight"] = df["Weight"] / df["Weight"].sum()

    df["Allocation ($)"] = df["Weight"] * capital

    return df

col1, col2 = st.columns(2)

col1.subheader("📊 Current Portfolio (Equal Weight)")
col1.dataframe(current_portfolio)

col2.subheader("📰 Macro Signal Input (Demo Only)")
headline = col2.text_area("Paste a news headline or tweet:")

if headline:
    cluster_id = simulate_macro_cluster(headline)
    theme = cluster_names[cluster_id]

    st.write("---")
    st.subheader("🧠 MacroMoney Interpretation")
    st.write(f"**Detected Theme:** {theme}")
    st.write(f"**Cluster ID:** {cluster_id}")

    suggested = generate_suggested_portfolio(cluster_id, current_portfolio)

    st.write("---")
    st.subheader("📈 Suggested Rebalance")
    st.dataframe(suggested)

    st.success("This suggestion is generated using rule-based macro sensitivity.")

    colA, colB = st.columns(2)
    if colA.button("📩 Send Alert (Simulated)"):
        st.info("Alert sent to user (simulated).")

    if colB.button("✔ Approve Rebalance (Demo Only)"):
        st.success("Rebalance approved and applied (simulated).")
else:
    st.info("Enter a news headline to generate macro interpretation.")
