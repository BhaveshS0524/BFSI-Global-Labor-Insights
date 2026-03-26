import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai

# --- STEP 0: PAGE CONFIGURATION ---
st.set_page_config(page_title="Global Employment AI", layout="wide")

# --- STEP 1: AI SETUP (GEMINI) ---
# Using the most stable model naming convention
API_KEY = "AIzaSyALqZ9C5nEBBrKa8BP-aDwC-my3x3xUClI" 
genai.configure(api_key=API_KEY)

# SENIOR FIX: Changed from 'gemini-1.5-flash' to the most compatible version
model = genai.GenerativeModel('gemini-pro') 

# Alternative if 'gemini-pro' fails: 'models/gemini-1.5-flash-latest'
# --- STEP 2: LOAD & NORMALIZE DATA ---
@st.cache_data
def load_data():
    # Load the file
    data = pd.read_csv("occupazione.csv")
    
    # SENIOR FIX: Clean all column names (remove spaces and lowercase)
    data.columns = data.columns.str.strip().str.lower()
    
    # MAPPING: Automatically find the right columns
    column_mapping = {
        'country_col': 'ref_area' if 'ref_area' in data.columns else ('country' if 'country' in data.columns else data.columns[1]),
        'year_col': 'time' if 'time' in data.columns else ('year' if 'year' in data.columns else 'time'),
        'value_col': 'obs_value' if 'obs_value' in data.columns else 'obs_value',
        'sex_col': 'sex' if 'sex' in data.columns else ('gender' if 'gender' in data.columns else None)
    }
    
    # Clean the data itself
    data = data.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    
    return data, column_mapping

df, mapping = load_data()

# --- STEP 3: SIDEBAR PERSONA & FILTERS ---
st.sidebar.header("🤖 AI Agent Settings")
agent_role = st.sidebar.selectbox("Select Agent Persona", 
    ["BFSI Data Analyst", "Economic Researcher", "Global Labor Consultant"])

st.sidebar.divider()
st.sidebar.header("📊 Data Filters")
available_countries = sorted(df[mapping['country_col']].unique())
selected_country = st.sidebar.selectbox("Select a Country", available_countries)

# --- STEP 4: EXECUTIVE METRICS ---
st.title("🌍 Global Employment AI Explorer")
st.write(f"Analyzing data for **{selected_country}** through the lens of a **{agent_role}**.")

# Filter data for metrics
filtered_df = df[df[mapping['country_col']] == selected_country].sort_values(by=mapping['year_col'])

if not filtered_df.empty:
    st.divider()
    m_col1, m_col2, m_col3 = st.columns(3)
    
    max_val = filtered_df[mapping['value_col']].max()
    min_val = filtered_df[mapping['value_col']].min()
    latest_val = filtered_df[mapping['value_col']].iloc[-1]
    prev_val = filtered_df[mapping['value_col']].iloc[-2] if len(filtered_df) > 1 else latest_val
    delta = latest_val - prev_val

    with m_col1:
        st.metric(label="All-Time High", value=f"{max_val}%")
    with m_col2:
        st.metric(label="All-Time Low", value=f"{min_val}%")
    with m_col3:
        st.metric(label="Latest Change", value=f"{latest_val}%", delta=f"{delta:.2f}%")

    # --- STEP 5: VISUAL TREND ---
    fig = px.line(filtered_df, x=mapping['year_col'], y=mapping['value_col'], 
                  title=f"Employment Trend: {selected_country}", color=mapping['sex_col'] if mapping['sex_col'] else None)
    st.plotly_chart(fig, use_container_width=True)

# --- STEP 6: THE AGENTIC CHAT BRAIN ---
st.divider()
st.subheader(f"💬 Chat with your {agent_role}")

user_query = st.chat_input(f"Ask your {agent_role} a question about the data...")

if user_query:
    with st.chat_message("user"):
        st.write(user_query)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing data and generating insights..."):
            # This is the "Context Injection" that makes the AI smart
            data_summary = filtered_df.tail(5).to_string() # Give AI the last 5 years of data
            
            full_prompt = f"""
            You are a {agent_role}. 
            You are looking at employment data for {selected_country}.
            
            Recent Data Trends for this country:
            {data_summary}
            
            User Question: {user_query}
            
            Provide a professional, data-driven answer based ONLY on the trends provided. 
            If the user asks about a specific year not in the summary, ask them to check the charts.
            """
            
            try:
                response = model.generate_content(full_prompt)
                st.write(response.text)
            except Exception as e:
                st.error(f"AI Connection Error: {e}. Did you check your API Key?")

# --- STEP 7: RAW DATA ---
if st.checkbox("Show Raw Data Table"):
    st.write(filtered_df)