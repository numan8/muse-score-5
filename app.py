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

# --- AGI to PCPI Ratio → Base Score & Label ---
def base_score_from_agi(agi, pcpi):
    agi = min(agi, 1_000_000)  # cap AGI at $1M
    ratio = agi / pcpi

    if ratio < 0.6:
        return 350, "🔴 Critical Financial Stress"
    elif ratio < 0.7:
        return 400, "🔴 Severe Stress"
    elif ratio < 0.8:
        return 450, "🔴 Financial Stress"
    elif ratio < 0.9:
        return 500, "🟠 At Risk"
    elif ratio < 1.0:
        return 550, "🟠 Near Average"
    elif ratio < 1.2:
        return 600, "🟡 Stable"
    elif ratio < 1.5:
        return 675, "🟢 Good"
    elif ratio < 2.0:
        return 750, "🟢 Very Good"
    elif ratio < 2.5:
        return 800, "🟢 Excellent"
    else:
        return 850, "🟢 Top Performer (Cap)"

# --- Streamlit Layout ---
st.set_page_config(page_title="Muse Score Calculator", layout="centered")
st.title("📊 Muse Score Calculator")

st.markdown("Get a personalized financial wellness score based on your AGI and your area's economic profile.")

with st.container():
    col1, col2 = st.columns(2)
    with col1:
        zip_code = st.text_input("📍 Enter ZIP Code", max_chars=10)
    with col2:
        agi = st.number_input("💰 Enter Your AGI", min_value=1000, max_value=1_000_000, step=1000, value=50000)

st.markdown("---")

if st.button("📈 Calculate Muse Score"):
    if zip_code in df['zip'].values:
        row = df[df['zip'] == zip_code].iloc[0]

        # Normalize factors
        COLI = inverse_normalize(df['COLI']).loc[row.name]
        TRF = inverse_normalize(df['TRF']).loc[row.name]
        PTR = inverse_normalize(df['PTR']).loc[row.name]
        SITF = inverse_normalize(df['TR']).loc[row.name]
        RSF = normalize(df['RSF']).loc[row.name]
        ISF = normalize(df['Savings']).loc[row.name]

        # Muse Score calculation
        base_score, status = base_score_from_agi(agi, row['PCPI'])
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

        # --- Summary Output UI ---
        st.markdown("### 📋 Results Summary")
        with st.container():
            st.markdown(f"""
            <div style="background-color: #f9f9f9; padding: 20px; border-radius: 10px;">
                <strong>ZIP Code:</strong> {zip_code}<br>
                <strong>City:</strong> {row.city}<br>
                <strong>State:</strong> {row.state_id}<br>
                <strong>Your AGI:</strong> ${agi:,.0f}<br>
                <strong>AGI Status:</strong> {status}<br>
                <strong>Local Avg Income (PCPI):</strong> ${row.PCPI:,.0f}<br>
                <strong>Cost of Living Index (COLI):</strong> {row.COLI}
            </div>
            """, unsafe_allow_html=True)

    else:
        st.error("❌ ZIP code not found in dataset. Please try another.")
