import streamlit as st
import pandas as pd
import plotly.express as px
from google import genai  # THE NEW SDK

# --- PAGE CONFIG ---
st.set_page_config(page_title="BFSI AI Agent", layout="wide")

# --- STEP 1: MODERN AI SETUP ---
API_KEY = "YOUR_API_KEY_HERE" 
try:
    # New SDK uses a Client object
    client = genai.Client(api_key=API_KEY)
    # Testing with the new 2026 flagship model
    model_id = "gemini-2.0-flash" 
except Exception as e:
    st.error(f"Setup Error: {e}")

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

# --- STEP 3: SIDEBAR ---
st.sidebar.title("🤖 Agent Settings")
agent_role = st.sidebar.selectbox("Persona", ["BFSI Analyst", "Researcher"])
selected_country = st.sidebar.selectbox("Country", sorted(df[mapping['country_col']].unique()))

# --- STEP 4: CHAT INTERFACE ---
st.title("📈 BFSI Labor Insights")
user_query = st.chat_input("Ask about the data...")

if user_query:
    with st.chat_message("user"):
        st.write(user_query)
        
    with st.chat_message("assistant"):
        try:
            # We use the new generate_content syntax
            response = client.models.generate_content(
                model=model_id,
                contents=f"Role: {agent_role}\nCountry: {selected_country}\nQuery: {user_query}"
            )
            st.write(response.text)
        except Exception as e:
            st.error(f"Connection Error: {e}")
            st.info("Ensure 'google-genai' is in requirements.txt")