import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Page Title
st.title("🌍 Global Employment Explorer")
st.write("Analyze 30+ years of employment data instantly.")

# --- STEP 1: DEFINE THE LOADING FUNCTION ---
@st.cache_data
def load_data():
    # We load the data here but don't 'use' it yet
    data = pd.read_csv("occupazione.csv")
    return data

# --- STEP 2: ACTUALLY CREATE THE 'df' VARIABLE ---
# This line MUST come before you try to use 'df.columns'
df = load_data()

# --- STEP 3: NOW USE THE DATA ---
# Now 'df' exists, so this line will work!
st.sidebar.write("Actual Columns in CSV:", df.columns.tolist())
df = load_data()

# 3. Sidebar Filters (The 'Controls')
st.sidebar.header("Filter Data")
selected_country = st.sidebar.selectbox("Select a Country", df['country'].unique())
selected_sex = st.sidebar.radio("Select Gender", ["Total", "Male", "Female"])

# 4. Filter the dataframe based on user input
filtered_df = df[(df['country'] == selected_country) & (df['sex'] == selected_sex)]

# 5. Display Visuals
st.subheader(f"Trend for {selected_country} ({selected_sex})")

# Create a line chart
fig = px.line(filtered_df, x="year", y="obs_value", title="Employment Rate Over Time")
st.plotly_chart(fig)

# 6. Display Raw Data Table
if st.checkbox("Show Raw Data"):
    st.write(filtered_df)

# 7. Add a simple Automation/Insight feature
st.divider()
st.subheader("💡 Automated AI Insight")

latest_val = filtered_df['obs_value'].iloc[-1]
previous_val = filtered_df['obs_value'].iloc[-2]
change = latest_val - previous_val

if change > 0:
    st.success(f"Employment is trending UP. It increased by {change:.2f}% compared to the previous period.")
else:
    st.warning(f"Employment is trending DOWN by {abs(change):.2f}%. Action may be needed.")

# This is a "Tool" that an AI Agent can call later
def get_employment_stats(country, year):
    """
    Finds the employment value for a specific country and year.
    This is what makes your app 'Agentic'.
    """
    try:
        result = df[(df['ref_area'] == country) & (df['time'] == year)]
        if not result.empty:
            value = result['obs_value'].iloc[0]
            return f"The employment rate for {country} in {year} was {value}%."
        else:
            return "Data not found for that specific selection."
    except Exception as e:
        return f"Error: {e}"

# Test it in your sidebar to see if it works
st.sidebar.divider()
st.sidebar.subheader("🤖 Agent Tool Test")
test_country = st.sidebar.text_input("Enter Country to test tool:")
test_year = st.sidebar.number_input("Enter Year to test tool:", min_value=1991, max_value=2025, value=2022)

if st.sidebar.button("Run Tool"):
    message = get_employment_stats(test_country, test_year)
    st.sidebar.info(message)

def get_employment_stats(country, year):
    """
    Finds the employment value for a specific country and year.
    Updated with the exact column names from your CSV.
    """
    try:
        # Convert year to string if necessary, as 'time' might be stored as text
        year_str = str(year)
        
        # Filtering the dataframe
        result = df[(df['ref_area'] == country) & (df['time'].astype(str) == year_str)]
        
        if not result.empty:
            # We take the first match and get the 'obs_value' column
            value = result['obs_value'].iloc[0]
            return f"✅ SUCCESS: In {year}, the employment rate for {country} was {value}%."
        else:
            return f"❓ INFO: No data found for {country} in {year}. (Check if the country name is exactly as shown in the dropdown)."
    except Exception as e:
        return f"❌ ERROR: {e}"