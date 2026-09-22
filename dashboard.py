"""
dashboard.py
------------
Live interactive dashboard comparing entrepreneur onboarding performance
across South African cities, for the FNB e-Identity Services funnel:

  Digital ID -> CIPC Registration -> Funding Request -> Funded

Run with:
    streamlit run dashboard.py

Then it opens automatically in your browser -- fully interactive, live.
"""

import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="e-Identity Services Dashboard", layout="wide")

# ---------- Load data ----------
# Later: swap this for a live database query, e.g. pd.read_sql(..., engine)
@st.cache_data
def load_data():
    df = pd.read_csv("fake_signups.csv", parse_dates=["Date"])
    return df

df = load_data()

st.title("🇿🇦 FNB e-Identity Services — City Performance Dashboard")
st.caption("Tracking entrepreneur onboarding from Digital ID through to Funding, by city")

# ---------- Filters ----------
col1, col2 = st.columns(2)
with col1:
    date_range = st.date_input(
        "Date range",
        value=(df["Date"].min().date(), df["Date"].max().date()),
    )
with col2:
    selected_cities = st.multiselect(
        "Cities (leave empty for all)",
        options=sorted(df["City"].unique()),
    )

filtered = df[(df["Date"].dt.date >= date_range[0]) & (df["Date"].dt.date <= date_range[1])]
if selected_cities:
    filtered = filtered[filtered["City"].isin(selected_cities)]

# ---------- Top-line KPIs ----------
total_signups = len(filtered)
cipc_rate = filtered["CIPCRegistered"].mean() * 100 if total_signups else 0
funding_rate = filtered["FundingRequested"].mean() * 100 if total_signups else 0
funded_rate = filtered["Funded"].mean() * 100 if total_signups else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Signups", f"{total_signups:,}")
k2.metric("CIPC Registration Rate", f"{cipc_rate:.1f}%")
k3.metric("Funding Request Rate", f"{funding_rate:.1f}%")
k4.metric("Funded Rate", f"{funded_rate:.1f}%")

st.divider()

# ---------- City comparison table ----------
st.subheader("City Performance Comparison")

city_stats = filtered.groupby("City").agg(
    Signups=("SignupID", "count"),
    CIPC_Rate=("CIPCRegistered", "mean"),
    Funding_Rate=("FundingRequested", "mean"),
    Funded_Rate=("Funded", "mean"),
    Lat=("Lat", "first"),
    Lon=("Lon", "first"),
).reset_index()

city_stats["CIPC_Rate"] = (city_stats["CIPC_Rate"] * 100).round(1)
city_stats["Funding_Rate"] = (city_stats["Funding_Rate"] * 100).round(1)
city_stats["Funded_Rate"] = (city_stats["Funded_Rate"] * 100).round(1)
city_stats = city_stats.sort_values("Funded_Rate", ascending=False)

# The "gap" -- how far behind each city is from the top performer
if not city_stats.empty:
    top_rate = city_stats["Funded_Rate"].max()
    city_stats["Gap Behind Leader (pts)"] = (top_rate - city_stats["Funded_Rate"]).round(1)

st.dataframe(
    city_stats[["City", "Signups", "CIPC_Rate", "Funding_Rate", "Funded_Rate", "Gap Behind Leader (pts)"]],
    use_container_width=True,
    hide_index=True,
)

# ---------- Map view ----------
st.subheader("Geographic View — Funded Rate by City")
if not city_stats.empty:
    fig_map = px.scatter_map(
        city_stats,
        lat="Lat", lon="Lon",
        size="Signups",
        color="Funded_Rate",
        color_continuous_scale="RdYlGn",
        hover_name="City",
        hover_data={"Signups": True, "Funded_Rate": True, "Lat": False, "Lon": False},
        zoom=4.3,
        map_style="carto-positron",
        title="Bubble size = signup volume, color = funded rate",
    )
    fig_map.update_layout(margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig_map, use_container_width=True)

# ---------- Trend over time ----------
st.subheader("Signup Trend Over Time, by City")
trend = filtered.groupby([pd.Grouper(key="Date", freq="W"), "City"]).size().reset_index(name="Signups")
if not trend.empty:
    fig_trend = px.line(trend, x="Date", y="Signups", color="City")
    st.plotly_chart(fig_trend, use_container_width=True)

# ---------- Funnel drop-off ----------
st.subheader("Where Is the Biggest Drop-off? (Funnel by City)")
funnel_data = []
for city in city_stats["City"]:
    city_df = filtered[filtered["City"] == city]
    funnel_data.append({
        "City": city,
        "Digital ID": len(city_df),
        "CIPC Registered": city_df["CIPCRegistered"].sum(),
        "Funding Requested": city_df["FundingRequested"].sum(),
        "Funded": city_df["Funded"].sum(),
    })
funnel_df = pd.DataFrame(funnel_data)

if not funnel_df.empty:
    funnel_melted = funnel_df.melt(id_vars="City", var_name="Stage", value_name="Count")
    stage_order = ["Digital ID", "CIPC Registered", "Funding Requested", "Funded"]
    funnel_melted["Stage"] = pd.Categorical(funnel_melted["Stage"], categories=stage_order, ordered=True)
    fig_funnel = px.bar(
        funnel_melted, x="City", y="Count", color="Stage",
        barmode="group", category_orders={"Stage": stage_order},
    )
    st.plotly_chart(fig_funnel, use_container_width=True)

st.caption("Data is currently simulated. Swap load_data() for a live database query when real signup data is available.")
