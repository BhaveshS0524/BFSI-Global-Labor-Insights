import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai

# --- STEP 0: CONFIGURATION & SECRETS ---
st.set_page_config(page_title="BFSI Labor Insights AI", layout="wide", page_icon="📈")

# Securely load the API Key from Streamlit Secrets
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # Using the updated 2026 production model
    model = genai.GenerativeModel('gemini-2.5-flash') 
else:
    st.error("Missing API Key in Secrets. Please add 'GOOGLE_API_KEY' to your Streamlit Cloud settings.")
    st.stop()

# --- STEP 1: LOAD DATA ---
@st.cache_data
def load_data():
    data = pd.read_csv("occupazione.csv")
    data.columns = data.columns.str.strip().str.lower()
    return data

df = load_data()

# --- STEP 2: RESTORED SIDEBAR FILTERS ---
st.sidebar.header("📊 Filter Analytics")

# Country Filter
countries = sorted(df['country'].unique())
selected_country = st.sidebar.selectbox("Select Country", countries)

# Gender/Sex Filter (Restored)
if 'sex' in df.columns:
    genders = df['sex'].unique().tolist()
    selected_sex = st.sidebar.radio("Select Gender Profile", genders)
    filtered_df = df[(df['country'] == selected_country) & (df['sex'] == selected_sex)]
else:
    filtered_df = df[df['country'] == selected_country]

# Sort by year for clean line charts
filtered_df = filtered_df.sort_values(by='year')

# --- STEP 3: MAIN DASHBOARD ---
st.title("🌍 BFSI Global Labor Insights")
st.markdown(f"**Currently Analyzing:** {selected_country} | **Profile:** {selected_sex if 'sex' in df.columns else 'All'}")

# Plotly Chart
fig = px.line(filtered_df, x='year', y='obs_value', markers=True,
              title=f"Employment Trend: {selected_country}")
st.plotly_chart(fig, use_container_width=True)

# --- STEP 4: STRATEGIC REPORTING (AI) ---
st.divider()
if st.button("🚀 Generate AI Executive Summary"):
    with st.spinner("Agentic AI is synthesizing data..."):
        try:
            latest_yr = filtered_df['year'].max()
            latest_val = filtered_df[filtered_df['year'] == latest_yr]['obs_value'].iloc[0]
            avg_val = filtered_df['obs_value'].mean()

            prompt = f"Act as a BFSI Consultant. Analyze {selected_country} data: Latest ({latest_yr}) is {latest_val:.2f}%, Avg is {avg_val:.2f}%. Give a 3-point strategic report."
            
            response = model.generate_content(prompt)
            st.markdown(f"### 📄 Strategic Report: {selected_country}")
            st.write(response.text)
        except Exception as e:
            st.error(f"AI Generation Error: {e}")

# --- STEP 5: METRICS ROW ---
col1, col2, col3 = st.columns(3)
col1.metric("Max Rate", f"{filtered_df['obs_value'].max()}%")
col2.metric("Min Rate", f"{filtered_df['obs_value'].min()}%")
col3.metric("Avg Rate", f"{filtered_df['obs_value'].mean():.2f}%")

# --- Updated Sidebar Test UI ---
st.sidebar.divider()
st.sidebar.subheader("🤖 Agent Tool Test (v2.0)")
st.sidebar.caption("Type in lowercase (e.g. 'india') to test normalization.")

test_input = st.sidebar.text_input("Country Search:", value="india")
test_yr = st.sidebar.number_input("Year Search:", min_value=1991, max_value=2025, value=2021)

if st.sidebar.button("Run Advanced Tool"):
    response = get_employment_stats(test_input, test_yr)
    if response["status"] == "success":
        st.sidebar.success(response["message"])
    else:
        st.sidebar.warning(response["message"])

# 6. Show Raw Data
if st.checkbox("Show Raw Data Table"):
    st.write(filtered_df)

# Sidebar Footer
st.sidebar.markdown("---")
st.sidebar.markdown("### 👨‍💼 Bhavesh Suryavanshi")
st.sidebar.markdown("*AI Solutions Architect | Data Strategist*")
