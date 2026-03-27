import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
import os

# --- STEP 0: PAGE CONFIGURATION ---
st.set_page_config(page_title="BFSI Labor Insights AI", layout="wide", page_icon="📈")

# --- STEP 1: INITIALIZE AI MODEL ---
# Replace 'YOUR_API_KEY' with your actual Google API Key or use secrets
# For local testing: os.getenv("GOOGLE_API_KEY")
google_api_key = st.sidebar.text_input("AIzaSyBcD8EwNxIC_88I_rVCCd9JZ7aGkQ6-QOc", type="password")

if google_api_key:
    genai.configure(api_key=google_api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.warning("Please enter your Google API Key in the sidebar to enable AI Reporting.")

# --- STEP 2: LOAD & NORMALIZE DATA ---
@st.cache_data
def load_data():
    try:
        data = pd.read_csv("occupazione.csv")
        # Clean column names
        data.columns = data.columns.str.strip().str.lower()
        
        # MAPPING: Matches your specific CSV columns
        column_mapping = {
            'country_col': 'country' if 'country' in data.columns else 'ref_area',
            'year_col': 'year' if 'year' in data.columns else 'time',
            'value_col': 'obs_value',
            'sex_col': 'sex' if 'sex' in data.columns else None
        }
        return data, column_mapping
    except Exception as e:
        st.error(f"Error loading CSV: {e}")
        return pd.DataFrame(), {}

df, mapping = load_data()

if not df.empty:
    # --- STEP 3: SIDEBAR & FILTERS ---
    st.title("🌍 BFSI Labor Insights & Strategic AI")
    st.sidebar.header("Filter Data")

    available_countries = sorted(df[mapping['country_col']].unique())
    selected_country = st.sidebar.selectbox("Select a Country", available_countries)

    if mapping['sex_col']:
        available_genders = df[mapping['sex_col']].unique().tolist()
        selected_sex = st.sidebar.radio("Select Gender", available_genders)
        filtered_df = df[(df[mapping['country_col']] == selected_country) & (df[mapping['sex_col']] == selected_sex)]
    else:
        filtered_df = df[df[mapping['country_col']] == selected_country]

    # Sort for consistent visuals
    filtered_df = filtered_df.sort_values(by=mapping['year_col'])

    # --- STEP 4: VISUALS ---
    st.subheader(f"Trend Analysis: {selected_country}")
    fig = px.line(filtered_df, 
                  x=mapping['year_col'], 
                  y=mapping['value_col'], 
                  markers=True,
                  title=f"Employment Rate Over Time: {selected_country}")
    st.plotly_chart(fig, use_container_width=True)

    # --- STEP 5: STRATEGIC REPORTING ENGINE ---
    st.markdown("---")
    st.subheader("📑 Automated Strategic Reporting")

    if st.button("🚀 Generate Executive Summary"):
        if not google_api_key:
            st.error("AI Model not initialized. Please provide an API Key in the sidebar.")
        else:
            try:
                with st.spinner(f"Agentic AI is analyzing {selected_country}..."):
                    y_col = mapping['year_col']
                    v_col = mapping['value_col']
                    
                    latest_year = filtered_df[y_col].max()
                    latest_val = filtered_df[filtered_df[y_col] == latest_year][v_col].iloc[0]
                    avg_val = filtered_df[v_col].mean()
                    
                    report_prompt = f"""
                    Act as a Senior BFSI Strategy Consultant. 
                    Analyze the following data for {selected_country}:
                    - Metric: Employment Rate
                    - Latest Year ({latest_year}) Value: {latest_val:.2f}%
                    - Historical Average: {avg_val:.2f}%
                    
                    Write a professional 3-point Executive Summary:
                    1. TREND ANALYSIS: Trajectory based on these numbers.
                    2. BENCHMARKING: Performance vs historical average.
                    3. STRATEGIC RECOMMENDATION: CEO focus for the next 12 months.
                    Format: Professional headings and bullet points. Under 200 words.
                    """
                    
                    response = model.generate_content(report_prompt)
                    st.success("Report Generated!")
                    st.markdown(f"### 📄 Executive Report: {selected_country}")
                    st.write(response.text)
                    
                    st.download_button("📥 Download Report", response.text, file_name=f"Report_{selected_country}.txt")
            except Exception as e:
                st.error(f"AI Error: {e}")

    # --- STEP 6: EXECUTIVE METRICS ---
    st.divider()
    m1, m2, m3 = st.columns(3)
    
    max_val = filtered_df[mapping['value_col']].max()
    min_val = filtered_df[mapping['value_col']].min()
    latest_rate = filtered_df[mapping['value_col']].iloc[-1]
    prev_rate = filtered_df[mapping['value_col']].iloc[-2] if len(filtered_df) > 1 else latest_rate
    
    m1.metric("All-Time High", f"{max_val}%")
    m2.metric("All-Time Low", f"{min_val}%")
    m3.metric("Latest Change", f"{latest_rate}%", f"{latest_rate - prev_rate:.2f}%")

else:
    st.error("Could not initialize the application. Check your CSV file.")