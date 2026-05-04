import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Page Configuration
st.set_page_config(page_title="NYC 311 Dashboard", page_icon="🗽", layout="wide")

# Data Loading and Cleaning
@st.cache_data # Cache data so CSV doesn't need to reload on every interaction
def load_data():
    # Data Loading
    filepath = "311_Service_Requests_from_2020_to_Present_20260401.csv"
    usecols = [
        'Unique Key', 'Created Date', 'Closed Date', 'Agency', 'Agency Name', 
        'Problem (formerly Complaint Type)', 'Problem Detail (formerly Descriptor)', 
        'Location Type', 'Incident Zip', 'Borough', 'Status', 'Latitude', 'Longitude'
    ]
    df = pd.read_csv(filepath, usecols=usecols, low_memory=False, nrows=5000000)
    
    # Data Cleaning
    df['Created Date'] = pd.to_datetime(df['Created Date'], errors='coerce')
    df['Closed Date'] = pd.to_datetime(df['Closed Date'], errors='coerce')
    df['Incident Zip'] = df['Incident Zip'].astype(str).str[:5]
    df['Incident Zip'] = df['Incident Zip'].replace('nan', np.nan)
    df['Borough'] = df['Borough'].replace('Unspecified', np.nan)
    df.dropna(subset=['Created Date', 'Problem (formerly Complaint Type)'], inplace=True)
    df.drop_duplicates(inplace=True)
    
    # Feature Engineering
    df['ResolutionTimeHours'] = (df['Closed Date'] - df['Created Date']).dt.total_seconds() / 3600
    df = df[(df['ResolutionTimeHours'] >= 0) | (df['ResolutionTimeHours'].isna())]

    df['Created Month'] = df['Created Date'].dt.month
    df['Created Year'] = df['Created Date'].dt.year
    df['Day of Week'] = df['Created Date'].dt.day_name()
    
    bins = [-1, 24, 72, 168, 8760, float('inf')]
    labels = ['< 1 Day', '1-3 Days', '3-7 Days', '1 Week - 1 Year', '> 1 Year']
    df['ResolutionCategory'] = pd.cut(df['ResolutionTimeHours'], bins=bins, labels=labels)
    
    # Rename Problem column for ease of use
    df.rename(columns={'Problem (formerly Complaint Type)': 'Complaint Type'}, inplace=True)
    
    return df

# Main App UI
st.title("🗽 NYC 311 Service Requests Dashboard")
st.markdown("Explore millions of 311 complaints across New York City. Use the sidebar to filter data by Borough.")

# Execute data loading, cleaning, and feature engineering
with st.spinner("Loading and cleaning data... (This may take a minute)"):
    raw_df = load_data()

# Set up side bar
st.sidebar.header("Global Filters")

# Allow filtering by borough to explore location-based insights
boroughs = raw_df['Borough'].dropna().unique().tolist()
borough_options = ["All Boroughs"] + sorted(boroughs)
selected_borough = st.sidebar.selectbox("Select Borough", options=borough_options)

# Apply Borough Filter
if selected_borough != "All Boroughs":
    filtered_df = raw_df[raw_df['Borough'] == selected_borough]
else:
    filtered_df = raw_df

if filtered_df.empty:
    st.warning("No data matches your filter criteria. Please adjust your sidebar filters.")
    st.stop()

# Helper lists for visualizations
top_10_complaints = filtered_df['Complaint Type'].value_counts().head(10).index
top_10_agencies = filtered_df['Agency'].value_counts().head(10).index

# Setup different views/tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "Overview & Categories", 
    "Temporal Trends", 
    "Agency & Resolution Equity", 
    "Geospatial & Heatmaps"
])

# ==========================================
# TAB 1: OVERVIEW & CATEGORIES
# ==========================================
with tab1:
    st.header("Overview & Categories")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Complaints", f"{len(filtered_df):,}")
    col2.metric("Median Resolution Time", f"{filtered_df['ResolutionTimeHours'].median():.1f} hrs")
    col3.metric("Top Complaint Type", filtered_df['Complaint Type'].mode()[0])
    col4.metric("Top Agency", filtered_df['Agency'].mode()[0] if not filtered_df['Agency'].empty else "N/A")
    
    st.markdown("---")
    
    # Viz 1: Top 20 Complaints
    st.subheader("1. Top 20 Most Frequent Complaints")
    top_20 = filtered_df['Complaint Type'].value_counts().head(20).reset_index()
    top_20.columns = ['Complaint Type', 'Count']
    fig1 = px.bar(top_20, x='Count', y='Complaint Type', orientation='h', color='Count', color_continuous_scale='viridis')
    fig1.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig1, width="stretch")
    
    # Viz 2: Borough counts
    st.subheader("2. Total 311 Requests by Borough")
    boro_counts = filtered_df['Borough'].value_counts().reset_index()
    boro_counts.columns = ['Borough', 'Count']
    fig2 = px.bar(boro_counts, x='Count', y='Borough', orientation='h', color='Count', color_continuous_scale='magma')
    fig2.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig2, width="stretch")

    # Viz 3: Resolution Category
    st.subheader("3. Percentage of Complaints by Resolution Time Category")
    res_counts = (filtered_df['ResolutionCategory'].value_counts(normalize=True) * 100).reset_index()
    res_counts.columns = ['Category', 'Percentage']
    fig3 = px.bar(res_counts, x='Category', y='Percentage', color='Category', color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(fig3, width="stretch")

# ==========================================
# TAB 2: TEMPORAL TRENDS
# ==========================================
with tab2:
    st.header("Temporal Trends")
    
    # Viz 4: Monthly Trend
    st.subheader("4. Monthly Trend of 311 Complaints Over Time")
    trend_df = filtered_df.set_index('Created Date').resample('ME').size().reset_index(name='Count')
    fig4 = px.line(trend_df, x='Created Date', y='Count', markers=True)
    fig4.update_traces(line_color="dodgerblue", line_width=3)
    st.plotly_chart(fig4, width="stretch")

    # Viz 5: Heatmap by Month
    st.subheader("5. Heatmap: Top Complaints by Month (Seasonality)")
    df_top_comp = filtered_df[filtered_df['Complaint Type'].isin(top_10_complaints)]
    if not df_top_comp.empty:
        monthly_comp = df_top_comp.groupby(['Created Month', 'Complaint Type']).size().reset_index(name='Count')
        fig5 = px.density_heatmap(monthly_comp, x='Created Month', y='Complaint Type', z='Count', histfunc='sum', color_continuous_scale='ylorrd')
        fig5.update_layout(xaxis=dict(tickmode='array', tickvals=list(range(1,13)), ticktext=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']))
        st.plotly_chart(fig5, width="stretch")

    # Viz 5b: Heatmap by Day of Week
    st.subheader("5b. Heatmap: Top Complaints by Day of the Week")
    if not df_top_comp.empty:
        day_comp = df_top_comp.groupby(['Day of Week', 'Complaint Type']).size().reset_index(name='Count')
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        fig5b = px.density_heatmap(
            day_comp, 
            x='Day of Week', 
            y='Complaint Type', 
            z='Count', 
            histfunc='sum', 
            color_continuous_scale='ylorrd',
            category_orders={'Day of Week': day_order}
        )
        st.plotly_chart(fig5b, width="stretch")

# ==========================================
# TAB 3: AGENCY & RESOLUTION EQUITY
# ==========================================
with tab3:
    st.header("Agency Performance & Resolution Equity")
    
    # Viz 6: Top Agencies
    st.subheader("6. Agencies by 311 Complaint Volume")
    agencies_counts = filtered_df['Agency'].value_counts().reset_index()
    agencies_counts.columns = ['Agency', 'Count']
    fig6 = px.bar(agencies_counts, x='Agency', y='Count', color='Count', color_continuous_scale='teal')
    st.plotly_chart(fig6, width="stretch")

    # Prepare resolution df 
    res_df = filtered_df.dropna(subset=['ResolutionTimeHours']).copy()
    if len(res_df) > 100000: # Sample to prevent plotly from crashing
        res_df = res_df.sample(n=100000, random_state=42)
    res_df['LogResolutionTime'] = np.log10(res_df['ResolutionTimeHours'] + 1)
    
    # Viz 7: Res Time by Agency
    st.subheader("7. Resolution Time by Top 10 Agencies (Log Scale)")
    df_top_agencies = res_df[res_df['Agency'].isin(top_10_agencies)]
    if not df_top_agencies.empty:
        agency_order = df_top_agencies.groupby('Agency')['ResolutionTimeHours'].median().sort_values().index.tolist()
        fig7 = px.box(df_top_agencies, x='Agency', y='LogResolutionTime', color='Agency', category_orders={'Agency': agency_order})
        st.plotly_chart(fig7, width="stretch")

    # Viz 8: Res Time by Complaint
    st.subheader("8. Resolution Time for Top 10 Complaints (Log Scale)")
    df_top_complaints_res = res_df[res_df['Complaint Type'].isin(top_10_complaints)]
    if not df_top_complaints_res.empty:
        comp_order = df_top_complaints_res.groupby('Complaint Type')['ResolutionTimeHours'].median().sort_values().index.tolist()
        fig8 = px.box(df_top_complaints_res, x='LogResolutionTime', y='Complaint Type', color='Complaint Type', orientation='h', category_orders={'Complaint Type': comp_order})
        st.plotly_chart(fig8, width="stretch")

    # Viz 9: Res Time by Borough
    st.subheader("9. Distribution of Resolution Time by Borough (Log Scale)")
    if not res_df.empty:
        boro_order = res_df.groupby('Borough')['ResolutionTimeHours'].median().sort_values().index.tolist()
        fig9 = px.box(res_df, x='Borough', y='LogResolutionTime', color='Borough', category_orders={'Borough': boro_order})
        st.plotly_chart(fig9, width="stretch")

# ==========================================
# TAB 4: GEOSPATIAL & HEATMAPS
# ==========================================
with tab4:
    st.header("Geospatial & Heatmaps")

    # Viz 10: Heatmap Complaints Across Boroughs
    st.subheader("10. Heatmap: Top Complaints Across NYC Boroughs")
    df_top2 = filtered_df[filtered_df['Complaint Type'].isin(top_10_complaints)]
    if not df_top2.empty:
        boro_comp = df_top2.groupby(['Borough', 'Complaint Type']).size().reset_index(name='Count')
        fig10 = px.density_heatmap(boro_comp, x='Complaint Type', y='Borough', z='Count', histfunc='sum', color_continuous_scale='ylgnbu')
        st.plotly_chart(fig10, width="stretch")
    
    # Viz 11: Correlation
    st.subheader("11. Correlation Matrix of Temporal/Geospatial Features")
    corr_cols = ['Latitude', 'Longitude', 'Created Month', 'ResolutionTimeHours']
    corr_data = filtered_df[corr_cols].dropna().corr()
    # Replace NaNs with 0 in correlation matrix to avoid Plotly errors if variance is 0
    corr_data = corr_data.fillna(0)
    fig11 = px.imshow(corr_data, text_auto=".2f", color_continuous_scale='rdbu', zmin=-1, zmax=1)
    st.plotly_chart(fig11, width="stretch")

    # Viz 12: Geospatial Scatter
    st.subheader("12. Geographic Distribution of Complaints (Sampled)")
    geo_df = filtered_df.dropna(subset=['Latitude', 'Longitude']).sample(n=min(10000, len(filtered_df)), random_state=42)
    if not geo_df.empty:
        fig12 = px.scatter_mapbox(
            geo_df, 
            lat="Latitude", 
            lon="Longitude", 
            color="Complaint Type",
            hover_data=["Agency", "Borough"],
            zoom=9, 
            height=600
        )
        fig12.update_layout(mapbox_style="carto-positron", margin={"r":0,"t":40,"l":0,"b":0})
        st.plotly_chart(fig12, width="stretch")
