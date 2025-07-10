import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Load Excel
@st.cache_data
def load_data():
    df = pd.read_excel("zip_code_demographics3.xlsx", dtype={'zip': str}, engine='openpyxl')
    numeric_cols = ['COLI', 'TRF', 'PCPI', 'PTR', 'TR', 'RSF', 'Savings']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df.dropna(subset=numeric_cols, inplace=True)
    return df

df = load_data()

# Normalize function (0–100)
def normalize(series):
    return 100 * (series - series.min()) / (series.max() - series.min())

def inverse_normalize(series):
    return 100 * (series.max() - series) / (series.max() - series.min())

# AGI to Muse Score baseline
def get_agi_base_score(agi, pcpi):
    ratio = min(agi / pcpi, 2.0)  # cap ratio at 2.0
    if ratio < 0.5:
        return 350
    elif ratio < 0.8:
        return 500
    elif ratio < 1.0:
        return 650
    elif ratio < 1.2:
        return 725
    elif ratio < 1.5:
        return 775
    else:
        return 800

# Main App
st.title("📍 Muse Score Calculator (AGI-Driven)")

zip_code = st.text_input("Enter your ZIP code:", "")
agi = st.number_input("Enter your Adjusted Gross Income (AGI):", min_value=1000, max_value=1_000_000, step=1000, value=50000)

if st.button("Calculate Muse Score"):
    if zip_code in df['zip'].values:
        user_row = df[df['zip'] == zip_code].iloc[0]

        # Baseline from AGI/PCPI ratio
        base_score = get_agi_base_score(agi, user_row['PCPI'])

        # Adjustment factors (normalized properly)
        CLF_adj = inverse_normalize(df['COLI']).loc[user_row.name] / 100 * 10
        TRF_adj = inverse_normalize(df['TRF']).loc[user_row.name] / 100 * 10
        PTR_adj = inverse_normalize(df['PTR']).loc[user_row.name] / 100 * 5
        SITF_adj = inverse_normalize(df['TR']).loc[user_row.name] / 100 * 5
        RSF_adj = normalize(df['RSF']).loc[user_row.name] / 100 * 10
        ISF_adj = normalize(df['Savings']).loc[user_row.name] / 100 * 10

        adjustment = CLF_adj + TRF_adj + PTR_adj + SITF_adj + RSF_adj + ISF_adj
        muse_score = min(base_score + adjustment, 850)

        # Gauge
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=muse_score,
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
                    'value': muse_score
                }
            }
        ))

        st.plotly_chart(fig, use_container_width=True)

        # Summary
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
        """)

        # Interpretation
        ratio = agi / user_row['PCPI']
        if ratio < 0.8:
            st.warning("🟠 Your income is below the local average. Consider areas with lower living costs.")
        elif ratio < 1.2:
            st.info("🟡 You're well-aligned with the local economy.")
        else:
            st.success("🟢 You're earning well above the local average. Strong financial resilience expected.")

    else:
        st.error("ZIP code not found. Please check your input.")
