import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai

# --- STEP 0: PAGE CONFIGURATION ---
st.set_page_config(page_title="BFSI Labor Insights AI", layout="wide", page_icon="📈")

# --- STEP 1: AI BRAIN SETUP (THE PROVEN WAY) ---
# 🔑 Get your key from: https://aistudio.google.com/
API_KEY = "AIzaSyBcD8EwNxIC_88I_rVCCd9JZ7aGkQ6-QOc" 

try:
    genai.configure(api_key=API_KEY)
    # Using the most stable 2026 model version
    model = genai.GenerativeModel('gemini-pro')
except Exception as e:
    st.error(f"AI Configuration Error: {e}")

# --- STEP 2: DATA ENGINE (WITH SENIOR FIXES) ---
@st.cache_data
def load_data():
    try:
        data = pd.read_csv("occupazione.csv")
        data.columns = data.columns.str.strip().str.lower()
        
        # Intelligent Column Mapping
        mapping = {
            'country_col': 'ref_area' if 'ref_area' in data.columns else 'country',
            'year_col': 'time' if 'time' in data.columns else 'year',
            'value_col': 'obs_value',
            'sex_col': 'sex' if 'sex' in data.columns else 'gender'
        }
        # Clean white spaces from data
        data = data.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        return data, mapping
    except Exception as e:
        st.error(f"Data Load Error: {e}")
        return None, None

df, mapping = load_data()

# --- STEP 3: SIDEBAR (CONTROLS & PERSONA) ---
st.sidebar.title("🤖 Agent Control Center")
agent_role = st.sidebar.selectbox("Select AI Persona", 
    ["BFSI Data Analyst", "Economic Researcher", "Global Labor Consultant"])

st.sidebar.divider()
available_countries = sorted(df[mapping['country_col']].unique())
selected_country = st.sidebar.selectbox("Select Country", available_countries)

# Gender Logic
if mapping['sex_col'] in df.columns:
    genders = df[mapping['sex_col']].unique().tolist()
    selected_sex = st.sidebar.radio("Gender Filter", genders)
    filtered_df = df[(df[mapping['country_col']] == selected_country) & (df[mapping['sex_col']] == selected_sex)]
else:
    filtered_df = df[df[mapping['country_col']] == selected_country]

filtered_df = filtered_df.sort_values(by=mapping['year_col'])

# --- STEP 4: MAIN DASHBOARD (METRICS & TRENDS) ---
st.title("📈 BFSI Global Labor Insights")
st.write(f"Currently acting as: **{agent_role}**")

if not filtered_df.empty:
    col1, col2, col3 = st.columns(3)
    latest_val = filtered_df[mapping['value_col']].iloc[-1]
    prev_val = filtered_df[mapping['value_col']].iloc[-2] if len(filtered_df) > 1 else latest_val
    
    col1.metric("Latest Rate", f"{latest_val}%", delta=f"{latest_val - prev_val:.2f}%")
    col2.metric("Historical Max", f"{filtered_df[mapping['value_col']].max()}%")
    col3.metric("Historical Min", f"{filtered_df[mapping['value_col']].min()}%")

    fig = px.line(filtered_df, x=mapping['year_col'], y=mapping['value_col'], 
                  title=f"Employment Trend: {selected_country} ({selected_sex if 'selected_sex' in locals() else 'Total'})",
                  markers=True, template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

# --- STEP 5: THE AI AGENT CHAT (THE PROVEN BRIDGE) ---
st.divider()
st.subheader(f"💬 Consult with your {agent_role}")
st.caption("The AI has access to your filtered data trends below.")

user_query = st.chat_input("Ask a question about these employment trends...")

if user_query:
    with st.chat_message("user"):
        st.write(user_query)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing data and generating expert response..."):
            # PROVEN RAG PATTERN: Injecting data summary into the prompt
            recent_data_str = filtered_df.tail(10).to_string(index=False)
            
            prompt_context = f"""
            ROLE: You are a professional {agent_role}.
            CONTEXT: You are analyzing employment data for {selected_country}.
            DATA SNAPSHOT (Last 10 Records):
            {recent_data_str}
            
            USER QUESTION: {user_query}
            
            TASK: Provide a concise, expert analysis. Use the DATA SNAPSHOT to be specific. 
            If the user asks for data you don't see, tell them to check the charts above.
            """
            
            try:
                response = model.generate_content(prompt_context)
                st.write(response.text)
            except Exception as e:
                st.error(f"Connection Failed: {e}")
                st.info("Tip: Ensure your API Key is valid and 'google-generativeai' is in requirements.txt")

# --- STEP 6: RAW DATA CHECKBOX ---
if st.checkbox("Show Raw Data Source"):
    st.dataframe(filtered_df)
