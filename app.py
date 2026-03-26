import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Page Configuration
st.set_page_config(page_title="Global Employment Explorer", layout="wide")
st.title("🌍 Global Employment Explorer")
st.write("Analyze 30+ years of global employment data instantly.")

# --- STEP 1: LOAD & NORMALIZE DATA ---
@st.cache_data
def load_data():
    # Load the file
    data = pd.read_csv("occupazione.csv")
    
    # SENIOR FIX: Clean column names (remove spaces and lowercase)
    data.columns = data.columns.str.strip().str.lower()
    
    # MAPPING: We define which column to use for 'Country', 'Year', and 'Value'
    # This avoids the KeyError by checking multiple possible names
    column_mapping = {
        'country_col': 'ref_area' if 'ref_area' in data.columns else ('country' if 'country' in data.columns else data.columns[1]),
        'year_col': 'time' if 'time' in data.columns else ('year' if 'year' in data.columns else 'time'),
        'value_col': 'obs_value' if 'obs_value' in data.columns else 'obs_value',
        'sex_col': 'sex' if 'sex' in data.columns else ('gender' if 'gender' in data.columns else None)
    }
    
    return data, column_mapping

# Load data and get the mapping
df, mapping = load_data()

# --- STEP 2: SIDEBAR & FILTERS ---
st.sidebar.header("Filter Data")

# Use the mapped column for country selection
available_countries = sorted(df[mapping['country_col']].unique())
selected_country = st.sidebar.selectbox("Select a Country", available_countries)

# Gender Selection (if the column exists)
if mapping['sex_col']:
    available_genders = df[mapping['sex_col']].unique().tolist()
    selected_sex = st.sidebar.radio("Select Gender", available_genders)
    filtered_df = df[(df[mapping['country_col']] == selected_country) & (df[mapping['sex_col']] == selected_sex)]
else:
    filtered_df = df[df[mapping['country_col']] == selected_country]

# --- STEP 3: VISUALS ---
st.subheader(f"Trend for {selected_country}")

# Use the mapped columns for the chart
fig = px.line(filtered_df, 
              x=mapping['year_col'], 
              y=mapping['value_col'], 
              title=f"Employment Rate Over Time: {selected_country}")
st.plotly_chart(fig, use_container_width=True)

# --- NEW: EXECUTIVE METRICS ROW ---
st.divider()
col1, col2, col3 = st.columns(3)

# 1. Highest Employment Rate in History
max_val = filtered_df[mapping['value_col']].max()
max_year = filtered_df[filtered_df[mapping['value_col']] == max_val][mapping['year_col']].iloc[0]

# 2. Lowest Employment Rate in History
min_val = filtered_df[mapping['value_col']].min()
min_year = filtered_df[filtered_df[mapping['value_col']] == min_val][mapping['year_col']].iloc[0]

# 3. Current Rate vs Previous (Delta)
latest_rate = filtered_df[mapping['value_col']].iloc[-1]
prev_rate = filtered_df[mapping['value_col']].iloc[-2] if len(filtered_df) > 1 else latest_rate
delta = latest_rate - prev_rate

with col1:
    st.metric(label="All-Time High", value=f"{max_val}%", help=f"Recorded in {max_year}")

with col2:
    st.metric(label="All-Time Low", value=f"{min_val}%", help=f"Recorded in {min_year}")

with col3:
    st.metric(label="Latest Change", value=f"{latest_rate}%", delta=f"{delta:.2f}%")

# --- STEP 4: AUTOMATED AI INSIGHT ---
st.divider()
st.subheader("💡 Automated AI Insight")

# Ensure we have enough data to compare
if len(filtered_df) >= 2:
    # Sort by year to ensure we compare the latest
    filtered_df = filtered_df.sort_values(by=mapping['year_col'])
    latest_val = filtered_df[mapping['value_col']].iloc[-1]
    previous_val = filtered_df[mapping['value_col']].iloc[-2]
    change = latest_val - previous_val

    if change > 0:
        st.success(f"Employment is trending UP. It increased by {change:.2f}% compared to the previous period.")
    else:
        st.warning(f"Employment is trending DOWN by {abs(change):.2f}%. Action may be needed.")
else:
    st.info("Not enough data points to calculate a trend.")

# --- STEP 6: AGENT PERSONALITY SETTINGS ---
st.sidebar.divider()
st.sidebar.subheader("🧠 AI Agent Configuration")
agent_role = st.sidebar.selectbox("Agent Persona", 
    ["BFSI Data Analyst", "Economic Researcher", "Global Labor Consultant"])

system_instructions = f"""
You are an expert {agent_role}. 
Your goal is to explain employment trends to users in Ahmedabad and across the globe.
Always use the 'get_employment_stats' tool to verify facts before answering.
"""
st.sidebar.caption("System Instructions Loaded.")

# --- STEP 5: THE AGENTIC TOOL (VERSION 2.0 - API READY) ---
def get_employment_stats(country, year):
    """
    PROFESSIONAL TOOL: Fetches employment data for an AI Agent.
    Handles case-sensitivity and provides structured dictionary feedback.
    """
    try:
        # 1. Normalize Input (Strip spaces and capitalize for matching)
        target_country = str(country).strip().title()
        target_year = str(year).strip()
        
        # 2. Search using normalized columns
        # We use .str.title() on the dataframe side to match our input
        result = df[
            (df[mapping['country_col']].str.title() == target_country) & 
            (df[mapping['year_col']].astype(str) == target_year)
        ]
        
        if not result.empty:
            value = result[mapping['value_col']].iloc[0]
            return {
                "status": "success",
                "data": value,
                "message": f"✅ SUCCESS: In {target_year}, {target_country} had an employment rate of {value}%."
            }
        else:
            return {
                "status": "not_found",
                "message": f"❓ INFO: No data found for '{target_country}' in {target_year}."
            }
    except Exception as e:
        return {"status": "error", "message": f"❌ ERROR: {str(e)}"}

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

# --- STEP 7: THE CHAT INTERFACE ---
st.divider()
st.subheader(f"💬 Chat with your {agent_role}")
st.info(f"The {agent_role} is initialized with your data. Ask a question below.")

# User Input Box
user_question = st.chat_input("Ask a question about global employment trends...")

if user_question:
    with st.chat_message("user"):
        st.write(user_question)
    
    with st.chat_message("assistant"):
        # This is a placeholder until we connect Gemini tomorrow
        st.write(f"Hello! I am your {agent_role}. I see you are asking about '{user_question}'.")
        st.write("Tomorrow, I will be connected to the Gemini API to give you a real-time reasoned answer using your data tools!")