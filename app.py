import streamlit as st
import pandas as pd
import plotly.express as px
from google import genai  # THE NEW 2026 SDK

# --- PAGE CONFIG ---
st.set_page_config(page_title="BFSI AI Agent", layout="wide")

# --- STEP 1: MODERN AI SETUP ---
# 🔑 Get a fresh key if needed from https://aistudio.google.com/
API_KEY = "AIzaSyBcD8EwNxIC_88I_rVCCd9JZ7aGkQ6-QOc" 

try:
    client = genai.Client(api_key=API_KEY)
    # Using the 2.0 Flash model (Standard for 2026)
    MODEL_ID = "gemini-2.0-flash" 
except Exception as e:
    st.error(f"AI Setup Error: {e}")

# --- STEP 2: DATA ENGINE ---
@st.cache_data
def load_data():
    data = pd.read_csv("occupazione.csv")
    data.columns = data.columns.str.strip().str.lower()
    mapping = {
        'country_col': 'ref_area' if 'ref_area' in data.columns else 'country',
        'year_col': 'time' if 'time' in data.columns else 'year',
        'value_col': 'obs_value'
    }
    return data, mapping

df, mapping = load_data()

# --- STEP 3: SIDEBAR & FILTERS ---
st.sidebar.title("🤖 Agent Settings")
agent_role = st.sidebar.selectbox("Persona", ["BFSI Analyst", "Researcher", "Consultant"])
countries = sorted(df[mapping['country_col']].unique())
selected_country = st.sidebar.selectbox("Select Country", countries)

# --- STEP 4: DASHBOARD VISUALS ---
st.title("📈 BFSI Labor Insights Platform")
filtered_df = df[df[mapping['country_col']] == selected_country].sort_values(by=mapping['year_col'])

if not filtered_df.empty:
    fig = px.line(filtered_df, x=mapping['year_col'], y=mapping['value_col'], title=f"Trend: {selected_country}")
    st.plotly_chart(fig, use_container_width=True)

# --- STEP 5: THE MODERN CHAT INTERFACE ---
st.divider()
st.subheader(f"💬 Chat with your {agent_role}")
user_query = st.chat_input("Ask about the data trends...")

if user_query:
    with st.chat_message("user"):
        st.write(user_query)
        
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # MODERN SYNTAX: We send context and query to the 2.0 model
                data_summary = filtered_df.tail(10).to_string(index=False)
                
                response = client.models.generate_content(
                    model=MODEL_ID,
                    contents=f"Role: {agent_role}\nData: {data_summary}\nQuestion: {user_query}"
                )
                st.write(response.text)
            except Exception as e:
                st.error(f"Connection Failed: {e}")
                st.info("Ensure 'google-genai' is in requirements.txt and your key is active.")