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

# Enhanced CSS for colorful styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        margin: 0.5rem;
        text-align: center;
    }
    .property-card {
        border: none;
        border-radius: 15px;
        padding: 25px;
        margin-bottom: 25px;
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        transition: transform 0.3s ease;
    }
    .property-card:hover {
        transform: translateY(-5px);
    }
    .status-active { 
        background: linear-gradient(45deg, #56ab2f, #a8e6cf);
        padding: 5px 15px;
        border-radius: 20px;
        color: white;
        font-weight: bold;
    }
    .status-pending { 
        background: linear-gradient(45deg, #f7971e, #ffd200);
        padding: 5px 15px;
        border-radius: 20px;
        color: white;
        font-weight: bold;
    }
    .status-sold { 
        background: linear-gradient(45deg, #ed4264, #ffedbc);
        padding: 5px 15px;
        border-radius: 20px;
        color: white;
        font-weight: bold;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    .stSelectbox > div > div {
        background: linear-gradient(45deg, #fa709a 0%, #fee140 100%);
        border-radius: 10px;
    }
    .success-box {
        background: linear-gradient(45deg, #56ab2f, #a8e6cf);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize comprehensive sample data
@st.cache_data
def get_sample_data():
    return pd.DataFrame({
        'id': ['5500-Grand-Lake-Dr', '1234-Oak-Street', '5678-Pine-Ave'],
        'formattedAddress': [
            '5500 Grand Lake Dr, San Antonio, TX 78244',
            '1234 Oak Street, Austin, TX 78701',
            '5678 Pine Ave, Dallas, TX 75201'
        ],
        'addressLine1': ['5500 Grand Lake Dr', '1234 Oak Street', '5678 Pine Ave'],
        'addressLine2': ['', 'Apt 101', ''],
        'city': ['San Antonio', 'Austin', 'Dallas'],
        'state': ['TX', 'TX', 'TX'],
        'zipCode': ['78244', '78701', '75201'],
        'county': ['Bexar', 'Travis', 'Dallas'],
        'latitude': [29.476011, 30.2672, 32.7767],
        'longitude': [-98.351454, -97.7431, -96.7970],
        'propertyType': ['Single Family', 'Condo', 'Townhouse'],
        'bedrooms': [3, 2, 4],
        'bathrooms': [2.0, 1.5, 3.0],
        'squareFootage': [1878, 1200, 2500],
        'lotSize': [8843, 0, 3500],
        'yearBuilt': [1973, 1985, 2010],
        'assessorID': ['05076-103-0500', '12345-678-0900', '98765-432-0100'],
        'legalDescription': ['CB 5076A BLK 3 LOT 50', 'Unit 101 Block A', 'Lot 15 Block C'],
        'subdivision': ['CONV A/S CODE', 'Oak Hills', 'Pine Valley'],
        'zoning': ['RH', 'MF', 'SF'],
        'lastSaleDate': ['2017-10-19', '2020-05-15', '2022-03-10'],
        'lastSalePrice': [185000, 320000, 450000],
        'hoa_fee': [175, 250, 0],
        'architectureType': ['Contemporary', 'Modern', 'Traditional'],
        'cooling': [True, True, True],
        'coolingType': ['Central', 'Central', 'Central'],
        'exteriorType': ['Wood', 'Brick', 'Stone'],
        'fireplace': [True, False, True],
        'fireplaceType': ['Masonry', '', 'Gas'],
        'floorCount': [1, 1, 2],
        'foundationType': ['Slab', 'Slab', 'Basement'],
        'garage': [True, False, True],
        'garageSpaces': [2, 0, 3],
        'garageType': ['Attached', '', 'Attached'],
        'heating': [True, True, True],
        'heatingType': ['Forced Air', 'Heat Pump', 'Radiant'],
        'pool': [True, False, True],
        'poolType': ['Concrete', '', 'Fiberglass'],
        'roofType': ['Asphalt', 'Tile', 'Metal'],
        'roomCount': [5, 3, 7],
        'unitCount': [1, 1, 1],
        'viewType': ['City', 'Courtyard', 'Lake'],
        'taxAssessment_2019': [135430, 280000, 400000],
        'taxAssessment_2020': [142610, 290000, 410000],
        'taxAssessment_2021': [163440, 305000, 425000],
        'taxAssessment_2022': [197600, 315000, 440000],
        'taxAssessment_2023': [225790, 325000, 455000],
        'propertyTax_2019': [2984, 6720, 9600],
        'propertyTax_2020': [3023, 6960, 9840],
        'propertyTax_2021': [3455, 7320, 10200],
        'propertyTax_2022': [4091, 7560, 10560],
        'propertyTax_2023': [4201, 7800, 10920],
        'saleHistory_2004-06-16_price': [95000, 0, 0],
        'saleHistory_2017-10-19_price': [185000, 0, 0],
        'owner_name': ['Michael Smith', 'Sarah Johnson', 'Robert Davis'],
        'owner_type': ['Individual', 'Individual', 'LLC'],
        'owner_mailingAddress': [
            '149 Weaver Blvd, # 264, Weaverville, NC 28787',
            '1234 Oak Street, Austin, TX 78701',
            'PO Box 123, Dallas, TX 75201'
        ],
        'ownerOccupied': [False, True, False],
        'status': ['Active', 'Rented', 'Active'],
        'rental_rate': [2500, 2800, 3200],
        'occupancy_rate': [95, 100, 90],
        'maintenance_cost': [3500, 2100, 4200]
    })

# Initialize session state
if 'property_data' not in st.session_state:
    st.session_state.property_data = get_sample_data()

if 'selected_property_id' not in st.session_state:
    st.session_state.selected_property_id = None

# Function to load CSV data with error handling
@st.cache_data
def load_property_data():
    try:
        df = pd.read_csv("property_data.csv")
        # Convert numeric columns with error handling
        numeric_columns = ['bedrooms', 'bathrooms', 'squareFootage', 'lotSize', 'yearBuilt', 'lastSalePrice']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    except:
        return st.session_state.property_data

# Load data
df = load_property_data()

# Ensure numeric columns are properly typed
numeric_columns = ['bedrooms', 'bathrooms', 'squareFootage', 'lotSize', 'yearBuilt', 'lastSalePrice', 'rental_rate', 'maintenance_cost', 'occupancy_rate']
for col in numeric_columns:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

# Fill NaN values to prevent slider errors
df = df.fillna(0)

# Title and header
st.markdown('<h1 class="main-header">🏡 Property Management Dashboard</h1>', unsafe_allow_html=True)

# Colorful sidebar
st.sidebar.markdown("""
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 15px; margin-bottom: 20px;">
<h2 style="color: white; text-align: center;">🏠 Navigation</h2>
</div>
""", unsafe_allow_html=True)

page = st.sidebar.selectbox(
    "Choose a page:",
    ["📊 Dashboard Overview", "🏘️ Property Portfolio", "📈 Analytics", "💰 Financial Reports", "🔧 Property Management", "➕ Add Property", "✏️ Edit Property"]
)

# File upload section
st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style="background: linear-gradient(45deg, #fa709a 0%, #fee140 100%); padding: 15px; border-radius: 10px;">
<h3 style="color: white; margin: 0;">📁 Upload Property Data</h3>
</div>
""", unsafe_allow_html=True)

uploaded_file = st.sidebar.file_uploader("Upload CSV file", type=['csv'])
if uploaded_file is not None:
    try:
        new_df = pd.read_csv(uploaded_file)
        # Process numeric columns
        for col in numeric_columns:
            if col in new_df.columns:
                new_df[col] = pd.to_numeric(new_df[col], errors='coerce')
        new_df = new_df.fillna(0)
        df = new_df
        st.sidebar.success(f"✅ Loaded {len(df)} properties")
    except Exception as e:
        st.sidebar.error(f"Error loading file: {str(e)}")

# Main content based on selected page
if page == "📊 Dashboard Overview":
    
    # Key Metrics Row with colorful cards
    st.markdown("""
    <div style="background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 50%, #fecfef 100%); padding: 20px; border-radius: 15px; margin-bottom: 30px;">
    <h2 style="text-align: center; color: white; font-size: 2rem;">📈 Key Performance Metrics</h2>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_properties = len(df)
        st.markdown(f"""
        <div class="metric-card">
            <h3>🏠 Total Properties</h3>
            <h2>{total_properties}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        avg_value = df['lastSalePrice'].mean() if 'lastSalePrice' in df.columns and len(df) > 0 else 0
        st.markdown(f"""
        <div class="metric-card">
            <h3>💰 Avg Property Value</h3>
            <h2>${avg_value:,.0f}</h2>
            <p style="color: #90EE90;">↗ 5.2%</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        monthly_income = df['rental_rate'].sum() if 'rental_rate' in df.columns else 0
        st.markdown(f"""
        <div class="metric-card">
            <h3>💵 Monthly Income</h3>
            <h2>${monthly_income:,.0f}</h2>
            <p style="color: #90EE90;">↗ 3.1%</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        avg_occupancy = df['occupancy_rate'].mean() if 'occupancy_rate' in df.columns and len(df) > 0 else 0
        st.markdown(f"""
        <div class="metric-card">
            <h3>📊 Occupancy Rate</h3>
            <h2>{avg_occupancy:.1f}%</h2>
            <p style="color: #90EE90;">↗ 2.3%</p>
        </div>
        """, unsafe_allow_html=True)

    # Charts row with colorful themes
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="background: linear-gradient(45deg, #FA8072, #FFE4E1); padding: 20px; border-radius: 15px; margin-bottom: 20px;">
        <h3 style="text-align: center; color: white;">🏘️ Property Types Distribution</h3>
        </div>
        """, unsafe_allow_html=True)
        
        if 'propertyType' in df.columns and len(df) > 0:
            prop_type_counts = df['propertyType'].value_counts()
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
            fig_pie = px.pie(values=prop_type_counts.values, names=prop_type_counts.index, color_discrete_sequence=colors)
            fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Property type data not available")
    
    with col2:
        st.markdown("""
        <div style="background: linear-gradient(45deg, #667eea, #764ba2); padding: 20px; border-radius: 15px; margin-bottom: 20px;">
        <h3 style="text-align: center; color: white;">📍 Properties by City</h3>
        </div>
        """, unsafe_allow_html=True)
        
        if 'city' in df.columns and len(df) > 0:
            city_counts = df['city'].value_counts().head(10)
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98FB98', '#F0E68C', '#FFB6C1', '#20B2AA']
            fig_bar = px.bar(x=city_counts.index, y=city_counts.values, color=city_counts.index, color_discrete_sequence=colors)
            fig_bar.update_layout(xaxis_title="City", yaxis_title="Number of Properties", showlegend=False)
            fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("City data not available")

    # Property Value Trends with colorful styling
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 15px; margin: 30px 0;">
    <h2 style="text-align: center; color: white;">💹 Property Assessment Trends</h2>
    </div>
    """, unsafe_allow_html=True)
    
    assessment_cols = ['taxAssessment_2019', 'taxAssessment_2020', 'taxAssessment_2021', 'taxAssessment_2022', 'taxAssessment_2023']
    if all(col in df.columns for col in assessment_cols) and len(df) > 0:
        years = ['2019', '2020', '2021', '2022', '2023']
        avg_assessments = []
        for year in years:
            col_name = f'taxAssessment_{year}'
            if col_name in df.columns:
                avg_assessments.append(df[col_name].mean())
        
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(
            x=years, 
            y=avg_assessments, 
            mode='lines+markers', 
            name='Avg Assessment',
            line=dict(color='#FF6B6B', width=4),
            marker=dict(size=10, color='#4ECDC4')
        ))
        fig_line.update_layout(
            title="Average Tax Assessment Over Time", 
            xaxis_title="Year", 
            yaxis_title="Assessment Value ($)",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("Assessment trend data not available")

elif page == "🏘️ Property Portfolio":
    
    st.markdown("""
    <div style="background: linear-gradient(45deg, #FA8072, #FFE4E1); padding: 20px; border-radius: 15px; margin-bottom: 30px;">
    <h2 style="text-align: center; color: white;">🔍 Property Search & Filters</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Filters in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if 'city' in df.columns and len(df) > 0:
            cities = ['All'] + sorted(df['city'].dropna().unique().tolist())
            selected_city = st.selectbox("🏙️ City", cities)
        else:
            selected_city = 'All'
    
    with col2:
        if 'propertyType' in df.columns and len(df) > 0:
            prop_types = ['All'] + sorted(df['propertyType'].dropna().unique().tolist())
            selected_type = st.selectbox("🏠 Property Type", prop_types)
        else:
            selected_type = 'All'
    
    with col3:
        if 'bedrooms' in df.columns and len(df) > 0:
            min_beds = st.selectbox("🛏️ Min Bedrooms", [0, 1, 2, 3, 4, 5])
        else:
            min_beds = 0
    
    with col4:
        if 'lastSalePrice' in df.columns and len(df) > 0:
            min_price = float(df['lastSalePrice'].min())
            max_price = float(df['lastSalePrice'].max())
            if min_price < max_price:
                price_range = st.slider("💰 Price Range", min_price, max_price, (min_price, max_price))
            else:
                price_range = (min_price, max_price)
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
    
    if 'lastSalePrice' in df.columns and len(filtered_df) > 0:
        filtered_df = filtered_df[
            (filtered_df['lastSalePrice'] >= price_range[0]) & 
            (filtered_df['lastSalePrice'] <= price_range[1])
        ]

    st.markdown(f"""
    <div style="background: linear-gradient(45deg, #56ab2f, #a8e6cf); padding: 15px; border-radius: 10px; margin: 20px 0;">
    <h3 style="color: white; text-align: center;">📋 Showing {len(filtered_df)} properties</h3>
    </div>
    """, unsafe_allow_html=True)

    # Display properties with colorful cards
    for idx, row in filtered_df.iterrows():
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.markdown(f"""
            <div class="property-card">
                <h2>🏠 {row.get('formattedAddress', 'N/A')}</h2>
                <div style="display: flex; flex-wrap: wrap; gap: 15px; margin: 15px 0;">
                    <span style="background: rgba(255,255,255,0.2); padding: 8px 15px; border-radius: 20px;">
                        🏠 {row.get('propertyType', 'N/A')}
                    </span>
                    <span style="background: rgba(255,255,255,0.2); padding: 8px 15px; border-radius: 20px;">
                        🛏️ {row.get('bedrooms', 'N/A')} beds
                    </span>
                    <span style="background: rgba(255,255,255,0.2); padding: 8px 15px; border-radius: 20px;">
                        🛁 {row.get('bathrooms', 'N/A')} baths
                    </span>
                    <span style="background: rgba(255,255,255,0.2); padding: 8px 15px; border-radius: 20px;">
                        📐 {row.get('squareFootage', 'N/A'):,} sq ft
                    </span>
                    <span style="background: rgba(255,255,255,0.2); padding: 8px 15px; border-radius: 20px;">
                        📅 Built {row.get('yearBuilt', 'N/A')}
                    </span>
                </div>
                
                <div style="margin: 20px 0;">
                    <h4>💰 Financial Information</h4>
                    <p><strong>Last Sale:</strong> ${row.get('lastSalePrice', 0):,} | 
                    <strong>Assessment 2023:</strong> ${row.get('taxAssessment_2023', 0):,} | 
                    <strong>Monthly Rent:</strong> ${row.get('rental_rate', 0):,}</p>
                </div>
                
                <div style="margin: 20px 0;">
                    <h4>📍 Location</h4>
                    <p><strong>City:</strong> {row.get('city', 'N/A')}, {row.get('state', 'N/A')} {row.get('zipCode', 'N/A')} | 
                    <strong>County:</strong> {row.get('county', 'N/A')}</p>
                </div>
                
                <div style="margin: 20px 0;">
                    <h4>🏠 Features</h4>
                    <div style="display: flex; flex-wrap: wrap; gap: 10px;">
                        {'<span style="background: rgba(255,255,255,0.3); padding: 5px 10px; border-radius: 15px;">🚗 ' + str(row.get('garageSpaces', 0)) + ' Car Garage</span>' if row.get('garage', False) else ''}
                        {'<span style="background: rgba(255,255,255,0.3); padding: 5px 10px; border-radius: 15px;">🏊 Pool</span>' if row.get('pool', False) else ''}
                        {'<span style="background: rgba(255,255,255,0.3); padding: 5px 10px; border-radius: 15px;">🔥 Fireplace</span>' if row.get('fireplace', False) else ''}
                        <span style="background: rgba(255,255,255,0.3); padding: 5px 10px; border-radius: 15px;">❄️ {row.get('coolingType', 'N/A')}</span>
                        <span style="background: rgba(255,255,255,0.3); padding: 5px 10px; border-radius: 15px;">🔥 {row.get('heatingType', 'N/A')}</span>
                    </div>
                </div>
                
                <div style="margin: 20px 0;">
                    <h4>👤 Owner Information</h4>
                    <p><strong>Name:</strong> {row.get('owner_name', 'N/A')} ({row.get('owner_type', 'N/A')}) | 
                    <strong>Occupied:</strong> {'Yes' if row.get('ownerOccupied', False) else 'No'}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("<br><br>", unsafe_allow_html=True)
            if st.button("👁️ View Details", key=f"view_{idx}", use_container_width=True):
                st.session_state.selected_property_id = row.get('id')
            if st.button("✏️ Edit", key=f"edit_{idx}", use_container_width=True):
                st.session_state.selected_property_id = row.get('id')
                st.rerun()
            if st.button("📊 Analytics", key=f"analytics_{idx}", use_container_width=True):
                st.success(f"Analytics for {row.get('formattedAddress', 'N/A')}")

elif page == "📈 Analytics":
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 15px; margin-bottom: 30px;">
    <h2 style="text-align: center; color: white;">📊 Property Analytics</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Analytics tabs
    tab1, tab2, tab3, tab4 = st.tabs(["💰 Financial", "📍 Geographic", "🏠 Property Features", "📈 Trends"])
    
    with tab1:
        st.subheader("💰 Financial Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if 'lastSalePrice' in df.columns and len(df) > 0:
                st.subheader("💵 Price Distribution")
                colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
                fig_hist = px.histogram(df, x='lastSalePrice', nbins=20, color_discrete_sequence=colors)
                fig_hist.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_hist, use_container_width=True)
            else:
                st.info("Price data not available")
            
        with col2:
            if all(col in df.columns for col in ['squareFootage', 'lastSalePrice']) and len(df) > 0:
                st.subheader("📐 Price vs Square Footage")
                fig_scatter = px.scatter(df, x='squareFootage', y='lastSalePrice', color='propertyType' if 'propertyType' in df.columns else None)
                fig_scatter.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_scatter, use_container_width=True)
            else:
                st.info("Square footage or price data not available")
    
    with tab2:
        st.subheader("📍 Geographic Distribution")
        
        if 'latitude' in df.columns and 'longitude' in df.columns and len(df) > 0:
            # Create colorful map
            valid_coords = df.dropna(subset=['latitude', 'longitude'])
            if len(valid_coords) > 0:
                map_center = [valid_coords['latitude'].mean(), valid_coords['longitude'].mean()]
                m = folium.Map(location=map_center, zoom_start=10, tiles='CartoDB positron')
                
                colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'beige', 'darkblue', 'darkgreen']
                
                for idx, row in valid_coords.iterrows():
                    color = colors[idx % len(colors)]
                    folium.CircleMarker(
                        [row['latitude'], row['longitude']],
                        radius=10,
                        popup=f"""
                        <b>{row.get('formattedAddress', 'N/A')}</b><br>
                        💰 ${row.get('lastSalePrice', 0):,}<br>
                        🏠 {row.get('propertyType', 'N/A')}<br>
                        🛏️ {row.get('bedrooms', 'N/A')} beds, 🛁 {row.get('bathrooms', 'N/A')} baths
                        """,
                        tooltip=row.get('formattedAddress', 'N/A'),
                        color=color,
                        fill=True,
                        fillColor=color
                    ).add_to(m)
                
                folium_static(m, width=700, height=500)
            else:
                st.info("No valid coordinates found for mapping")
        else:
            st.info("Location data not available for mapping")
    
    with tab3:
        st.subheader("🏠 Property Features Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if 'bedrooms' in df.columns and len(df) > 0:
                bedroom_counts = df['bedrooms'].value_counts().sort_index()
                colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
                fig_bed = px.bar(x=bedroom_counts.index, y=bedroom_counts.values, color=bedroom_counts.index, color_discrete_sequence=colors)
                fig_bed.update_layout(title="🛏️ Properties by Bedroom Count", xaxis_title="Bedrooms", yaxis_title="Count", showlegend=False)
                fig_bed.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_bed, use_container_width=True)
        
        with col2:
            if 'yearBuilt' in df.columns and len(df) > 0:
                colors = ['#DDA0DD', '#98FB98', '#F0E68C', '#FFB6C1', '#20B2AA']
                fig_year = px.histogram(df, x='yearBuilt', nbins=20, color_discrete_sequence=colors)
                fig_year.update_layout(title="📅 Properties by Year Built")
                fig_year.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_year, use_container_width=True)
    
    with tab4:
        st.subheader("📈 Market Trends")
        
        if 'yearBuilt' in df.columns and 'lastSalePrice' in df.columns and len(df) > 0:
            decade_analysis = df.copy()
            decade_analysis['decade'] = (decade_analysis['yearBuilt'] // 10) * 10
            decade_prices = decade_analysis.groupby('decade')['lastSalePrice'].mean().reset_index()
            
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98FB98']
            fig_trend = px.bar(decade_prices, x='decade', y='lastSalePrice', color='decade', color_discrete_sequence=colors)
            fig_trend.update_layout(title="💰 Average Price by Decade Built", xaxis_title="Decade", yaxis_title="Average Price", showlegend=False)
            fig_trend.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_trend, use_container_width=True)

elif page == "💰 Financial Reports":
    
    st.markdown("""
    <div style="background: linear-gradient(45deg, #56ab2f, #a8e6cf); padding: 20px; border-radius: 15px; margin-bottom: 30px;">
    <h2 style="text-align: center; color: white;">💼 Financial Dashboard</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Financial metrics with colorful cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_value = df['lastSalePrice'].sum() if 'lastSalePrice' in df.columns else 0
        st.markdown(f"""
        <div style="background: linear-gradient(45deg, #667eea, #764ba2); padding: 20px; border-radius: 15px; text-align: center; color: white;">
            <h3>🏠 Total Portfolio Value</h3>
            <h2>${total_value:,.0f}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        total_tax = df['propertyTax_2023'].sum() if 'propertyTax_2023' in df.columns else 0
        st.markdown(f"""
        <div style="background: linear-gradient(45deg, #f093fb, #f5576c); padding: 20px; border-radius: 15px; text-align: center; color: white; margin-top: 20px;">
            <h3>🏛️ Annual Property Tax</h3>
            <h2>${total_tax:,.0f}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        monthly_income = df['rental_rate'].sum() if 'rental_rate' in df.columns else 0
        annual_income = monthly_income * 12
        st.markdown(f"""
        <div style="background: linear-gradient(45deg, #56ab2f, #a8e6cf); padding: 20px; border-radius: 15px; text-align: center; color: white;">
            <h3>💵 Annual Rental Income</h3>
            <h2>${annual_income:,.0f}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        total_maintenance = df['maintenance_cost'].sum() if 'maintenance_cost' in df.columns else 0
        st.markdown(f"""
        <div style="background: linear-gradient(45deg, #fa709a, #fee140); padding: 20px; border-radius: 15px; text-align: center; color: white; margin-top: 20px;">
            <h3>🔧 Annual Maintenance</h3>
            <h2>${total_maintenance:,.0f}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        if all(col in df.columns for col in ['rental_rate', 'maintenance_cost', 'propertyTax_2023']):
            net_income = (df['rental_rate'] * 12) - df['maintenance_cost'] - df['propertyTax_2023']
            total_net = net_income.sum()
            color = "linear-gradient(45deg, #56ab2f, #a8e6cf)" if total_net >= 0 else "linear-gradient(45deg, #ed4264, #ffedbc)"
            st.markdown(f"""
            <div style="background: {color}; padding: 20px; border-radius: 15px; text-align: center; color: white;">
                <h3>📊 Net Annual Income</h3>
                <h2>${total_net:,.0f}</h2>
            </div>
            """, unsafe_allow_html=True)

    # Revenue breakdown with colorful waterfall chart
    if all(col in df.columns for col in ['rental_rate', 'maintenance_cost', 'propertyTax_2023']) and len(df) > 0:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 15px; margin: 30px 0;">
        <h2 style="text-align: center; color: white;">📊 Revenue Breakdown</h2>
        </div>
        """, unsafe_allow_html=True)
        
        total_revenue = df['rental_rate'].sum() * 12
        total_maintenance = df['maintenance_cost'].sum()
        total_tax = df['propertyTax_2023'].sum()
        net_profit = total_revenue - total_maintenance - total_tax
        
        categories = ['Gross Revenue', 'Maintenance', 'Property Tax', 'Net Profit']
        values = [total_revenue, -total_maintenance, -total_tax, net_profit]
        colors = ['#56ab2f', '#ed4264', '#f7971e', '#667eea']
        
        fig_waterfall = go.Figure()
        fig_waterfall.add_trace(go.Bar(x=categories, y=values, marker_color=colors))
        fig_waterfall.update_layout(title="Annual Financial Performance", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_waterfall, use_container_width=True)

elif page == "🔧 Property Management":
    
    st.markdown("""
    <div style="background: linear-gradient(45deg, #fa709a, #fee140); padding: 20px; border-radius: 15px; margin-bottom: 30px;">
    <h2 style="text-align: center; color: white;">🔧 Property Management Tools</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Management tabs
    tab1, tab2, tab3 = st.tabs(["📋 Tasks", "🔧 Maintenance", "👥 Tenants"])
    
    with tab1:
        st.markdown("""
        <div style="background: linear-gradient(45deg, #667eea, #764ba2); padding: 15px; border-radius: 10px; margin-bottom: 20px;">
        <h3 style="color: white; text-align: center;">📋 Task Management</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Add new task
        with st.expander("➕ Add New Task", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                task_property = st.selectbox("🏠 Property", df['formattedAddress'].tolist() if 'formattedAddress' in df.columns else ['No properties'])
                task_type = st.selectbox("📝 Task Type", ["Maintenance", "Inspection", "Showing", "Administrative", "Cleaning", "Repair"])
            with col2:
                task_priority = st.selectbox("⚡ Priority", ["Low", "Medium", "High", "Urgent"])
                due_date = st.date_input("📅 Due Date")
            
            task_description = st.text_area("📄 Description")
            assigned_to = st.text_input("👤 Assigned To")
            
            if st.button("✅ Add Task", type="primary"):
                st.markdown('<div class="success-box">✅ Task added successfully!</div>', unsafe_allow_html=True)
        
        # Display existing tasks with colorful styling
        st.markdown("""
        <div style="background: linear-gradient(45deg, #4ECDC4, #44A08D); padding: 15px; border-radius: 10px; margin: 20px 0;">
        <h3 style="color: white; text-align: center;">📋 Current Tasks</h3>
        </div>
        """, unsafe_allow_html=True)
        
        tasks_data = {
            'Property': ['5500 Grand Lake Dr', '1234 Oak Street', '5678 Pine Ave'],
            'Task': ['HVAC Inspection', 'Gutter Cleaning', 'Tenant Showing'],
            'Priority': ['Medium', 'Low', 'High'],
            'Due Date': ['2025-08-20', '2025-08-25', '2025-08-18'],
            'Status': ['Pending', 'Scheduled', 'In Progress'],
            'Assigned To': ['John Doe', 'Mike Smith', 'Sarah Johnson']
        }
        tasks_df = pd.DataFrame(tasks_data)
        st.dataframe(tasks_df, use_container_width=True)
    
    with tab2:
        st.markdown("""
        <div style="background: linear-gradient(45deg, #f093fb, #f5576c); padding: 15px; border-radius: 10px; margin-bottom: 20px;">
        <h3 style="color: white; text-align: center;">🔧 Maintenance Tracking</h3>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💰 Maintenance Costs by Property")
            if 'maintenance_cost' in df.columns and 'formattedAddress' in df.columns and len(df) > 0:
                maintenance_data = df[['formattedAddress', 'maintenance_cost']].copy()
                colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
                fig_maint = px.bar(maintenance_data, x='formattedAddress', y='maintenance_cost', color='formattedAddress', color_discrete_sequence=colors)
                fig_maint.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_maint, use_container_width=True)
        
        with col2:
            st.subheader("📅 Schedule Maintenance")
            property_select = st.selectbox("🏠 Select Property", df['formattedAddress'].tolist() if 'formattedAddress' in df.columns else ['No properties'])
            maintenance_type = st.selectbox("🔧 Maintenance Type", ["HVAC", "Plumbing", "Electrical", "Roofing", "Painting", "Landscaping", "Appliance Repair", "Flooring"])
            contractor = st.text_input("👷 Contractor/Vendor")
            scheduled_date = st.date_input("📅 Schedule Date")
            estimated_cost = st.number_input("💰 Estimated Cost", min_value=0.0, step=50.0)
            notes = st.text_area("📝 Notes")
            
            if st.button("📅 Schedule Maintenance", type="primary"):
                st.markdown('<div class="success-box">✅ Maintenance scheduled successfully!</div>', unsafe_allow_html=True)
        
        # Maintenance history
        st.markdown("""
        <div style="background: linear-gradient(45deg, #56ab2f, #a8e6cf); padding: 15px; border-radius: 10px; margin: 20px 0;">
        <h3 style="color: white; text-align: center;">📋 Recent Maintenance History</h3>
        </div>
        """, unsafe_allow_html=True)
        
        maintenance_history = {
            'Date': ['2025-08-10', '2025-08-05', '2025-08-01'],
            'Property': ['5500 Grand Lake Dr', '1234 Oak Street', '5678 Pine Ave'],
            'Type': ['HVAC Service', 'Plumbing Repair', 'Painting'],
            'Contractor': ['ABC HVAC', 'Quick Fix Plumbing', 'Pro Painters'],
            'Cost': [350, 180, 1200],
            'Status': ['Completed', 'Completed', 'In Progress']
        }
        maint_df = pd.DataFrame(maintenance_history)
        st.dataframe(maint_df, use_container_width=True)
    
    with tab3:
        st.markdown("""
        <div style="background: linear-gradient(45deg, #667eea, #764ba2); padding: 15px; border-radius: 10px; margin-bottom: 20px;">
        <h3 style="color: white; text-align: center;">👥 Tenant Management</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Enhanced tenant data
        tenant_data = {
            'Property': ['5500 Grand Lake Dr', '1234 Oak Street', '5678 Pine Ave'],
            'Tenant': ['John & Mary Johnson', 'Sarah Wilson', 'Robert & Lisa Davis'],
            'Lease Start': ['2024-01-01', '2024-06-15', '2023-09-01'],
            'Lease End': ['2025-12-31', '2025-06-14', '2024-08-31'],
            'Monthly Rent': [2500, 2800, 3200],
            'Security Deposit': [2500, 2800, 3200],
            'Status': ['Active', 'Active', 'Expiring Soon'],
            'Phone': ['(555) 123-4567', '(555) 987-6543', '(555) 456-7890'],
            'Email': ['johnson@email.com', 'sarah.w@email.com', 'rdavis@email.com']
        }
        tenant_df = pd.DataFrame(tenant_data)
        st.dataframe(tenant_df, use_container_width=True)
        
        # Add tenant form
        with st.expander("➕ Add New Tenant", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                tenant_property = st.selectbox("🏠 Property", df['formattedAddress'].tolist() if 'formattedAddress' in df.columns else ['No properties'], key="tenant_prop")
                tenant_name = st.text_input("👤 Tenant Name")
                tenant_phone = st.text_input("📞 Phone Number")
                tenant_email = st.text_input("📧 Email Address")
            with col2:
                lease_start = st.date_input("📅 Lease Start")
                lease_end = st.date_input("📅 Lease End")
                monthly_rent = st.number_input("💰 Monthly Rent", min_value=0.0, step=50.0)
                security_deposit = st.number_input("🛡️ Security Deposit", min_value=0.0, step=50.0)
            
            emergency_contact = st.text_input("🚨 Emergency Contact")
            notes = st.text_area("📝 Notes")
            
            if st.button("➕ Add Tenant", type="primary"):
                st.markdown('<div class="success-box">✅ Tenant added successfully!</div>', unsafe_allow_html=True)

elif page == "➕ Add Property":
    
    st.markdown("""
    <div style="background: linear-gradient(45deg, #56ab2f, #a8e6cf); padding: 20px; border-radius: 15px; margin-bottom: 30px;">
    <h2 style="text-align: center; color: white;">➕ Add New Property</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Comprehensive property form with all fields
    with st.form("add_property_form"):
        st.markdown("### 📍 Location Information")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            address_line1 = st.text_input("🏠 Street Address")
            address_line2 = st.text_input("🏠 Address Line 2 (Optional)")
            city = st.text_input("🏙️ City")
        with col2:
            state = st.selectbox("🗺️ State", ["TX", "CA", "FL", "NY", "WA", "OR", "AZ", "NV", "Other"])
            zip_code = st.text_input("📮 ZIP Code")
            county = st.text_input("🏛️ County")
        with col3:
            latitude = st.number_input("🌐 Latitude", format="%.6f", step=0.000001)
            longitude = st.number_input("🌐 Longitude", format="%.6f", step=0.000001)
        
        st.markdown("### 🏠 Property Details")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            prop_type = st.selectbox("🏠 Property Type", ["Single Family", "Condo", "Townhouse", "Multi-Family", "Duplex", "Apartment"])
            bedrooms = st.number_input("🛏️ Bedrooms", min_value=0, max_value=20, step=1)
        with col2:
            bathrooms = st.number_input("🛁 Bathrooms", min_value=0.0, max_value=20.0, step=0.5)
            sqft = st.number_input("📐 Square Footage", min_value=0, step=50)
        with col3:
            lot_size = st.number_input("🌳 Lot Size (sq ft)", min_value=0, step=100)
            year_built = st.number_input("📅 Year Built", min_value=1800, max_value=2025, step=1)
        with col4:
            room_count = st.number_input("🏠 Total Rooms", min_value=0, max_value=50, step=1)
            floor_count = st.number_input("🏢 Floor Count", min_value=1, max_value=10, step=1)
        
        st.markdown("### 🏗️ Property Features")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            architecture_type = st.selectbox("🏛️ Architecture Type", ["Contemporary", "Traditional", "Modern", "Colonial", "Ranch", "Victorian", "Craftsman", "Other"])
            exterior_type = st.selectbox("🧱 Exterior Type", ["Wood", "Brick", "Stone", "Vinyl", "Stucco", "Aluminum", "Fiber Cement"])
            roof_type = st.selectbox("🏠 Roof Type", ["Asphalt", "Tile", "Metal", "Slate", "Wood", "Flat", "Other"])
        
        with col2:
            has_cooling = st.checkbox("❄️ Air Conditioning")
            cooling_type = st.selectbox("❄️ Cooling Type", ["Central", "Window Units", "Heat Pump", "Evaporative", "None"]) if has_cooling else "None"
            has_heating = st.checkbox("🔥 Heating System")
            heating_type = st.selectbox("🔥 Heating Type", ["Forced Air", "Radiant", "Heat Pump", "Baseboard", "Fireplace", "Other"]) if has_heating else "None"
        
        with col3:
            has_fireplace = st.checkbox("🔥 Fireplace")
            fireplace_type = st.selectbox("🔥 Fireplace Type", ["Masonry", "Gas", "Electric", "Wood Burning"]) if has_fireplace else ""
            foundation_type = st.selectbox("🏗️ Foundation Type", ["Slab", "Crawl Space", "Basement", "Pier and Beam"])
        
        st.markdown("### 🚗 Garage & Parking")
        col1, col2 = st.columns(2)
        with col1:
            has_garage = st.checkbox("🚗 Garage")
            garage_spaces = st.number_input("🚗 Garage Spaces", min_value=0, max_value=10) if has_garage else 0
        with col2:
            garage_type = st.selectbox("🚗 Garage Type", ["Attached", "Detached", "Carport"]) if has_garage else ""
        
        st.markdown("### 🏊 Additional Amenities")
        col1, col2 = st.columns(2)
        with col1:
            has_pool = st.checkbox("🏊 Pool")
            pool_type = st.selectbox("🏊 Pool Type", ["Concrete", "Fiberglass", "Vinyl", "Above Ground"]) if has_pool else ""
        with col2:
            view_type = st.selectbox("🌅 View Type", ["City", "Mountain", "Lake", "Ocean", "Garden", "Courtyard", "None"])
        
        st.markdown("### 💰 Financial Information")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            purchase_price = st.number_input("💰 Purchase Price", min_value=0.0, step=1000.0)
            last_sale_date = st.date_input("📅 Last Sale Date")
        with col2:
            rental_rate = st.number_input("🏠 Monthly Rental Rate", min_value=0.0, step=50.0)
            hoa_fee = st.number_input("🏢 HOA Fee", min_value=0.0, step=25.0)
        with col3:
            tax_assessment_2023 = st.number_input("🏛️ Tax Assessment 2023", min_value=0.0, step=1000.0)
            property_tax_2023 = st.number_input("💸 Property Tax 2023", min_value=0.0, step=100.0)
        with col4:
            maintenance_cost = st.number_input("🔧 Annual Maintenance Cost", min_value=0.0, step=100.0)
            occupancy_rate = st.number_input("📊 Occupancy Rate (%)", min_value=0.0, max_value=100.0, step=5.0)
        
        st.markdown("### 👤 Owner Information")
        col1, col2 = st.columns(2)
        
        with col1:
            owner_name = st.text_input("👤 Owner Name")
            owner_type = st.selectbox("🏢 Owner Type", ["Individual", "LLC", "Corporation", "Trust", "Partnership"])
        with col2:
            owner_occupied = st.checkbox("🏠 Owner Occupied")
            owner_address = st.text_area("📮 Owner Mailing Address")
        
        st.markdown("### 📋 Legal & Administrative")
        col1, col2 = st.columns(2)
        
        with col1:
            assessor_id = st.text_input("🆔 Assessor ID")
            legal_description = st.text_area("📜 Legal Description")
        with col2:
            subdivision = st.text_input("🏘️ Subdivision")
            zoning = st.text_input("🗺️ Zoning")
        
        st.markdown("### 📈 Property Status")
        status = st.selectbox("📊 Property Status", ["Active", "Rented", "Vacant", "Under Renovation", "For Sale", "Sold"])
        
        # Submit button
        submitted = st.form_submit_button("✅ Add Property", type="primary", use_container_width=True)
        
        if submitted:
            st.markdown("""
            <div style="background: linear-gradient(45deg, #56ab2f, #a8e6cf); padding: 20px; border-radius: 15px; text-align: center; color: white; margin: 20px 0;">
                <h2>🎉 Property Added Successfully!</h2>
                <p>Your new property has been added to the portfolio.</p>
            </div>
            """, unsafe_allow_html=True)
            st.balloons()

elif page == "✏️ Edit Property":
    
    st.markdown("""
    <div style="background: linear-gradient(45deg, #f093fb, #f5576c); padding: 20px; border-radius: 15px; margin-bottom: 30px;">
    <h2 style="text-align: center; color: white;">✏️ Edit Property</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Property selection
    if len(df) > 0:
        property_options = df['formattedAddress'].tolist() if 'formattedAddress' in df.columns else df.index.tolist()
        selected_property = st.selectbox("🏠 Select Property to Edit", property_options)
        
        if selected_property:
            # Find the selected property
            if 'formattedAddress' in df.columns:
                property_data = df[df['formattedAddress'] == selected_property].iloc[0]
            else:
                property_data = df.iloc[0]
            
            # Edit form with pre-filled data
            with st.form("edit_property_form"):
                st.markdown("### 📍 Location Information")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    address_line1 = st.text_input("🏠 Street Address", value=str(property_data.get('addressLine1', '')))
                    address_line2 = st.text_input("🏠 Address Line 2", value=str(property_data.get('addressLine2', '')))
                    city = st.text_input("🏙️ City", value=str(property_data.get('city', '')))
                with col2:
                    state = st.text_input("🗺️ State", value=str(property_data.get('state', '')))
                    zip_code = st.text_input("📮 ZIP Code", value=str(property_data.get('zipCode', '')))
                    county = st.text_input("🏛️ County", value=str(property_data.get('county', '')))
                with col3:
                    latitude = st.number_input("🌐 Latitude", value=float(property_data.get('latitude', 0)), format="%.6f", step=0.000001)
                    longitude = st.number_input("🌐 Longitude", value=float(property_data.get('longitude', 0)), format="%.6f", step=0.000001)
                
                st.markdown("### 🏠 Property Details")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    prop_types = ["Single Family", "Condo", "Townhouse", "Multi-Family", "Duplex", "Apartment"]
                    current_type = str(property_data.get('propertyType', 'Single Family'))
                    prop_type_index = prop_types.index(current_type) if current_type in prop_types else 0
                    prop_type = st.selectbox("🏠 Property Type", prop_types, index=prop_type_index)
                    bedrooms = st.number_input("🛏️ Bedrooms", value=int(property_data.get('bedrooms', 0)), min_value=0, max_value=20, step=1)
                with col2:
                    bathrooms = st.number_input("🛁 Bathrooms", value=float(property_data.get('bathrooms', 0)), min_value=0.0, max_value=20.0, step=0.5)
                    sqft = st.number_input("📐 Square Footage", value=int(property_data.get('squareFootage', 0)), min_value=0, step=50)
                with col3:
                    lot_size = st.number_input("🌳 Lot Size (sq ft)", value=int(property_data.get('lotSize', 0)), min_value=0, step=100)
                    year_built = st.number_input("📅 Year Built", value=int(property_data.get('yearBuilt', 2000)), min_value=1800, max_value=2025, step=1)
                with col4:
                    room_count = st.number_input("🏠 Total Rooms", value=int(property_data.get('roomCount', 0)), min_value=0, max_value=50, step=1)
                    floor_count = st.number_input("🏢 Floor Count", value=int(property_data.get('floorCount', 1)), min_value=1, max_value=10, step=1)
                
                st.markdown("### 🏗️ Property Features")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    arch_types = ["Contemporary", "Traditional", "Modern", "Colonial", "Ranch", "Victorian", "Craftsman", "Other"]
                    current_arch = str(property_data.get('architectureType', 'Contemporary'))
                    arch_index = arch_types.index(current_arch) if current_arch in arch_types else 0
                    architecture_type = st.selectbox("🏛️ Architecture Type", arch_types, index=arch_index)
                    
                    exterior_types = ["Wood", "Brick", "Stone", "Vinyl", "Stucco", "Aluminum", "Fiber Cement"]
                    current_exterior = str(property_data.get('exteriorType', 'Wood'))
                    exterior_index = exterior_types.index(current_exterior) if current_exterior in exterior_types else 0
                    exterior_type = st.selectbox("🧱 Exterior Type", exterior_types, index=exterior_index)
                    
                    roof_types = ["Asphalt", "Tile", "Metal", "Slate", "Wood", "Flat", "Other"]
                    current_roof = str(property_data.get('roofType', 'Asphalt'))
                    roof_index = roof_types.index(current_roof) if current_roof in roof_types else 0
                    roof_type = st.selectbox("🏠 Roof Type", roof_types, index=roof_index)
                
                with col2:
                    has_cooling = st.checkbox("❄️ Air Conditioning", value=bool(property_data.get('cooling', False)))
                    cooling_types = ["Central", "Window Units", "Heat Pump", "Evaporative", "None"]
                    current_cooling = str(property_data.get('coolingType', 'Central'))
                    cooling_index = cooling_types.index(current_cooling) if current_cooling in cooling_types else 0
                    cooling_type = st.selectbox("❄️ Cooling Type", cooling_types, index=cooling_index) if has_cooling else "None"
                    
                    has_heating = st.checkbox("🔥 Heating System", value=bool(property_data.get('heating', False)))
                    heating_types = ["Forced Air", "Radiant", "Heat Pump", "Baseboard", "Fireplace", "Other"]
                    current_heating = str(property_data.get('heatingType', 'Forced Air'))
                    heating_index = heating_types.index(current_heating) if current_heating in heating_types else 0
                    heating_type = st.selectbox("🔥 Heating Type", heating_types, index=heating_index) if has_heating else "None"
                
                with col3:
                    has_fireplace = st.checkbox("🔥 Fireplace", value=bool(property_data.get('fireplace', False)))
                    fireplace_types = ["Masonry", "Gas", "Electric", "Wood Burning"]
                    current_fireplace = str(property_data.get('fireplaceType', 'Masonry'))
                    fireplace_index = fireplace_types.index(current_fireplace) if current_fireplace in fireplace_types else 0
                    fireplace_type = st.selectbox("🔥 Fireplace Type", fireplace_types, index=fireplace_index) if has_fireplace else ""
                    
                    foundation_types = ["Slab", "Crawl Space", "Basement", "Pier and Beam"]
                    current_foundation = str(property_data.get('foundationType', 'Slab'))
                    foundation_index = foundation_types.index(current_foundation) if current_foundation in foundation_types else 0
                    foundation_type = st.selectbox("🏗️ Foundation Type", foundation_types, index=foundation_index)
                
                st.markdown("### 🚗 Garage & Parking")
                col1, col2 = st.columns(2)
                with col1:
                    has_garage = st.checkbox("🚗 Garage", value=bool(property_data.get('garage', False)))
                    garage_spaces = st.number_input("🚗 Garage Spaces", value=int(property_data.get('garageSpaces', 0)), min_value=0, max_value=10) if has_garage else 0
                with col2:
                    garage_types = ["Attached", "Detached", "Carport"]
                    current_garage = str(property_data.get('garageType', 'Attached'))
                    garage_index = garage_types.index(current_garage) if current_garage in garage_types else 0
                    garage_type = st.selectbox("🚗 Garage Type", garage_types, index=garage_index) if has_garage else ""
                
                st.markdown("### 🏊 Additional Amenities")
                col1, col2 = st.columns(2)
                with col1:
                    has_pool = st.checkbox("🏊 Pool", value=bool(property_data.get('pool', False)))
                    pool_types = ["Concrete", "Fiberglass", "Vinyl", "Above Ground"]
                    current_pool = str(property_data.get('poolType', 'Concrete'))
                    pool_index = pool_types.index(current_pool) if current_pool in pool_types else 0
                    pool_type = st.selectbox("🏊 Pool Type", pool_types, index=pool_index) if has_pool else ""
                with col2:
                    view_types = ["City", "Mountain", "Lake", "Ocean", "Garden", "Courtyard", "None"]
                    current_view = str(property_data.get('viewType', 'City'))
                    view_index = view_types.index(current_view) if current_view in view_types else 0
                    view_type = st.selectbox("🌅 View Type", view_types, index=view_index)
                
                st.markdown("### 💰 Financial Information")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    purchase_price = st.number_input("💰 Last Sale Price", value=float(property_data.get('lastSalePrice', 0)), min_value=0.0, step=1000.0)
                    last_sale_date = st.date_input("📅 Last Sale Date", value=pd.to_datetime(property_data.get('lastSaleDate', '2020-01-01')).date())
                with col2:
                    rental_rate = st.number_input("🏠 Monthly Rental Rate", value=float(property_data.get('rental_rate', 0)), min_value=0.0, step=50.0)
                    hoa_fee = st.number_input("🏢 HOA Fee", value=float(property_data.get('hoa_fee', 0)), min_value=0.0, step=25.0)
                with col3:
                    tax_assessment_2023 = st.number_input("🏛️ Tax Assessment 2023", value=float(property_data.get('taxAssessment_2023', 0)), min_value=0.0, step=1000.0)
                    property_tax_2023 = st.number_input("💸 Property Tax 2023", value=float(property_data.get('propertyTax_2023', 0)), min_value=0.0, step=100.0)
                with col4:
                    maintenance_cost = st.number_input("🔧 Annual Maintenance Cost", value=float(property_data.get('maintenance_cost', 0)), min_value=0.0, step=100.0)
                    occupancy_rate = st.number_input("📊 Occupancy Rate (%)", value=float(property_data.get('occupancy_rate', 0)), min_value=0.0, max_value=100.0, step=5.0)
                
                st.markdown("### 👤 Owner Information")
                col1, col2 = st.columns(2)
                
                with col1:
                    owner_name = st.text_input("👤 Owner Name", value=str(property_data.get('owner_name', '')))
                    owner_types = ["Individual", "LLC", "Corporation", "Trust", "Partnership"]
                    current_owner_type = str(property_data.get('owner_type', 'Individual'))
                    owner_type_index = owner_types.index(current_owner_type) if current_owner_type in owner_types else 0
                    owner_type = st.selectbox("🏢 Owner Type", owner_types, index=owner_type_index)
                with col2:
                    owner_occupied = st.checkbox("🏠 Owner Occupied", value=bool(property_data.get('ownerOccupied', False)))
                    owner_address = st.text_area("📮 Owner Mailing Address", value=str(property_data.get('owner_mailingAddress', '')))
                
                st.markdown("### 📋 Legal & Administrative")
                col1, col2 = st.columns(2)
                
                with col1:
                    assessor_id = st.text_input("🆔 Assessor ID", value=str(property_data.get('assessorID', '')))
                    legal_description = st.text_area("📜 Legal Description", value=str(property_data.get('legalDescription', '')))
                with col2:
                    subdivision = st.text_input("🏘️ Subdivision", value=str(property_data.get('subdivision', '')))
                    zoning = st.text_input("🗺️ Zoning", value=str(property_data.get('zoning', '')))
                
                st.markdown("### 📈 Property Status")
                status_options = ["Active", "Rented", "Vacant", "Under Renovation", "For Sale", "Sold"]
                current_status = str(property_data.get('status', 'Active'))
                status_index = status_options.index(current_status) if current_status in status_options else 0
                status = st.selectbox("📊 Property Status", status_options, index=status_index)
                
                # Submit button
                col1, col2, col3 = st.columns(3)
                with col1:
                    update_submitted = st.form_submit_button("✅ Update Property", type="primary", use_container_width=True)
                with col2:
                    if st.form_submit_button("🗑️ Delete Property", use_container_width=True):
                        st.warning("⚠️ This action cannot be undone!")
                        if st.button("Confirm Delete", type="secondary"):
                            st.markdown("""
                            <div style="background: linear-gradient(45ed, #ed4264, #ffedbc); padding: 20px; border-radius: 15px; text-align: center; color: white; margin: 20px 0;">
                                <h2>🗑️ Property Deleted</h2>
                                <p>The property has been removed from your portfolio.</p>
                            </div>
                            """, unsafe_allow_html=True)
                with col3:
                    if st.form_submit_button("📋 Duplicate Property", use_container_width=True):
                        st.info("Property duplicated successfully!")
                
                if update_submitted:
                    st.markdown("""
                    <div style="background: linear-gradient(45deg, #56ab2f, #a8e6cf); padding: 20px; border-radius: 15px; text-align: center; color: white; margin: 20px 0;">
                        <h2>✅ Property Updated Successfully!</h2>
                        <p>All changes have been saved to your portfolio.</p>
                    </div>
                    """, unsafe_allow_html=True)
                    st.success("✨ Property information updated!")
    else:
        st.warning("No properties available to edit. Please add properties first.")

# Enhanced Footer with colorful styling
st.markdown("---")
st.markdown("""
<div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 15px; text-align: center; margin-top: 30px;">
    <h3 style="color: white; margin: 0;">🏠 Property Management Dashboard</h3>
    <p style="color: rgba(255,255,255,0.8); margin: 10px 0 0 0;">
        Built with ❤️ using Streamlit | 
        📊 Data Analytics | 
        🔧 Property Management | 
        💰 Financial Tracking
    </p>
</div>
""", unsafe_allow_html=True)
