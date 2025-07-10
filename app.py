import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Load Excel data
@st.cache_data
def load_data():
    df = pd.read_excel("zip_code_demographics3.xlsx", dtype={'zip': str}, engine='openpyxl')
    numeric_cols = ['COLI', 'TRF', 'PCPI', 'PTR', 'TR', 'RSF', 'Savings']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df.dropna(subset=numeric_cols, inplace=True)
    return df

df = load_data()

# Normalization function
def normalize(series):
    return 100 * (series - series.min()) / (series.max() - series.min())

# AGI factor (new function)
def agi_factor(user_agi, local_pcpi):
    ratio = user_agi / local_pcpi
    if ratio >= 1.5:
        return 100
    elif ratio >= 1.2:
        return 85
    elif ratio >= 1.0:
        return 70
    elif ratio >= 0.8:
        return 50
    elif ratio >= 0.5:
        return 30
    else:
        return 10

# App UI
st.title("📍 Muse Score Calculator")

zip_code = st.text_input("Enter your ZIP code:", "")
agi = st.number_input("Enter your Adjusted Gross Income (AGI):", min_value=1000, step=1000, value=50000)

if st.button("Calculate Muse Score"):
    if zip_code in df['zip'].values:
        user_row = df[df['zip'] == zip_code].iloc[0]

        # Normalized Factors
        CLF = normalize(df['COLI']).loc[user_row.name]
        TRF = normalize(df['TRF']).loc[user_row.name]
        TTIF = normalize(df['PCPI']).loc[user_row.name]
        PTF = normalize(df['PTR']).loc[user_row.name]
        SITF = normalize(df['TR']).loc[user_row.name]
        RSF = normalize(df['RSF']).loc[user_row.name]
        ISF = normalize(df['Savings']).loc[user_row.name]
        DDF = 50  # Placeholder

        # New AGI Factor (dynamic)
        AGIF = agi_factor(agi, user_row['PCPI'])

        # Adjusted Muse Score calculation including AGI factor
        muse_score = (
            0.15 * CLF +
            0.15 * TRF +
            0.15 * TTIF +
            0.15 * PTF +
            0.10 * SITF +
            0.10 * AGIF +  # AGI factor has 10% impact
            0.05 * DDF +
            0.05 * RSF +
            0.05 * ISF
        )

        muse_score_scaled = 300 + (muse_score * 550 / 100)

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
                    {'range': [800, 850], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 4},
                    'thickness': 0.75,
                    'value': muse_score_scaled
                }
            }
        ))

        st.plotly_chart(fig, use_container_width=True)

        st.subheader(f"📋 Summary for ZIP: {zip_code} - {user_row.city}, {user_row.state_id}")
        st.markdown(f"""
        - **Cost of Living Index (COLI):** {user_row.COLI}
        - **Tax Rate Factor (TRF):** {user_row.TRF}%
        - **Local Avg. Personal Income (PCPI):** ${user_row.PCPI}
        - **Your AGI:** ${agi}
        - **Property Tax Rate (PTR):** {user_row.PTR}%
        - **State Income Tax Rate (TR):** {user_row.TR}%
        - **Retirement Savings Factor (RSF):** {user_row.RSF}
        - **Investment Savings:** ${user_row.Savings}
        - **Population:** {user_row.population}
        - **Population Density:** {user_row.density} people/km²
        """)

        # Professional financial comment
        if muse_score_scaled < 550:
            comment = "🔴 Financial stress: Your AGI is significantly below your area's average. Consider budgeting and additional income strategies."
        elif muse_score_scaled < 700:
            comment = "🟠 At risk: Your AGI is slightly below the local average. Improving savings and optimizing expenses is recommended."
        elif muse_score_scaled < 800:
            comment = "🟡 Good shape: Your AGI aligns with the local average. Maintain financial discipline and explore additional optimization."
        else:
            comment = "🟢 Excellent financial position: Your AGI exceeds the local average significantly. You're in a strong position for advanced financial planning."

        st.info(comment)

    else:
        st.error("ZIP code not found. Please verify your input.")
