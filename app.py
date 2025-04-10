import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
from io import BytesIO

# Page config
st.set_page_config(layout="wide")
st.title("📍 Minnesota County Income vs. Unemployment Explorer")

@st.cache_data
def load_data():
    income_df = pd.read_csv('Household income in minnesota.csv', skiprows=4, nrows=91)
    unemp_df = pd.read_csv('Unemployment in minnesota.csv', skiprows=4, nrows=91)

    income_df = income_df.rename(columns={'County': 'county', 'Value (Dollars)': 'median_income'})
    unemp_df = unemp_df.rename(columns={'County': 'county', 'Value (Percent)': 'unemployment_rate'})

    income_df['county'] = income_df['county'].str.replace(" County", "").str.strip()
    unemp_df['county'] = unemp_df['county'].str.replace(" County", "").str.strip()

    income_df['median_income'] = income_df['median_income'].astype(str).str.replace(',', '')
    unemp_df['unemployment_rate'] = unemp_df['unemployment_rate'].astype(str)

    combined_df = pd.merge(income_df[['county', 'median_income']],
                           unemp_df[['county', 'unemployment_rate']],
                           on='county')

    combined_df['median_income'] = pd.to_numeric(combined_df['median_income'], errors='coerce').astype(float)
    combined_df['unemployment_rate'] = pd.to_numeric(combined_df['unemployment_rate'], errors='coerce').astype(float)

    counties = gpd.read_file("shapefiles/cb_2022_us_county_20m.shp")
    mn_counties = counties[counties['STATEFP'] == '27'].copy()
    mn_counties['county'] = mn_counties['NAME'].str.strip()

    gdf = mn_counties.merge(combined_df, on='county')
    gdf = gdf.to_crs("EPSG:4326")
    gdf["county_display"] = gdf["county"]

    return gdf

gdf = load_data()
geojson = gdf.__geo_interface__

income_min, income_max = gdf['median_income'].min(), gdf['median_income'].max()
unemp_min, unemp_max = gdf['unemployment_rate'].min(), gdf['unemployment_rate'].max()
all_counties = sorted(gdf['county_display'].unique().tolist())

# Sidebar Filters
st.sidebar.markdown("### 🎯 County Filters")

with st.sidebar.expander("💰 Median Income Map Filters", expanded=True):
    select_all_income = st.button("Select All (Income)")
    unselect_all_income = st.button("Unselect All (Income)")

    if "selected_income_counties" not in st.session_state:
        st.session_state.selected_income_counties = all_counties

    if select_all_income:
        st.session_state.selected_income_counties = all_counties
    if unselect_all_income:
        st.session_state.selected_income_counties = []

    selected_income = st.multiselect(
        "Select Counties (Income):",
        options=all_counties,
        default=st.session_state.selected_income_counties,
        key="income_dropdown"
    )

with st.sidebar.expander("📉 Unemployment Map Filters", expanded=True):
    select_all_unemp = st.button("Select All (Unemp)")
    unselect_all_unemp = st.button("Unselect All (Unemp)")

    if "selected_unemp_counties" not in st.session_state:
        st.session_state.selected_unemp_counties = all_counties

    if select_all_unemp:
        st.session_state.selected_unemp_counties = all_counties
    if unselect_all_unemp:
        st.session_state.selected_unemp_counties = []

    selected_unemp = st.multiselect(
        "Select Counties (Unemp):",
        options=all_counties,
        default=st.session_state.selected_unemp_counties,
        key="unemp_dropdown"
    )

# Filter separately
income_df = gdf[gdf['county_display'].isin(selected_income)]
unemp_df = gdf[gdf['county_display'].isin(selected_unemp)]

# Layout
col1, col2 = st.columns(2)

with col1:
    st.subheader("💰 Median Household Income Heatmap")
    fig_income = px.choropleth(
        income_df,
        geojson=geojson,
        locations="NAME",
        featureidkey="properties.NAME",
        color="median_income",
        hover_data={
            "county_display": True,
            "median_income": True,
            "unemployment_rate": True,
            "NAME": False
        },
        color_continuous_scale="Reds",
        range_color=[income_min, income_max],
        title="Median Income by County"
    )
    fig_income.update_traces(marker_line_color="rgba(0,0,0,0.2)", marker_line_width=0.5)
    fig_income.update_geos(fitbounds="locations", visible=False)
    fig_income.update_layout(
        height=700,
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        geo=dict(bgcolor='rgba(0,0,0,0)'),
        legend=dict(bgcolor='rgba(0,0,0,0)')
    )
    st.plotly_chart(fig_income, use_container_width=True)

with col2:
    st.subheader("📉 Unemployment Rate")
    fig_unemp = px.choropleth(
        unemp_df,
        geojson=geojson,
        locations="NAME",
        featureidkey="properties.NAME",
        color="unemployment_rate",
        hover_data={
            "county_display": True,
            "median_income": True,
            "unemployment_rate": True,
            "NAME": False
        },
        color_continuous_scale="Reds",
        range_color=[unemp_min, unemp_max],
        title="Unemployment Rate by County"
    )
    fig_unemp.update_traces(marker_line_color="rgba(0,0,0,0.2)", marker_line_width=0.5)
    fig_unemp.update_geos(fitbounds="locations", visible=False)
    fig_unemp.update_layout(
        height=700,
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        geo=dict(bgcolor='rgba(0,0,0,0)'),
        legend=dict(bgcolor='rgba(0,0,0,0)')
    )
    st.plotly_chart(fig_unemp, use_container_width=True)

# Bar charts
if income_df.shape[0] > 0:
    st.subheader("💰 Median Household Income Comparison")
    st.bar_chart(income_df.set_index('county_display')[['median_income']])

if unemp_df.shape[0] > 0:
    st.subheader("📉 Unemployment Rate Comparison")
    st.bar_chart(unemp_df.set_index('county_display')[['unemployment_rate']])

# CSV/Excel export section
st.sidebar.markdown("### 📤 Export Selected Data")

export_option = st.sidebar.radio(
    "Choose what to export:",
    ["Median Income", "Unemployment Rate", "Both"],
    index=2
)

# Build export DataFrame
if export_option == "Median Income":
    export_df = income_df[["county_display", "median_income"]].rename(columns={"county_display": "County"})
elif export_option == "Unemployment Rate":
    export_df = unemp_df[["county_display", "unemployment_rate"]].rename(columns={"county_display": "County"})
else:
    export_df = pd.merge(
        income_df[["county_display", "median_income"]],
        unemp_df[["county_display", "unemployment_rate"]],
        on="county_display",
        how="outer"
    ).rename(columns={"county_display": "County"})

# Download Buttons
if not export_df.empty:
    st.sidebar.download_button(
        label="📥 Download CSV",
        data=export_df.to_csv(index=False),
        file_name="mn_selected_data.csv",
        mime="text/csv"
    )

    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
        export_df.to_excel(writer, index=False, sheet_name='Selected Data')
    excel_data = excel_buffer.getvalue()

    st.sidebar.download_button(
        label="📊 Download Excel",
        data=excel_data,
        file_name="mn_selected_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
