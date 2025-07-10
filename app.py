import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv("zip_code_demographics3.csv", dtype={'zip': str})
    return df

df = load_data()

# Muse Score Calculation (standardization function)
def normalize(series):
    return 100 * (series - series.min()) / (series.max() - series.min())

# Main App
st.title("📍 Muse Score Calculator")

# User input
zip_code = st.text_input("Enter your ZIP code:", "")
agi = st.number_input("Enter your Adjusted Gross Income (AGI):", min_value=1000, step=1000, value=50000)

if st.button("Calculate Muse Score"):
    if zip_code in df['zip'].values:
        user_row = df[df['zip'] == zip_code].iloc[0]

        # Factors normalization
        CLF = normalize(df['COLI']).loc[user_row.name]
        TRF = normalize(df['TRF']).loc[user_row.name]
        TTIF = normalize(df['PCPI']).loc[user_row.name]
        PTF = normalize(df['PTR']).loc[user_row.name]
        SITF = normalize(df['TR']).loc[user_row.name]
        RSF = normalize(df['RSF']).loc[user_row.name]
        ISF = normalize(df['Savings']).loc[user_row.name]
        DDF = 50  # placeholder as data is missing

        muse_score = (
            0.20 * CLF +
            0.20 * TRF +
            0.15 * TTIF +
            0.15 * PTF +
            0.15 * SITF +
            0.05 * DDF +
            0.05 * RSF +
            0.05 * ISF
        )

        # Scale Muse Score to 300-850
        muse_score_scaled = 300 + (muse_score * 550 / 100)

        # Gauge Chart for Muse Score
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

        # Show summary
        st.subheader(f"📋 Summary for ZIP: {zip_code} - {user_row.city}, {user_row.state_id}")
        st.markdown(f"""
        - **Cost of Living Index (COLI):** {user_row.COLI}
        - **Tax Rate Factor (TRF):** {user_row.TRF}%
        - **Total Taxable Income (PCPI):** ${user_row.PCPI}
        - **Property Tax Rate (PTR):** {user_row.PTR}%
        - **State Income Tax Rate (TR):** {user_row.TR}%
        - **Retirement Savings Factor (RSF):** {user_row.RSF}
        - **Investment Savings:** ${user_row.Savings}
        - **Population:** {user_row.population}
        - **Population Density:** {user_row.density} people/km²
        """)
        
        # Professional financial comment
        if muse_score_scaled < 550:
            comment = "🔴 Your financial situation indicates significant stress. Consider immediate cost management."
        elif muse_score_scaled < 700:
            comment = "🟠 Your financial situation is somewhat at risk. You may benefit from better financial planning."
        elif muse_score_scaled < 800:
            comment = "🟡 You're in good financial shape. Optimize further with tax planning."
        else:
            comment = "🟢 Excellent financial health! Continue strategic investment and tax planning."

        st.info(comment)

    else:
        st.error("ZIP code not found. Please check your input.")
