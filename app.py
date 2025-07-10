import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- Load Excel Data ---
@st.cache_data
def load_data():
    df = pd.read_excel("zip_code_demographics3.xlsx", dtype={'zip': str}, engine='openpyxl')
    numeric_cols = ['COLI', 'TRF', 'PCPI', 'PTR', 'TR', 'RSF', 'Savings']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df.dropna(subset=numeric_cols, inplace=True)
    return df

df = load_data()

# --- Normalization Function ---
def normalize(series):
    return 100 * (series - series.min()) / (series.max() - series.min())

# --- Additive AGI Adjustment Function ---
def agi_additive_adjustment(user_agi, local_pcpi):
    ratio = user_agi / local_pcpi
    ratio = min(max(ratio, 0.5), 2.0)  # Clamp ratio between 0.5 and 2.0
    adjustment = (ratio - 1) * 20  # -10 to +20
    return adjustment

# --- Streamlit UI ---
st.title("📍 Muse Score Calculator")

zip_code = st.text_input("Enter your ZIP code:", "")
agi = st.number_input("Enter your Adjusted Gross Income (AGI):", min_value=1000, step=1000, value=50000)

if st.button("Calculate Muse Score"):
    if zip_code in df['zip'].values:
        user_row = df[df['zip'] == zip_code].iloc[0]

        # Normalize Factors
        CLF = normalize(df['COLI']).loc[user_row.name]
        TRF = normalize(df['TRF']).loc[user_row.name]
        TTIF = normalize(df['PCPI']).loc[user_row.name]
        PTF = normalize(df['PTR']).loc[user_row.name]
        SITF = normalize(df['TR']).loc[user_row.name]
        RSF = normalize(df['RSF']).loc[user_row.name]
        ISF = normalize(df['Savings']).loc[user_row.name]
        DDF = 50  # Placeholder

        # AGI Adjustment (additive effect)
        agi_adj = agi_additive_adjustment(agi, user_row['PCPI'])

        # Base Muse Score (0–100 scale)
        base_score = (
            0.20 * CLF +
            0.20 * TRF +
            0.15 * TTIF +
            0.15 * PTF +
            0.15 * SITF +
            0.05 * DDF +
            0.05 * RSF +
            0.05 * ISF
        )

        # Final Muse Score scaled to 300–850 with AGI adjustment
        muse_score_scaled = 300 + ((base_score + agi_adj) * 550 / 100)
        muse_score_scaled = min(max(muse_score_scaled, 300), 850)

        # Gauge Chart
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=muse_score_scaled,
            title={'text': "Muse Score"},
            gauge={
                'axis': {'range': [300, 850]},
                'steps': [
                    {'range': [300, 550], 'color': "red"},
                    {'range': [550, 700], 'color': "orange"},
                    {'range': [700, 800], 'color': "yellow"},
                    {'range': [800, 850], 'color': "green"},
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 4},
                    'thickness': 0.75,
                    'value': muse_score_scaled
                }
            }
        ))

        st.plotly_chart(fig, use_container_width=True)

        # Summary of Data
        st.subheader(f"📋 Summary for ZIP: {zip_code} — {user_row.city}, {user_row.state_id}")
        st.markdown(f"""
        - **Your AGI:** ${agi:,.0f}
        - **Local Avg Income (PCPI):** ${user_row.PCPI:,.0f}
        - **Cost of Living Index (COLI):** {user_row.COLI}
        - **Tax Rate Factor (TRF):** {user_row.TRF}%
        - **Property Tax Rate (PTR):** {user_row.PTR}%
        - **State Income Tax Rate (TR):** {user_row.TR}%
        - **Retirement Savings Factor (RSF):** {user_row.RSF}
        - **Investment Savings:** ${user_row.Savings:,.0f}
        - **Population:** {user_row.population}
        - **Population Density:** {user_row.density} people/km²
        """)

        # Interpretation Message
        if muse_score_scaled < 550:
            comment = "🔴 Your AGI is well below local average. Significant financial stress expected in this area."
        elif muse_score_scaled < 700:
            comment = "🟠 Your AGI is below average. Financial risk exists. Boost income or reduce expenses."
        elif muse_score_scaled < 800:
            comment = "🟡 Your AGI aligns with local averages. You're in a good position. Stay financially disciplined."
        else:
            comment = "🟢 Excellent! Your AGI is well above local norms. Strong financial resilience."

        st.info(comment)

    else:
        st.error("ZIP code not found. Please verify your input.")
