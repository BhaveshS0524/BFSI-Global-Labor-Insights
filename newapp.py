import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import google.generativeai as genai
import json
import numpy as np

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Global Labour Market Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    .main { background-color: #0f1117; }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #1e2130 0%, #252a3d 100%);
        border: 1px solid #2e3452;
        border-radius: 16px;
        padding: 20px 24px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    .metric-card h3 { color: #8b92b3; font-size: 12px; font-weight: 500; 
                       text-transform: uppercase; letter-spacing: 1px; margin: 0 0 8px 0; }
    .metric-card .value { font-size: 32px; font-weight: 700; margin: 0; }
    .metric-card .delta { font-size: 12px; margin-top: 6px; }
    .red-val   { color: #ff6b6b; }
    .green-val { color: #51cf66; }
    .blue-val  { color: #74c0fc; }
    .gold-val  { color: #ffd43b; }

    /* Section headers */
    .section-header {
        color: #e2e8f0;
        font-size: 18px;
        font-weight: 600;
        margin: 8px 0 16px 0;
        padding-bottom: 8px;
        border-bottom: 2px solid #2e3452;
    }

    /* AI chat */
    .chat-msg-user {
        background: linear-gradient(135deg, #3b4fd8 0%, #5c6ef0 100%);
        color: white; border-radius: 16px 16px 4px 16px;
        padding: 12px 16px; margin: 8px 0; max-width: 80%; float: right; clear: both;
    }
    .chat-msg-ai {
        background: linear-gradient(135deg, #1e2130 0%, #252a3d 100%);
        border: 1px solid #2e3452; color: #e2e8f0;
        border-radius: 16px 16px 16px 4px;
        padding: 12px 16px; margin: 8px 0; max-width: 85%; float: left; clear: both;
    }
    .chat-clearfix { clear: both; }
    .ai-badge { color: #74c0fc; font-weight: 600; font-size: 12px; margin-bottom: 4px; }
    .user-badge { color: #a9b1ff; font-weight: 600; font-size: 12px; 
                  margin-bottom: 4px; text-align: right; }

    /* Sidebar */
    .css-1d391kg, section[data-testid="stSidebar"] {
        background-color: #151823 !important;
    }

    /* Hide Streamlit default footer */
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Data loading ──────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    unemp = pd.read_csv("disoccupazione.csv")
    emp   = pd.read_csv("occupazione.csv")
    unemp.rename(columns={"obs_value": "unemployment_rate"}, inplace=True)
    emp.rename(columns={"obs_value": "employment_rate"},   inplace=True)
    merged = pd.merge(unemp, emp, on=["iso_code","country","sex","age","year"], how="outer")
    return unemp, emp, merged

unemp_df, emp_df, merged_df = load_data()

all_countries = sorted(merged_df["country"].unique())
all_years     = sorted(merged_df["year"].unique())
min_year, max_year = int(min(all_years)), int(max(all_years))

# ── Sidebar filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌍 Labour Market Dashboard")
    st.markdown("---")

    st.markdown("### 🔍 Smart Filters")

    selected_countries = st.multiselect(
        "Countries", all_countries,
        default=["United States", "Germany", "India", "Brazil", "China"]
    )
    if not selected_countries:
        selected_countries = all_countries[:5]

    year_range = st.slider("Year Range", min_year, max_year, (2005, max_year))

    sex_options = st.multiselect(
        "Gender", ["Total", "Male", "Female"], default=["Total"]
    )
    if not sex_options:
        sex_options = ["Total"]

    age_options = st.multiselect(
        "Age Group", ["15+", "15-24", "25+"], default=["15+"]
    )
    if not age_options:
        age_options = ["15+"]

    st.markdown("---")
    st.markdown("### 🤖 Gemini AI Agent")
    gemini_key = st.text_input("Gemini API Key", type="password",
                               placeholder="AIza...")
    st.caption("Get a free key at [ai.google.dev](https://ai.google.dev)")

    st.markdown("---")
    st.caption("Data: ILO Global Labour Statistics")

# ── Filter data ───────────────────────────────────────────────────────────────
@st.cache_data
def filter_df(df, countries, yr_min, yr_max, sexes, ages):
    return df[
        df["country"].isin(countries) &
        df["year"].between(yr_min, yr_max) &
        df["sex"].isin(sexes) &
        df["age"].isin(ages)
    ]

filtered = filter_df(merged_df, selected_countries,
                     year_range[0], year_range[1], sex_options, age_options)
unemp_f  = filter_df(unemp_df, selected_countries,
                     year_range[0], year_range[1], sex_options, age_options)
emp_f    = filter_df(emp_df, selected_countries,
                     year_range[0], year_range[1], sex_options, age_options)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<h1 style='color:#e2e8f0; font-size:28px; font-weight:700; margin-bottom:4px;'>
  🌍 Global Labour Market Dashboard
</h1>
<p style='color:#8b92b3; margin-top:0; font-size:14px;'>
  Unemployment & Employment Intelligence — ILO Data 1991–2025
</p>
""", unsafe_allow_html=True)

# ── KPI Cards ─────────────────────────────────────────────────────────────────
latest_year = filtered["year"].max() if not filtered.empty else max_year
prev_year   = latest_year - 1

latest = filtered[(filtered["year"] == latest_year) & (filtered["sex"] == "Total") & (filtered["age"] == "15+")]
prev   = filtered[(filtered["year"] == prev_year)   & (filtered["sex"] == "Total") & (filtered["age"] == "15+")]

avg_unemp   = latest["unemployment_rate"].mean()
avg_emp     = latest["employment_rate"].mean()
prev_unemp  = prev["unemployment_rate"].mean()
prev_emp    = prev["employment_rate"].mean()

unemp_delta = avg_unemp - prev_unemp
emp_delta   = avg_emp   - prev_emp

highest_unemp_row = latest.nlargest(1, "unemployment_rate")
lowest_unemp_row  = latest.nsmallest(1, "unemployment_rate")

highest_unemp_country = highest_unemp_row["country"].values[0] if not highest_unemp_row.empty else "N/A"
highest_unemp_val     = highest_unemp_row["unemployment_rate"].values[0] if not highest_unemp_row.empty else 0
lowest_unemp_country  = lowest_unemp_row["country"].values[0]  if not lowest_unemp_row.empty else "N/A"
lowest_unemp_val      = lowest_unemp_row["unemployment_rate"].values[0] if not lowest_unemp_row.empty else 0

col1, col2, col3, col4 = st.columns(4)

with col1:
    delta_sign = "▲" if unemp_delta > 0 else "▼"
    delta_col  = "red-val" if unemp_delta > 0 else "green-val"
    st.markdown(f"""
    <div class='metric-card'>
      <h3>Avg Unemployment Rate</h3>
      <p class='value red-val'>{avg_unemp:.1f}%</p>
      <p class='delta {delta_col}'>{delta_sign} {abs(unemp_delta):.2f}% vs {prev_year}</p>
    </div>""", unsafe_allow_html=True)

with col2:
    delta_sign = "▲" if emp_delta > 0 else "▼"
    delta_col  = "green-val" if emp_delta > 0 else "red-val"
    st.markdown(f"""
    <div class='metric-card'>
      <h3>Avg Employment Rate</h3>
      <p class='value green-val'>{avg_emp:.1f}%</p>
      <p class='delta {delta_col}'>{delta_sign} {abs(emp_delta):.2f}% vs {prev_year}</p>
    </div>""", unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class='metric-card'>
      <h3>Highest Unemployment</h3>
      <p class='value red-val'>{highest_unemp_val:.1f}%</p>
      <p class='delta' style='color:#8b92b3;'>{highest_unemp_country} ({latest_year})</p>
    </div>""", unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class='metric-card'>
      <h3>Lowest Unemployment</h3>
      <p class='value green-val'>{lowest_unemp_val:.1f}%</p>
      <p class='delta' style='color:#8b92b3;'>{lowest_unemp_country} ({latest_year})</p>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Trends", "🗺️ World Map", "⚖️ Comparisons",
    "👥 Demographics", "🤖 AI Agent"
])

# ══ TAB 1: TRENDS ════════════════════════════════════════════════════════════
with tab1:
    st.markdown("<div class='section-header'>Unemployment & Employment Trends Over Time</div>",
                unsafe_allow_html=True)

    col_a, col_b = st.columns(2)

    with col_a:
        trend_u = unemp_f.groupby(["year","country"])["unemployment_rate"].mean().reset_index()
        fig_u = px.line(
            trend_u, x="year", y="unemployment_rate", color="country",
            title="📉 Unemployment Rate Trend",
            labels={"unemployment_rate": "Rate (%)", "year": "Year"},
            template="plotly_dark",
        )
        fig_u.update_layout(
            plot_bgcolor="#1e2130", paper_bgcolor="#1e2130",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            title_font_color="#e2e8f0", font_color="#8b92b3",
            hovermode="x unified",
        )
        fig_u.update_traces(line_width=2.5)
        st.plotly_chart(fig_u, use_container_width=True)

    with col_b:
        trend_e = emp_f.groupby(["year","country"])["employment_rate"].mean().reset_index()
        fig_e = px.line(
            trend_e, x="year", y="employment_rate", color="country",
            title="📈 Employment Rate Trend",
            labels={"employment_rate": "Rate (%)", "year": "Year"},
            template="plotly_dark",
        )
        fig_e.update_layout(
            plot_bgcolor="#1e2130", paper_bgcolor="#1e2130",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            title_font_color="#e2e8f0", font_color="#8b92b3",
            hovermode="x unified",
        )
        fig_e.update_traces(line_width=2.5)
        st.plotly_chart(fig_e, use_container_width=True)

    # Dual-axis combo chart
    st.markdown("<div class='section-header'>Combined View — Unemployment vs Employment</div>",
                unsafe_allow_html=True)

    combo_country = st.selectbox("Select Country for Combo Chart",
                                 selected_countries, key="combo_sel")
    combo_data = filtered[
        (filtered["country"] == combo_country) &
        (filtered["sex"] == "Total") &
        (filtered["age"] == "15+")
    ].sort_values("year")

    fig_combo = make_subplots(specs=[[{"secondary_y": True}]])
    fig_combo.add_trace(go.Scatter(
        x=combo_data["year"], y=combo_data["unemployment_rate"],
        name="Unemployment %", line=dict(color="#ff6b6b", width=2.5),
        fill="tozeroy", fillcolor="rgba(255,107,107,0.08)"
    ), secondary_y=False)
    fig_combo.add_trace(go.Scatter(
        x=combo_data["year"], y=combo_data["employment_rate"],
        name="Employment %", line=dict(color="#51cf66", width=2.5),
        fill="tozeroy", fillcolor="rgba(81,207,102,0.08)"
    ), secondary_y=True)
    fig_combo.update_layout(
        title=f"📊 {combo_country} — Unemployment vs Employment",
        plot_bgcolor="#1e2130", paper_bgcolor="#1e2130",
        font_color="#8b92b3", title_font_color="#e2e8f0",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig_combo.update_yaxes(title_text="Unemployment %", secondary_y=False, color="#ff6b6b")
    fig_combo.update_yaxes(title_text="Employment %",   secondary_y=True,  color="#51cf66")
    st.plotly_chart(fig_combo, use_container_width=True)

# ══ TAB 2: WORLD MAP ═════════════════════════════════════════════════════════
with tab2:
    st.markdown("<div class='section-header'>Global Choropleth Maps</div>",
                unsafe_allow_html=True)

    map_year = st.slider("Select Year for Map",
                         min_year, max_year, max_year, key="map_year")
    map_metric = st.radio("Metric", ["Unemployment Rate", "Employment Rate"],
                          horizontal=True, key="map_metric")

    map_data = merged_df[
        (merged_df["year"] == map_year) &
        (merged_df["sex"] == "Total") &
        (merged_df["age"] == "15+")
    ]

    col_field = "unemployment_rate" if map_metric == "Unemployment Rate" else "employment_rate"
    color_scale = "Reds" if map_metric == "Unemployment Rate" else "Greens"
    title_map = f"🗺️ {map_metric} — {map_year}"

    fig_map = px.choropleth(
        map_data, locations="iso_code", color=col_field,
        hover_name="country",
        hover_data={col_field: ":.2f", "iso_code": False},
        color_continuous_scale=color_scale,
        title=title_map, template="plotly_dark",
    )
    fig_map.update_layout(
        plot_bgcolor="#1e2130", paper_bgcolor="#1e2130",
        geo=dict(bgcolor="#1e2130", showframe=False,
                 showcoastlines=True, coastlinecolor="#2e3452"),
        title_font_color="#e2e8f0", font_color="#8b92b3",
        coloraxis_colorbar=dict(title="%", tickfont=dict(color="#8b92b3")),
        margin=dict(l=0, r=0, t=40, b=0),
        height=520,
    )
    st.plotly_chart(fig_map, use_container_width=True)

    # Top/Bottom table
    col_top, col_bot = st.columns(2)
    with col_top:
        top10 = map_data.nlargest(10, col_field)[["country", col_field]].reset_index(drop=True)
        top10.columns = ["Country", f"{map_metric} (%)"]
        top10[f"{map_metric} (%)"] = top10[f"{map_metric} (%)"].round(2)
        top10.index += 1
        st.markdown(f"**🔴 Top 10 Highest {map_metric}**")
        st.dataframe(top10, use_container_width=True, height=350)
    with col_bot:
        bot10 = map_data.nsmallest(10, col_field)[["country", col_field]].reset_index(drop=True)
        bot10.columns = ["Country", f"{map_metric} (%)"]
        bot10[f"{map_metric} (%)"] = bot10[f"{map_metric} (%)"].round(2)
        bot10.index += 1
        st.markdown(f"**🟢 Top 10 Lowest {map_metric}**")
        st.dataframe(bot10, use_container_width=True, height=350)

# ══ TAB 3: COMPARISONS ═══════════════════════════════════════════════════════
with tab3:
    st.markdown("<div class='section-header'>Country Comparisons & Rankings</div>",
                unsafe_allow_html=True)

    # Bar race / snapshot bar chart
    snap_year = st.slider("Snapshot Year", min_year, max_year, max_year, key="snap_year")
    snap_metric = st.radio("Metric", ["Unemployment Rate", "Employment Rate"],
                           horizontal=True, key="snap_metric")
    snap_field = "unemployment_rate" if snap_metric == "Unemployment Rate" else "employment_rate"
    snap_color = "#ff6b6b" if snap_metric == "Unemployment Rate" else "#51cf66"

    snap_data = merged_df[
        (merged_df["year"] == snap_year) &
        (merged_df["sex"] == "Total") &
        (merged_df["age"] == "15+") &
        (merged_df["country"].isin(selected_countries))
    ].sort_values(snap_field, ascending=True)

    fig_bar = px.bar(
        snap_data, x=snap_field, y="country", orientation="h",
        title=f"📊 {snap_metric} by Country — {snap_year}",
        labels={snap_field: "%", "country": ""},
        template="plotly_dark", text_auto=".1f",
    )
    fig_bar.update_traces(marker_color=snap_color, textfont_color="white")
    fig_bar.update_layout(
        plot_bgcolor="#1e2130", paper_bgcolor="#1e2130",
        title_font_color="#e2e8f0", font_color="#8b92b3",
        height=max(300, len(selected_countries) * 40),
        xaxis=dict(gridcolor="#2e3452"),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # Scatter: unemployment vs employment
    st.markdown("<div class='section-header'>Unemployment vs Employment Scatter</div>",
                unsafe_allow_html=True)

    scatter_year = st.slider("Year", min_year, max_year, max_year, key="scatter_year")
    scatter_data = merged_df[
        (merged_df["year"] == scatter_year) &
        (merged_df["sex"] == "Total") &
        (merged_df["age"] == "15+")
    ].dropna(subset=["unemployment_rate","employment_rate"])

    fig_scatter = px.scatter(
        scatter_data, x="unemployment_rate", y="employment_rate",
        hover_name="country", color="unemployment_rate",
        color_continuous_scale="RdYlGn_r",
        title=f"🔵 Unemployment vs Employment — {scatter_year} (all countries)",
        labels={"unemployment_rate": "Unemployment %",
                "employment_rate": "Employment %"},
        template="plotly_dark", size_max=12,
        opacity=0.8,
    )
    # Highlight selected countries
    highlight = scatter_data[scatter_data["country"].isin(selected_countries)]
    fig_scatter.add_trace(go.Scatter(
        x=highlight["unemployment_rate"], y=highlight["employment_rate"],
        mode="markers+text", name="Selected",
        text=highlight["country"],
        textposition="top center",
        marker=dict(color="#ffd43b", size=12, line=dict(width=2, color="#fff")),
    ))
    fig_scatter.update_layout(
        plot_bgcolor="#1e2130", paper_bgcolor="#1e2130",
        title_font_color="#e2e8f0", font_color="#8b92b3",
        xaxis=dict(gridcolor="#2e3452"),
        yaxis=dict(gridcolor="#2e3452"),
        height=480,
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

# ══ TAB 4: DEMOGRAPHICS ══════════════════════════════════════════════════════
with tab4:
    st.markdown("<div class='section-header'>Gender & Age Group Analysis</div>",
                unsafe_allow_html=True)

    demo_country = st.selectbox("Select Country", selected_countries, key="demo_country")
    demo_year_range = st.slider("Year Range", min_year, max_year,
                                (2010, max_year), key="demo_yr")

    demo_data = merged_df[
        (merged_df["country"] == demo_country) &
        (merged_df["year"].between(demo_year_range[0], demo_year_range[1]))
    ]

    col_g1, col_g2 = st.columns(2)

    with col_g1:
        gender_u = demo_data[
            (demo_data["sex"].isin(["Male","Female"])) &
            (demo_data["age"] == "15+")
        ].groupby(["year","sex"])["unemployment_rate"].mean().reset_index()

        fig_gu = px.line(
            gender_u, x="year", y="unemployment_rate", color="sex",
            color_discrete_map={"Male": "#74c0fc", "Female": "#f783ac"},
            title=f"👥 Gender Unemployment — {demo_country}",
            labels={"unemployment_rate": "Rate (%)", "year": "Year"},
            template="plotly_dark",
        )
        fig_gu.update_layout(
            plot_bgcolor="#1e2130", paper_bgcolor="#1e2130",
            title_font_color="#e2e8f0", font_color="#8b92b3",
        )
        fig_gu.update_traces(line_width=2.5)
        st.plotly_chart(fig_gu, use_container_width=True)

    with col_g2:
        age_u = demo_data[
            (demo_data["sex"] == "Total") &
            (demo_data["age"].isin(["15-24","25+"]))
        ].groupby(["year","age"])["unemployment_rate"].mean().reset_index()

        fig_au = px.line(
            age_u, x="year", y="unemployment_rate", color="age",
            color_discrete_map={"15-24": "#ffd43b", "25+": "#a9e34b"},
            title=f"📅 Age Group Unemployment — {demo_country}",
            labels={"unemployment_rate": "Rate (%)", "year": "Year"},
            template="plotly_dark",
        )
        fig_au.update_layout(
            plot_bgcolor="#1e2130", paper_bgcolor="#1e2130",
            title_font_color="#e2e8f0", font_color="#8b92b3",
        )
        fig_au.update_traces(line_width=2.5)
        st.plotly_chart(fig_au, use_container_width=True)

    # Grouped bar – latest year breakdown
    latest_demo = demo_data[demo_data["year"] == demo_data["year"].max()]
    breakdown = latest_demo[latest_demo["sex"].isin(["Male","Female"])][
        ["sex","age","unemployment_rate"]
    ].dropna()

    fig_grp = px.bar(
        breakdown, x="age", y="unemployment_rate", color="sex", barmode="group",
        color_discrete_map={"Male": "#74c0fc", "Female": "#f783ac"},
        title=f"📊 {demo_country} — Unemployment by Sex & Age ({demo_data['year'].max()})",
        labels={"unemployment_rate": "Rate (%)", "age": "Age Group"},
        template="plotly_dark", text_auto=".1f",
    )
    fig_grp.update_layout(
        plot_bgcolor="#1e2130", paper_bgcolor="#1e2130",
        title_font_color="#e2e8f0", font_color="#8b92b3",
        xaxis=dict(gridcolor="#2e3452"),
        yaxis=dict(gridcolor="#2e3452"),
    )
    st.plotly_chart(fig_grp, use_container_width=True)

# ══ TAB 5: AI AGENT ══════════════════════════════════════════════════════════
with tab5:
    st.markdown("<div class='section-header'>🤖 Gemini AI Labour Market Analyst</div>",
                unsafe_allow_html=True)

    st.markdown("""
    <p style='color:#8b92b3; font-size:14px;'>
    Ask anything about the labour market data! The AI agent reads the full dataset context
    and answers in natural language. Examples:
    </p>
    <ul style='color:#74c0fc; font-size:13px;'>
      <li>Which countries had the highest youth unemployment in 2023?</li>
      <li>Compare gender unemployment gap in India vs Germany over the last decade.</li>
      <li>What trend do you see in global employment rates post-COVID?</li>
      <li>Which countries improved the most between 2010 and 2025?</li>
    </ul>
    """, unsafe_allow_html=True)

    if not gemini_key:
        st.warning("⚠️ Please enter your Gemini API key in the sidebar to activate the AI agent.")
    else:
        # Build concise data context for the model
        @st.cache_data
        def build_context():
            # Latest year global snapshot
            latest_g = merged_df[
                (merged_df["year"] == merged_df["year"].max()) &
                (merged_df["sex"] == "Total") & (merged_df["age"] == "15+")
            ][["country","unemployment_rate","employment_rate"]].dropna()

            top5_u  = latest_g.nlargest(5,"unemployment_rate")[["country","unemployment_rate"]].to_dict("records")
            bot5_u  = latest_g.nsmallest(5,"unemployment_rate")[["country","unemployment_rate"]].to_dict("records")
            top5_e  = latest_g.nlargest(5,"employment_rate")[["country","employment_rate"]].to_dict("records")

            # Global averages by year
            global_avg = merged_df[
                (merged_df["sex"] == "Total") & (merged_df["age"] == "15+")
            ].groupby("year")[["unemployment_rate","employment_rate"]].mean().round(2).reset_index()
            global_avg_dict = global_avg.to_dict("records")

            # Gender gap latest
            gen_latest = merged_df[
                (merged_df["year"] == merged_df["year"].max()) &
                (merged_df["age"] == "15+") &
                (merged_df["sex"].isin(["Male","Female"]))
            ].groupby("sex")[["unemployment_rate","employment_rate"]].mean().round(2).to_dict()

            # Youth vs adult
            age_latest = merged_df[
                (merged_df["year"] == merged_df["year"].max()) &
                (merged_df["sex"] == "Total") &
                (merged_df["age"].isin(["15-24","25+"]))
            ].groupby("age")[["unemployment_rate"]].mean().round(2).to_dict()

            ctx = {
                "dataset_description": (
                    "ILO Global Labour Market dataset covering unemployment and employment rates "
                    f"for {merged_df['country'].nunique()} countries, years {int(merged_df['year'].min())}"
                    f"–{int(merged_df['year'].max())}, broken down by sex (Total/Male/Female) "
                    "and age group (15+, 15-24, 25+)."
                ),
                "latest_year": int(merged_df["year"].max()),
                "top5_highest_unemployment": top5_u,
                "top5_lowest_unemployment":  bot5_u,
                "top5_highest_employment":   top5_e,
                "global_averages_by_year": global_avg_dict[-10:],  # last 10 years
                "gender_breakdown_latest": gen_latest,
                "youth_vs_adult_unemployment_latest": age_latest,
                "currently_filtered_countries": selected_countries,
            }

            # Per-country stats for selected countries
            country_stats = {}
            for c in selected_countries:
                cdf = merged_df[
                    (merged_df["country"] == c) &
                    (merged_df["sex"] == "Total") &
                    (merged_df["age"] == "15+")
                ].sort_values("year")[["year","unemployment_rate","employment_rate"]]
                country_stats[c] = cdf.tail(10).round(2).to_dict("records")
            ctx["selected_country_recent_stats"] = country_stats

            return json.dumps(ctx, indent=2)

        data_context = build_context()

        # Chat history
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        # Render chat
        chat_html = ""
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                chat_html += f"""
                <div class='user-badge'>You</div>
                <div class='chat-msg-user'>{msg['content']}</div>
                <div class='chat-clearfix'></div>
                """
            else:
                chat_html += f"""
                <div class='ai-badge'>🤖 Gemini AI Analyst</div>
                <div class='chat-msg-ai'>{msg['content']}</div>
                <div class='chat-clearfix'></div>
                """

        if chat_html:
            st.markdown(
                f"<div style='max-height:450px; overflow-y:auto; padding:8px;'>{chat_html}</div>",
                unsafe_allow_html=True
            )

        # Input
        user_q = st.text_input(
            "Ask the AI analyst…",
            placeholder="e.g. Which countries had the highest youth unemployment in 2023?",
            key="ai_input",
            label_visibility="collapsed",
        )

        col_send, col_clear = st.columns([5, 1])
        with col_send:
            send = st.button("Send ➤", use_container_width=True, type="primary")
        with col_clear:
            if st.button("Clear", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()

        if send and user_q.strip():
            with st.spinner("🤖 Analysing data…"):
                try:
                    genai.configure(api_key=gemini_key)
                    model = genai.GenerativeModel("gemini-1.5-flash")

                    system_prompt = f"""You are an expert labour market analyst with deep knowledge of
global employment and unemployment statistics. You have access to the following
dataset summary and statistics:

{data_context}

Guidelines:
- Answer clearly and concisely in natural language
- Use specific numbers from the data when available
- Highlight interesting trends, comparisons, or anomalies
- Structure longer answers with bullet points or short paragraphs
- Always mention the year when citing statistics
- Be insightful and analytical, not just descriptive
"""
                    history = [
                        {"role": m["role"], "parts": [m["content"]]}
                        for m in st.session_state.chat_history
                    ]

                    chat = model.start_chat(history=history)
                    response = chat.send_message(system_prompt + "\n\nUser question: " + user_q)
                    answer = response.text

                    st.session_state.chat_history.append({"role": "user",    "content": user_q})
                    st.session_state.chat_history.append({"role": "model",   "content": answer})
                    st.rerun()

                except Exception as e:
                    st.error(f"Gemini API error: {e}")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<hr style='border-color:#2e3452; margin-top:32px;'>
<p style='color:#3a3f5c; font-size:12px; text-align:center;'>
  Built with Streamlit · Plotly · Google Gemini AI · ILO Global Labour Statistics
</p>
""", unsafe_allow_html=True)
