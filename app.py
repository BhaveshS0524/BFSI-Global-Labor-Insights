import streamlit as st
import pandas as pd
import plotly.express as px

# ── 1. PAGE CONFIG ────────────────────────────────────────────────────────────
st.set_page_config(page_title="Global Employment Explorer", layout="wide")
st.title("🌍 Global Employment Explorer")
st.write("Analyze 30+ years of employment data instantly.")


# ── 2. LOAD DATA ──────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    data = pd.read_csv("occupazione.csv")

    # Strip hidden whitespace from column names and string values
    data.columns = data.columns.str.strip()
    data = data.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

    # Ensure obs_value is numeric (handles commas or stray text)
    data["obs_value"] = pd.to_numeric(data["obs_value"], errors="coerce")

    return data


df = load_data()

# ── 3. DETECT THE GENDER COLUMN ───────────────────────────────────────────────
# CSV files use different names: 'sex', 'sex_label', 'gender' — handle all
SEX_COL = None
for candidate in ["sex", "sex_label", "gender"]:
    if candidate in df.columns:
        SEX_COL = candidate
        break

if SEX_COL is None:
    st.error(
        f"❌ Could not find a gender column. "
        f"Columns found: {df.columns.tolist()}"
    )
    st.stop()

if "ref_area" not in df.columns:
    st.error(
        f"❌ Could not find 'ref_area' column. "
        f"Columns found: {df.columns.tolist()}"
    )
    st.stop()

# ── 4. SIDEBAR FILTERS ────────────────────────────────────────────────────────
st.sidebar.header("Filter Data")

available_countries = sorted(df["ref_area"].dropna().unique())
selected_country = st.sidebar.selectbox("Select a Country", available_countries)

# Build gender options from what actually exists in the column
raw_genders = df[SEX_COL].dropna().unique().tolist()

# Normalise display labels → map back to raw values
GENDER_MAP = {}
for val in raw_genders:
    label = str(val).strip()
    # Standardise common variants so the radio looks clean
    if label.lower() in ("tot", "total", "t", "both"):
        GENDER_MAP["Total"] = val
    elif label.lower() in ("male", "m", "men"):
        GENDER_MAP["Male"] = val
    elif label.lower() in ("female", "f", "women"):
        GENDER_MAP["Female"] = val
    else:
        GENDER_MAP[label] = val   # keep as-is if unrecognised

gender_options = list(GENDER_MAP.keys())
selected_sex_label = st.sidebar.radio("Select Gender", gender_options)
selected_sex_raw = GENDER_MAP[selected_sex_label]  # raw value used for filtering


# ── 5. FILTER DATA ────────────────────────────────────────────────────────────
# BUG FIX: previously the gender filter was selected but NEVER applied
filtered_df = df[
    (df["ref_area"] == selected_country) &
    (df[SEX_COL] == selected_sex_raw)
].copy()

# Sort by time so trend lines and insight logic are correct
filtered_df = filtered_df.sort_values("time").reset_index(drop=True)

# ── 6. LINE CHART ─────────────────────────────────────────────────────────────
st.subheader(f"Trend for {selected_country} — {selected_sex_label}")

if filtered_df.empty:
    st.warning("No data found for this combination. Try a different country or gender.")
else:
    fig = px.line(
        filtered_df,
        x="time",
        y="obs_value",
        color=SEX_COL,
        markers=True,
        title=f"Employment Rate Over Time: {selected_country} ({selected_sex_label})",
        labels={"obs_value": "Employment Rate (%)", "time": "Year"},
    )
    fig.update_layout(legend_title_text="Gender")
    st.plotly_chart(fig, use_container_width=True)


# ── 7. AUTOMATED INSIGHT ──────────────────────────────────────────────────────
st.divider()
st.subheader("💡 Automated AI Insight")

if len(filtered_df) >= 2:
    latest_val = filtered_df["obs_value"].iloc[-1]
    previous_val = filtered_df["obs_value"].iloc[-2]

    if pd.isna(latest_val) or pd.isna(previous_val):
        st.info("Latest data contains missing values — cannot calculate trend.")
    else:
        change = latest_val - previous_val
        latest_year = filtered_df["time"].iloc[-1]
        prev_year = filtered_df["time"].iloc[-2]

        if change > 0:
            st.success(
                f"📈 Employment is trending **UP** for {selected_country} ({selected_sex_label}). "
                f"It rose by **{change:.2f}%** from {prev_year} to {latest_year}."
            )
        elif change < 0:
            st.warning(
                f"📉 Employment is trending **DOWN** for {selected_country} ({selected_sex_label}). "
                f"It fell by **{abs(change):.2f}%** from {prev_year} to {latest_year}."
            )
        else:
            st.info(f"➡️ Employment remained **unchanged** between {prev_year} and {latest_year}.")
else:
    st.info("Not enough data points to calculate a trend.")


# ── 8. AGENT TOOL ─────────────────────────────────────────────────────────────
def get_employment_stats(country: str, year: int) -> str:
    """Return employment stats for a given country and year (all genders)."""
    try:
        year_str = str(year)
        result = df[
            (df["ref_area"].str.lower() == country.strip().lower()) &
            (df["time"].astype(str) == year_str)
        ]

        if not result.empty:
            lines = [f"📊 Employment data for **{country}** in **{year}**:\n"]
            for _, row in result.iterrows():
                gender = row[SEX_COL]
                value = row["obs_value"]
                if pd.notna(value):
                    lines.append(f"• {gender}: **{value:.2f}%**")
                else:
                    lines.append(f"• {gender}: data not available")
            return "\n".join(lines)
        else:
            return f"❓ No data found for **{country}** in **{year}**. Check spelling (case-insensitive)."
    except Exception as e:
        return f"❌ ERROR: {e}"


st.sidebar.divider()
st.sidebar.subheader("🤖 Agent Tool Test")

test_country = st.sidebar.text_input("Enter Country:", value="India")
test_year = st.sidebar.number_input(
    "Enter Year:", min_value=1991, max_value=2025, value=2021
)

if st.sidebar.button("Run Tool"):
    message = get_employment_stats(test_country, int(test_year))
    st.sidebar.markdown(message)


# ── 9. RAW DATA TABLE ─────────────────────────────────────────────────────────
if st.checkbox("Show Raw Data"):
    st.dataframe(filtered_df, use_container_width=True)
