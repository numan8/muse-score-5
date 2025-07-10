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

# --- Normalization Functions ---
def normalize(series):
    return 100 * (series - series.min()) / (series.max() - series.min())

def inverse_normalize(series):
    return 100 * (series.max() - series) / (series.max() - series.min())

def normalize_agi_ratio(user_agi, local_pcpi):
    ratio = user_agi / local_pcpi
    ratio = min(max(ratio, 0.5), 2.0)  # clamp between 0.5 and 2.0
    return (ratio - 0.5) / 1.5 * 100   # normalize to 0–100 scale

# --- Streamlit UI ---
st.title("📍 Muse Score Calculator")

zip_code = st.text_input("Enter your ZIP code:", "")
agi = st.number_input("Enter your Adjusted Gross Income (AGI):", min_value=1000, step=1000, value=50000)

if st.button("Calculate Muse Score"):
    if zip_code in df['zip'].values:
        user_row = df[df['zip'] == zip_code].iloc[0]

        # Normalize all factors
        CLF = inverse_normalize(df['COLI']).loc[user_row.name]
        TRF = inverse_normalize(df['TRF']).loc[user_row.name]
        PTR = inverse_normalize(df['PTR']).loc[user_row.name]
        SITF = inverse_normalize(df['TR']).loc[user_row.name]
        RSF = normalize(df['RSF']).loc[user_row.name]
        ISF = normalize(df['Savings']).loc[user_row.name]
        AGI_norm = normalize_agi_ratio(agi, user_row['PCPI'])

        # Weighted Muse Score
        muse_score_raw = (
            0.15 * CLF +
            0.15 * TRF +
            0.10 * PTR +
            0.10 * SITF +
            0.30 * AGI_norm +
            0.10 * RSF +
            0.10 * ISF
        )

        # Scale to 300–850
        muse_score_scaled = 300 + (muse_score_raw * 550 / 100)
        muse_score_scaled = min(max(muse_score_scaled, 300), 850)

        # --- Gauge Chart ---
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

        # --- Summary Info ---
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

        # --- AGI vs PCPI Commentary ---
        agi_ratio = agi / user_row['PCPI']
        if agi_ratio < 0.8:
            comment = "🔴 Your AGI is significantly below the local average. Financial stress is likely in this area."
        elif agi_ratio < 1.0:
            comment = "🟠 Your AGI is slightly below the local average. You may need to manage expenses carefully."
        elif agi_ratio < 1.2:
            comment = "🟡 Your AGI is well-aligned with the local average. Stable financial condition expected."
        else:
            comment = "🟢 Your AGI is significantly above the local average. You are financially well-positioned."

        st.info(comment)

    else:
        st.error("ZIP code not found. Please verify your input.")
