import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai

# --- STEP 0: PAGE CONFIG ---
st.set_page_config(page_title="BFSI AI Agent", layout="wide", page_icon="🤖")

# --- STEP 1: RESILIENT AI SETUP (THE MODEL HUNTER) ---
# 🔑 Replace with your key from: https://aistudio.google.com/
API_KEY = "AIzaSyBcD8EwNxIC_88I_rVCCd9JZ7aGkQ6-QOc" 
genai.configure(api_key=API_KEY)

# We try multiple names to bypass the 404 error
model_names = ['gemini-1.5-flash', 'models/gemini-1.5-flash', 'gemini-pro']
model = None
active_model_name = "None"

for name in model_names:
    try:
        test_model = genai.GenerativeModel(name)
        # Quick test to see if the model is reachable
        test_model.generate_content("test", generation_config={"max_output_tokens": 1})
        model = test_model
        active_model_name = name
        break # Exit the loop once we find a working model
    except:
        continue

# --- STEP 2: DATA ENGINE ---
@st.cache_data
def load_data():
    try:
        data = pd.read_csv("occupazione.csv")
        data.columns = data.columns.str.strip().str.lower()
        mapping = {
            'country_col': 'ref_area' if 'ref_area' in data.columns else 'country',
            'year_col': 'time' if 'time' in data.columns else 'year',
            'value_col': 'obs_value',
            'sex_col': 'sex' if 'sex' in data.columns else 'gender'
        }
        data = data.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        return data, mapping
    except Exception as e:
        return None, None

df, mapping = load_data()

# --- STEP 3: SIDEBAR & PERSONA ---
st.sidebar.title("🎮 Agent Dashboard")
if model:
    st.sidebar.success(f"✅ AI Connected: {active_model_name}")
else:
    st.sidebar.error("❌ AI Connection Failed. Check API Key.")

agent_role = st.sidebar.selectbox("AI Persona", 
    ["BFSI Data Analyst", "Economic Researcher", "Global Labor Consultant"])

st.sidebar.divider()
countries = sorted(df[mapping['country_col']].unique())
selected_country = st.sidebar.selectbox("Select Country", countries)

# Gender Logic
if mapping['sex_col'] in df.columns:
    genders = df[mapping['sex_col']].unique().tolist()
    selected_sex = st.sidebar.radio("Gender Filter", genders)
    filtered_df = df[(df[mapping['country_col']] == selected_country) & (df[mapping['sex_col']] == selected_sex)]
else:
    filtered_df = df[df[mapping['country_col']] == selected_country]

filtered_df = filtered_df.sort_values(by=mapping['year_col'])

# --- STEP 4: VISUALS & METRICS ---
st.title("📈 BFSI Global Labor Insights")
st.write(f"Expert Analysis by: **{agent_role}**")

if not filtered_df.empty:
    m1, m2, m3 = st.columns(3)
    latest = filtered_df[mapping['value_col']].iloc[-1]
    prev = filtered_df[mapping['value_col']].iloc[-2] if len(filtered_df) > 1 else latest
    
    m1.metric("Current Rate", f"{latest}%", delta=f"{latest - prev:.2f}%")
    m2.metric("All-Time High", f"{filtered_df[mapping['value_col']].max()}%")
    m3.metric("All-Time Low", f"{filtered_df[mapping['value_col']].min()}%")

    fig = px.line(filtered_df, x=mapping['year_col'], y=mapping['value_col'], 
                  title=f"Trend: {selected_country}", markers=True)
    st.plotly_chart(fig, use_container_width=True)

# --- STEP 5: THE AI CHAT (CONTEXTUAL RAG) ---
st.divider()
st.subheader(f"💬 Chat with {agent_role}")

user_query = st.chat_input("Ask a question about the data...")

if user_query:
    with st.chat_message("user"):
        st.write(user_query)

    with st.chat_message("assistant"):
        if model:
            with st.spinner("Analyzing data..."):
                # We feed the last 15 rows to the AI so it has the full context
                data_summary = filtered_df.tail(15).to_string(index=False)
                
                prompt = f"""
                ROLE: {agent_role}
                COUNTRY: {selected_country}
                DATA:
                {data_summary}
                
                QUESTION: {user_query}
                
                INSTRUCTION: Use the DATA provided to answer the QUESTION professionally.
                """
                try:
                    response = model.generate_content(prompt)
                    st.write(response.text)
                except Exception as e:
                    st.error(f"Chat Error: {e}")
        else:
            st.warning("AI is not connected. Please check your API Key in the code.")

# --- STEP 6: DATA SOURCE ---
if st.checkbox("Show Raw Data"):
    st.dataframe(filtered_df)