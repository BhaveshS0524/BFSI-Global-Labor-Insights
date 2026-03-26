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

# --- STEP 5: THE AGENTIC TOOL ---
def get_employment_stats(country, year):
    """
    Agent-ready tool to fetch specific data points.
    """
    try:
        # Match using the mapped columns
        result = df[(df[mapping['country_col']] == country) & (df[mapping['year_col']].astype(str) == str(year))]
        
        if not result.empty:
            value = result[mapping['value_col']].iloc[0]
            return f"✅ SUCCESS: In {year}, the employment rate for {country} was {value}%."
        else:
            return f"❓ INFO: No data found for {country} in {year}."
    except Exception as e:
        return f"❌ ERROR: {e}"

# Sidebar Tool Test
st.sidebar.divider()
st.sidebar.subheader("🤖 Agent Tool Test")
test_country = st.sidebar.text_input("Enter Country:", value=selected_country)
test_year = st.sidebar.number_input("Enter Year:", min_value=1991, max_value=2025, value=2021)

if st.sidebar.button("Run Tool"):
    message = get_employment_stats(test_country, test_year)
    st.sidebar.info(message)

# 6. Show Raw Data
if st.checkbox("Show Raw Data Table"):
    st.write(filtered_df)