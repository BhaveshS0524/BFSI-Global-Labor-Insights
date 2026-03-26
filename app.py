import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Page Title
st.set_page_config(page_title="Global Employment Explorer", layout="wide")
st.title("🌍 Global Employment Explorer")
st.write("Analyze 30+ years of employment data instantly.")

# --- STEP 1: LOAD DATA ---
# --- STEP 1: LOAD DATA ---
@st.cache_data
def load_data():
    # Loading the dataset
    data = pd.read_csv("occupazione.csv")
    
    # SENIOR FIX: Remove any hidden spaces from column names
    data.columns = data.columns.str.strip()
    
    # SENIOR FIX: Remove any hidden spaces from the data itself
    data = data.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    
    return data

df = load_data()
# --- STEP 2: SIDEBAR & FILTERS ---
st.sidebar.header("Filter Data")

# Debugging: Show columns briefly (optional, you can remove this later)
# st.sidebar.write("Columns:", df.columns.tolist())

# IMPORTANT: Using 'ref_area' because that is the name in your CSV
available_countries = sorted(df['ref_area'].unique())
selected_country = st.sidebar.selectbox("Select a Country", available_countries)

# Since your CSV might use different labels for gender, let's keep it simple
selected_sex = st.sidebar.radio("Select Gender", ["Total", "Male", "Female"])

# --- STEP 3: FILTER & VISUALS ---
# We use 'ref_area' and 'sex' (ensure 'sex' exists in your CSV or adjust to 'sex_label')
filtered_df = df[(df['ref_area'] == selected_country)]

# Display Visuals
st.subheader(f"Trend for {selected_country}")

# Create a line chart - Using 'time' and 'obs_value' from your CSV
fig = px.line(filtered_df, x="time", y="obs_value", color="sex", 
              title=f"Employment Rate Over Time: {selected_country}")
st.plotly_chart(fig, use_container_width=True)

# --- STEP 4: AUTOMATED INSIGHT ---
st.divider()
st.subheader("💡 Automated AI Insight")

if len(filtered_df) > 1:
    latest_val = filtered_df['obs_value'].iloc[-1]
    previous_val = filtered_df['obs_value'].iloc[-2]
    change = latest_val - previous_val

    if change > 0:
        st.success(f"Employment is trending UP. It increased by {change:.2f}% compared to the previous period.")
    else:
        st.warning(f"Employment is trending DOWN by {abs(change):.2f}%. Action may be needed.")
else:
    st.info("Not enough data points to calculate a trend.")

# --- STEP 5: THE AGENTIC TOOL ---
# This is the "80k Salary" logic
def get_employment_stats(country, year):
    try:
        year_str = str(year)
        # Match 'ref_area' and 'time'
        result = df[(df['ref_area'] == country) & (df['time'].astype(str) == year_str)]
        
        if not result.empty:
            value = result['obs_value'].iloc[0]
            return f"✅ SUCCESS: In {year}, the employment rate for {country} was {value}%."
        else:
            return f"❓ INFO: No data found for {country} in {year}."
    except Exception as e:
        return f"❌ ERROR: {e}"

# Sidebar Tool Test
st.sidebar.divider()
st.sidebar.subheader("🤖 Agent Tool Test")
test_country = st.sidebar.text_input("Enter Country:", value="India")
test_year = st.sidebar.number_input("Enter Year:", min_value=1991, max_value=2025, value=2021)

if st.sidebar.button("Run Tool"):
    message = get_employment_stats(test_country, test_year)
    st.sidebar.info(message)

# 6. Display Raw Data Table
if st.checkbox("Show Raw Data"):
    st.write(filtered_df)