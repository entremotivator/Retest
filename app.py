import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import folium
from streamlit_folium import folium_static
import io

# Configure page
st.set_page_config(
    page_title="Property Management Dashboard", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f4e79;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f4e79;
    }
    .property-card {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        background-color: #f9f9f9;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .status-active { color: #28a745; font-weight: bold; }
    .status-pending { color: #ffc107; font-weight: bold; }
    .status-sold { color: #dc3545; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'property_data' not in st.session_state:
    # Sample data - in real app, load from CSV
    st.session_state.property_data = pd.DataFrame({
        'id': ['5500-Grand-Lake-Dr'],
        'formattedAddress': ['5500 Grand Lake Dr, San Antonio, TX 78244'],
        'addressLine1': ['5500 Grand Lake Dr'],
        'city': ['San Antonio'],
        'state': ['TX'],
        'zipCode': ['78244'],
        'county': ['Bexar'],
        'latitude': [29.476011],
        'longitude': [-98.351454],
        'propertyType': ['Single Family'],
        'bedrooms': [3],
        'bathrooms': [2],
        'squareFootage': [1878],
        'lotSize': [8843],
        'yearBuilt': [1973],
        'lastSaleDate': ['2017-10-19'],
        'lastSalePrice': [185000],
        'hoa_fee': [175],
        'architectureType': ['Contemporary'],
        'cooling': [True],
        'coolingType': ['Central'],
        'exteriorType': ['Wood'],
        'fireplace': [True],
        'fireplaceType': ['Masonry'],
        'garage': [True],
        'garageSpaces': [2],
        'heating': [True],
        'heatingType': ['Forced Air'],
        'pool': [True],
        'poolType': ['Concrete'],
        'roofType': ['Asphalt'],
        'taxAssessment_2023': [225790],
        'propertyTax_2023': [4201],
        'owner_name': ['Michael Smith'],
        'owner_type': ['Individual'],
        'ownerOccupied': [False],
        'status': ['Active'],
        'rental_rate': [2500],
        'occupancy_rate': [95],
        'maintenance_cost': [3500]
    })

# Function to load CSV data
@st.cache_data
def load_property_data():
    try:
        # Try to read the uploaded CSV
        df = pd.read_csv("property_data.csv")
        return df
    except:
        # Return sample data if file not found
        return st.session_state.property_data

# Load data
df = load_property_data()

# Title and header
st.markdown('<h1 class="main-header">🏡 Property Management Dashboard</h1>', unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.title("🏠 Navigation")
page = st.sidebar.selectbox(
    "Choose a page:",
    ["📊 Dashboard Overview", "🏘️ Property Portfolio", "📈 Analytics", "💰 Financial Reports", "🔧 Property Management", "➕ Add Property"]
)

# File upload section
st.sidebar.markdown("---")
st.sidebar.subheader("📁 Upload Property Data")
uploaded_file = st.sidebar.file_uploader("Upload CSV file", type=['csv'])
if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        st.sidebar.success(f"✅ Loaded {len(df)} properties")
    except Exception as e:
        st.sidebar.error(f"Error loading file: {e}")

# Main content based on selected page
if page == "📊 Dashboard Overview":
    
    # Key Metrics Row
    st.subheader("📈 Key Performance Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_properties = len(df)
        st.metric("Total Properties", total_properties, delta=None)
    
    with col2:
        if 'lastSalePrice' in df.columns:
            avg_value = df['lastSalePrice'].mean()
            st.metric("Avg Property Value", f"${avg_value:,.0f}", delta="↗ 5.2%")
        else:
            st.metric("Avg Property Value", "N/A")
    
    with col3:
        if 'rental_rate' in df.columns:
            monthly_income = df['rental_rate'].sum()
            st.metric("Monthly Income", f"${monthly_income:,.0f}", delta="↗ 3.1%")
        else:
            st.metric("Monthly Income", "N/A")
    
    with col4:
        if 'occupancy_rate' in df.columns:
            avg_occupancy = df['occupancy_rate'].mean()
            st.metric("Occupancy Rate", f"{avg_occupancy:.1f}%", delta="↗ 2.3%")
        else:
            st.metric("Occupancy Rate", "N/A")

    # Charts row
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏘️ Property Types Distribution")
        if 'propertyType' in df.columns:
            prop_type_counts = df['propertyType'].value_counts()
            fig_pie = px.pie(values=prop_type_counts.values, names=prop_type_counts.index)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Property type data not available")
    
    with col2:
        st.subheader("📍 Properties by City")
        if 'city' in df.columns:
            city_counts = df['city'].value_counts().head(10)
            fig_bar = px.bar(x=city_counts.index, y=city_counts.values)
            fig_bar.update_layout(xaxis_title="City", yaxis_title="Number of Properties")
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("City data not available")

    # Property Value Trends
    st.subheader("💹 Property Assessment Trends")
    if all(col in df.columns for col in ['taxAssessment_2019', 'taxAssessment_2020', 'taxAssessment_2021', 'taxAssessment_2022', 'taxAssessment_2023']):
        years = ['2019', '2020', '2021', '2022', '2023']
        avg_assessments = []
        for year in years:
            col_name = f'taxAssessment_{year}'
            if col_name in df.columns:
                avg_assessments.append(df[col_name].mean())
        
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(x=years, y=avg_assessments, mode='lines+markers', name='Avg Assessment'))
        fig_line.update_layout(title="Average Tax Assessment Over Time", xaxis_title="Year", yaxis_title="Assessment Value ($)")
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("Assessment trend data not available")

elif page == "🏘️ Property Portfolio":
    
    st.subheader("🔍 Property Search & Filters")
    
    # Filters in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if 'city' in df.columns:
            cities = ['All'] + sorted(df['city'].dropna().unique().tolist())
            selected_city = st.selectbox("City", cities)
        else:
            selected_city = 'All'
    
    with col2:
        if 'propertyType' in df.columns:
            prop_types = ['All'] + sorted(df['propertyType'].dropna().unique().tolist())
            selected_type = st.selectbox("Property Type", prop_types)
        else:
            selected_type = 'All'
    
    with col3:
        if 'bedrooms' in df.columns:
            min_beds = st.selectbox("Min Bedrooms", [0, 1, 2, 3, 4, 5])
        else:
            min_beds = 0
    
    with col4:
        if 'lastSalePrice' in df.columns:
            min_price, max_price = int(df['lastSalePrice'].min()), int(df['lastSalePrice'].max())
            price_range = st.slider("Price Range", min_price, max_price, (min_price, max_price))
        else:
            price_range = (0, 1000000)

    # Apply filters
    filtered_df = df.copy()
    
    if selected_city != 'All' and 'city' in df.columns:
        filtered_df = filtered_df[filtered_df['city'] == selected_city]
    
    if selected_type != 'All' and 'propertyType' in df.columns:
        filtered_df = filtered_df[filtered_df['propertyType'] == selected_type]
    
    if 'bedrooms' in df.columns:
        filtered_df = filtered_df[filtered_df['bedrooms'] >= min_beds]
    
    if 'lastSalePrice' in df.columns:
        filtered_df = filtered_df[filtered_df['lastSalePrice'].between(price_range[0], price_range[1])]

    st.markdown(f"**Showing {len(filtered_df)} properties**")

    # Display properties
    for idx, row in filtered_df.iterrows():
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"""
                <div class="property-card">
                    <h3>🏠 {row.get('formattedAddress', 'N/A')}</h3>
                    <p><strong>Type:</strong> {row.get('propertyType', 'N/A')} | 
                    <strong>Bedrooms:</strong> {row.get('bedrooms', 'N/A')} | 
                    <strong>Bathrooms:</strong> {row.get('bathrooms', 'N/A')} | 
                    <strong>Sq Ft:</strong> {row.get('squareFootage', 'N/A'):,} | 
                    <strong>Year Built:</strong> {row.get('yearBuilt', 'N/A')}</p>
                    
                    <p><strong>💰 Last Sale:</strong> ${row.get('lastSalePrice', 0):,} | 
                    <strong>Assessment 2023:</strong> ${row.get('taxAssessment_2023', 0):,}</p>
                    
                    <p><strong>📍 Location:</strong> {row.get('city', 'N/A')}, {row.get('state', 'N/A')} | 
                    <strong>County:</strong> {row.get('county', 'N/A')}</p>
                    
                    <p><strong>👤 Owner:</strong> {row.get('owner_name', 'N/A')} | 
                    <strong>Occupied:</strong> {'Yes' if row.get('ownerOccupied', False) else 'No'}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.button("👁️ View Details", key=f"view_{idx}")
                st.button("✏️ Edit", key=f"edit_{idx}")
                st.button("📊 Analytics", key=f"analytics_{idx}")

elif page == "📈 Analytics":
    
    st.subheader("📊 Property Analytics")
    
    # Analytics tabs
    tab1, tab2, tab3, tab4 = st.tabs(["💰 Financial", "📍 Geographic", "🏠 Property Features", "📈 Trends"])
    
    with tab1:
        st.subheader("Financial Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if 'lastSalePrice' in df.columns:
                st.subheader("Price Distribution")
                fig_hist = px.histogram(df, x='lastSalePrice', bins=20)
                st.plotly_chart(fig_hist, use_container_width=True)
            
        with col2:
            if all(col in df.columns for col in ['squareFootage', 'lastSalePrice']):
                st.subheader("Price vs Square Footage")
                fig_scatter = px.scatter(df, x='squareFootage', y='lastSalePrice')
                st.plotly_chart(fig_scatter, use_container_width=True)
    
    with tab2:
        st.subheader("Geographic Distribution")
        
        if 'latitude' in df.columns and 'longitude' in df.columns:
            # Create map
            map_center = [df['latitude'].mean(), df['longitude'].mean()]
            m = folium.Map(location=map_center, zoom_start=10)
            
            for idx, row in df.iterrows():
                folium.Marker(
                    [row['latitude'], row['longitude']],
                    popup=f"{row.get('formattedAddress', 'N/A')}<br>${row.get('lastSalePrice', 0):,}",
                    tooltip=row.get('formattedAddress', 'N/A')
                ).add_to(m)
            
            folium_static(m, width=700, height=500)
        else:
            st.info("Location data not available for mapping")
    
    with tab3:
        st.subheader("Property Features Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if 'bedrooms' in df.columns:
                bedroom_counts = df['bedrooms'].value_counts().sort_index()
                fig_bed = px.bar(x=bedroom_counts.index, y=bedroom_counts.values)
                fig_bed.update_layout(title="Properties by Bedroom Count", xaxis_title="Bedrooms", yaxis_title="Count")
                st.plotly_chart(fig_bed, use_container_width=True)
        
        with col2:
            if 'yearBuilt' in df.columns:
                fig_year = px.histogram(df, x='yearBuilt', bins=20)
                fig_year.update_layout(title="Properties by Year Built")
                st.plotly_chart(fig_year, use_container_width=True)
    
    with tab4:
        st.subheader("Market Trends")
        
        if 'yearBuilt' in df.columns and 'lastSalePrice' in df.columns:
            decade_analysis = df.copy()
            decade_analysis['decade'] = (decade_analysis['yearBuilt'] // 10) * 10
            decade_prices = decade_analysis.groupby('decade')['lastSalePrice'].mean().reset_index()
            
            fig_trend = px.bar(decade_prices, x='decade', y='lastSalePrice')
            fig_trend.update_layout(title="Average Price by Decade Built", xaxis_title="Decade", yaxis_title="Average Price")
            st.plotly_chart(fig_trend, use_container_width=True)

elif page == "💰 Financial Reports":
    
    st.subheader("💼 Financial Dashboard")
    
    # Financial metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if 'lastSalePrice' in df.columns:
            total_value = df['lastSalePrice'].sum()
            st.metric("Total Portfolio Value", f"${total_value:,.0f}")
        
        if 'propertyTax_2023' in df.columns:
            total_tax = df['propertyTax_2023'].sum()
            st.metric("Annual Property Tax", f"${total_tax:,.0f}")
    
    with col2:
        if 'rental_rate' in df.columns:
            monthly_income = df['rental_rate'].sum()
            annual_income = monthly_income * 12
            st.metric("Annual Rental Income", f"${annual_income:,.0f}")
        
        if 'maintenance_cost' in df.columns:
            total_maintenance = df['maintenance_cost'].sum()
            st.metric("Annual Maintenance", f"${total_maintenance:,.0f}")
    
    with col3:
        if all(col in df.columns for col in ['rental_rate', 'maintenance_cost', 'propertyTax_2023']):
            net_income = (df['rental_rate'] * 12) - df['maintenance_cost'] - df['propertyTax_2023']
            total_net = net_income.sum()
            st.metric("Net Annual Income", f"${total_net:,.0f}")

    # Revenue breakdown
    if all(col in df.columns for col in ['rental_rate', 'maintenance_cost', 'propertyTax_2023']):
        st.subheader("📊 Revenue Breakdown")
        
        total_revenue = df['rental_rate'].sum() * 12
        total_maintenance = df['maintenance_cost'].sum()
        total_tax = df['propertyTax_2023'].sum()
        net_profit = total_revenue - total_maintenance - total_tax
        
        categories = ['Gross Revenue', 'Maintenance', 'Property Tax', 'Net Profit']
        values = [total_revenue, -total_maintenance, -total_tax, net_profit]
        colors = ['green', 'red', 'orange', 'blue']
        
        fig_waterfall = go.Figure()
        fig_waterfall.add_trace(go.Bar(x=categories, y=values, marker_color=colors))
        fig_waterfall.update_layout(title="Annual Financial Performance")
        st.plotly_chart(fig_waterfall, use_container_width=True)

elif page == "🔧 Property Management":
    
    st.subheader("🔧 Property Management Tools")
    
    # Management tabs
    tab1, tab2, tab3 = st.tabs(["📋 Tasks", "🔧 Maintenance", "👥 Tenants"])
    
    with tab1:
        st.subheader("Task Management")
        
        # Add new task
        with st.expander("➕ Add New Task"):
            col1, col2 = st.columns(2)
            with col1:
                task_property = st.selectbox("Property", df['formattedAddress'].tolist() if 'formattedAddress' in df.columns else ['No properties'])
                task_type = st.selectbox("Task Type", ["Maintenance", "Inspection", "Showing", "Administrative"])
            with col2:
                task_priority = st.selectbox("Priority", ["Low", "Medium", "High", "Urgent"])
                due_date = st.date_input("Due Date")
            
            task_description = st.text_area("Description")
            if st.button("Add Task"):
                st.success("Task added successfully!")
        
        # Display existing tasks (mock data)
        st.subheader("📋 Current Tasks")
        tasks_data = {
            'Property': ['5500 Grand Lake Dr', '5500 Grand Lake Dr'],
            'Task': ['HVAC Inspection', 'Gutter Cleaning'],
            'Priority': ['Medium', 'Low'],
            'Due Date': ['2025-08-20', '2025-08-25'],
            'Status': ['Pending', 'Scheduled']
        }
        tasks_df = pd.DataFrame(tasks_data)
        st.dataframe(tasks_df, use_container_width=True)
    
    with tab2:
        st.subheader("Maintenance Tracking")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Maintenance Costs by Property")
            if 'maintenance_cost' in df.columns:
                maintenance_data = df[['formattedAddress', 'maintenance_cost']].copy() if 'formattedAddress' in df.columns else pd.DataFrame()
                if not maintenance_data.empty:
                    fig_maint = px.bar(maintenance_data, x='formattedAddress', y='maintenance_cost')
                    st.plotly_chart(fig_maint, use_container_width=True)
        
        with col2:
            st.subheader("Schedule Maintenance")
            property_select = st.selectbox("Select Property", df['formattedAddress'].tolist() if 'formattedAddress' in df.columns else ['No properties'])
            maintenance_type = st.selectbox("Maintenance Type", ["HVAC", "Plumbing", "Electrical", "Roofing", "Painting", "Landscaping"])
            scheduled_date = st.date_input("Schedule Date")
            estimated_cost = st.number_input("Estimated Cost", min_value=0)
            
            if st.button("Schedule Maintenance"):
                st.success("Maintenance scheduled!")
    
    with tab3:
        st.subheader("Tenant Management")
        
        # Mock tenant data
        tenant_data = {
            'Property': ['5500 Grand Lake Dr'],
            'Tenant': ['John & Mary Johnson'],
            'Lease Start': ['2024-01-01'],
            'Lease End': ['2025-12-31'],
            'Monthly Rent': ['$2,500'],
            'Status': ['Active']
        }
        tenant_df = pd.DataFrame(tenant_data)
        st.dataframe(tenant_df, use_container_width=True)
        
        with st.expander("➕ Add New Tenant"):
            col1, col2 = st.columns(2)
            with col1:
                tenant_property = st.selectbox("Property", df['formattedAddress'].tolist() if 'formattedAddress' in df.columns else ['No properties'], key="tenant_prop")
                tenant_name = st.text_input("Tenant Name")
            with col2:
                lease_start = st.date_input("Lease Start")
                lease_end = st.date_input("Lease End")
            
            monthly_rent = st.number_input("Monthly Rent", min_value=0)
            if st.button("Add Tenant"):
                st.success("Tenant added successfully!")

elif page == "➕ Add Property":
    
    st.subheader("➕ Add New Property")
    
    # Property form
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📍 Location Details")
        address = st.text_input("Street Address")
        city = st.text_input("City")
        state = st.selectbox("State", ["TX", "CA", "FL", "NY", "Other"])
        zip_code = st.text_input("ZIP Code")
        
        st.subheader("🏠 Property Details")
        prop_type = st.selectbox("Property Type", ["Single Family", "Condo", "Townhouse", "Multi-Family"])
        bedrooms = st.number_input("Bedrooms", min_value=0, max_value=10)
        bathrooms = st.number_input("Bathrooms", min_value=0.0, max_value=10.0, step=0.5)
        sqft = st.number_input("Square Footage", min_value=0)
        year_built = st.number_input("Year Built", min_value=1800, max_value=2025)
    
    with col2:
        st.subheader("💰 Financial Details")
        purchase_price = st.number_input("Purchase Price", min_value=0)
        rental_rate = st.number_input("Monthly Rental Rate", min_value=0)
        hoa_fee = st.number_input("HOA Fee", min_value=0)
        
        st.subheader("🔧 Features")
        has_garage = st.checkbox("Garage")
        garage_spaces = st.number_input("Garage Spaces", min_value=0) if has_garage else 0
        has_pool = st.checkbox("Pool")
        has_fireplace = st.checkbox("Fireplace")
        cooling_type = st.selectbox("Cooling", ["Central", "Window Units", "None"])
        heating_type = st.selectbox("Heating", ["Forced Air", "Radiant", "Heat Pump", "Other"])
    
    st.subheader("👤 Owner Information")
    col1, col2 = st.columns(2)
    with col1:
        owner_name = st.text_input("Owner Name")
        owner_type = st.selectbox("Owner Type", ["Individual", "LLC", "Corporation", "Trust"])
    with col2:
        owner_occupied = st.checkbox("Owner Occupied")
        owner_address = st.text_area("Owner Mailing Address")
    
    if st.button("Add Property", type="primary"):
        st.success("🎉 Property added successfully!")
        st.balloons()

# Footer
st.markdown("---")
st.markdown("**Property Management Dashboard** | Built with Streamlit")
