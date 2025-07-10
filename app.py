import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- Load Data ---
@st.cache_data
def load_data():
    df = pd.read_excel("zip_code_demographics3.xlsx", dtype={'zip': str}, engine='openpyxl')
    numeric_cols = ['COLI', 'TRF', 'PCPI', 'PTR', 'TR', 'RSF', 'Savings']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df.dropna(subset=numeric_cols, inplace=True)
    return df

df = load_data()

# --- Normalization Utilities ---
def normalize(series):
    return 100 * (series - series.min()) / (series.max() - series.min())

def inverse_normalize(series):
    return 100 * (series.max() - series) / (series.max() - series.min())

# --- Base Score from AGI vs PCPI ---
def base_score_from_agi(agi, pcpi):
    agi = min(agi, 1_000_000)  # cap at $1M
    ratio = agi / pcpi

    if ratio < 0.8:
        return 400, "🔴 Financial Stress"
    elif ratio < 1.0:
        return 500, "🟠 At Risk"
    elif ratio < 1.2:
        return 600, "🟡 Stable"
    elif ratio < 1.5:
        return 700, "🟢 Good"
    elif ratio < 2.0:
        return 800, "🟢 Excellent"
    else:
        return 850, "🟢 Top Performer"

# --- Streamlit UI ---
st.title("📍 Muse Score Calculator (AGI-Driven)")

zip_code = st.text_input("Enter your ZIP code:", "")
agi = st.number_input("Enter your Adjusted Gross Income (AGI)", min_value=1000, max_value=1_000_000, step=1000, value=50000)

if st.button("Calculate Muse Score"):
    if zip_code in df['zip'].values:
        row = df[df['zip'] == zip_code].iloc[0]

        # Normalize factors
        COLI = inverse_normalize(df['COLI']).loc[row.name]
        TRF = inverse_normalize(df['TRF']).loc[row.name]
        PTR = inverse_normalize(df['PTR']).loc[row.name]
        SITF = inverse_normalize(df['TR']).loc[row.name]
        RSF = normalize(df['RSF']).loc[row.name]
        ISF = normalize(df['Savings']).loc[row.name]

        # AGI anchor score
        base_score, status = base_score_from_agi(agi, row['PCPI'])

        # Fine-tuned adjustment (max ±50)
        adjustment = (
            15 * (COLI / 100) +
            10 * (TRF / 100) +
            10 * (PTR / 100) +
            10 * (SITF / 100) +
            5 * (RSF / 100) +
            5 * (ISF / 100)
        )

        final_score = min(850, round(base_score + adjustment))

        # --- Gauge Chart ---
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=final_score,
            title={'text': f"Muse Score"},
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
                    'value': final_score
                }
            }
        ))

        st.plotly_chart(fig, use_container_width=True)

        # --- Summary Info ---
        st.subheader(f"📋 Summary for ZIP: {zip_code} — {row.city}, {row.state_id}")
        st.markdown(f"""
        - **Your AGI:** ${agi:,.0f}
        - **Local Avg Income (PCPI):** ${row.PCPI:,.0f}
        - **AGI Status:** {status}
        - **Cost of Living Index (COLI):** {row.COLI}
        - **Tax Rate Factor (TRF):** {row.TRF}%
        - **Property Tax Rate (PTR):** {row.PTR}%
        - **State Income Tax Rate (TR):** {row.TR}%
        - **Retirement Savings Factor (RSF):** {row.RSF}
        - **Investment Savings:** ${row.Savings:,.0f}
        - **Population:** {row.population}
        - **Population Density:** {row.density} people/km²
        """)

    else:
        st.error("ZIP code not found. Please verify your input.")
