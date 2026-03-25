import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Page Title
st.title("🌍 Global Employment Explorer")
st.write("Analyze 30+ years of employment data instantly.")

# 2. Load Data (Using the file you uploaded)
@st.cache_data  # This makes the app fast by saving data in memory
def load_data():
    df = pd.read_csv("occupazione.csv")
    return df

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