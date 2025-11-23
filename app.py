"""
Smart Garden App - Main Streamlit Application
A comprehensive plant care app with AI-powered features
"""
import streamlit as st
import os
from datetime import datetime, timedelta
from PIL import Image
import io
import tempfile

# Import our custom modules
from config import DEFAULT_CITY, DEFAULT_COUNTRY, load_api_keys
from utils.weather_service import WeatherService
from utils.plant_service import PlantService
from utils.gemini_service import GeminiService
from utils.huggingface_service import HuggingFaceService
from utils.groq_service import GroqService
from utils.data_manager import DataManager

# Import requests for location API
import requests

# Try to import voice-related packages, fallback if not available
SPEECH_RECOGNITION_AVAILABLE = False

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    pass

# Page Configuration
st.set_page_config(
    page_title="Smart Garden App",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load API keys from secrets or environment variables
# This must be called after Streamlit is initialized
load_api_keys()

# Custom CSS for beautiful green-themed UI with animations
st.markdown("""
<style>
    /* Main Background - Green Theme */
    .stApp {
        background: linear-gradient(135deg, #1b5e20 0%, #2e7d32 25%, #4caf50 50%, #66bb6a 75%, #81c784 100%);
        background-attachment: fixed;
        min-height: 100vh;
    }
    
    /* Main Content Area - Light Green Card */
    .main .block-container {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
        margin-top: 2rem;
        margin-bottom: 2rem;
        backdrop-filter: blur(10px);
    }
    
    /* Sidebar - Dark Green */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1b5e20 0%, #2e7d32 100%);
        color: white;
    }
    
    section[data-testid="stSidebar"] * {
        color: white !important;
    }
    
    section[data-testid="stSidebar"] .stRadio label {
        color: white !important;
    }
    
    /* Headers - White on Green Background */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
    }
    
    /* Paragraphs and Text - Dark for readability on light cards */
    .main p, .main div, .main span {
        color: #1b5e20 !important;
    }
    
    /* Header Styling */
    .main-header {
        background: linear-gradient(135deg, #2e7d32 0%, #4caf50 100%);
        color: white;
        padding: 30px;
        border-radius: 20px;
        margin-bottom: 30px;
        box-shadow: 0 8px 20px rgba(46, 125, 50, 0.3);
        text-align: center;
        animation: fadeInDown 0.6s ease-out;
    }
    
    /* Weather Banner - Animated */
    .weather-banner {
        background: linear-gradient(135deg, #66bb6a 0%, #81c784 100%);
        color: white;
        padding: 25px;
        border-radius: 15px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(102, 187, 106, 0.3);
        animation: slideInLeft 0.5s ease-out;
        position: relative;
        overflow: hidden;
    }
    
    .weather-banner::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(45deg, transparent, rgba(255,255,255,0.1), transparent);
        animation: shine 3s infinite;
    }
    
    /* Plant Card - Animated */
    .plant-card {
        background: linear-gradient(135deg, #ffffff 0%, #f1f8e9 100%);
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        border-left: 5px solid #4caf50;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        animation: fadeInUp 0.6s ease-out;
        position: relative;
    }
    
    .plant-card::before {
        content: '🌱';
        position: absolute;
        top: 10px;
        right: 15px;
        font-size: 2em;
        opacity: 0.3;
        color: #4caf50;
        filter: drop-shadow(0 2px 4px rgba(76, 175, 80, 0.3));
        animation: float 3s ease-in-out infinite;
    }
    
    .plant-card:hover {
        transform: translateY(-8px) scale(1.02);
        box-shadow: 0 12px 30px rgba(76, 175, 80, 0.4);
        border-left-width: 8px;
    }
    
    /* Alert Box - Animated */
    .alert-box {
        background: linear-gradient(135deg, #fff3cd 0%, #ffe082 100%);
        border-left: 5px solid #ffc107;
        padding: 15px;
        border-radius: 10px;
        margin: 15px 0;
        animation: pulse 2s infinite;
    }
    
    .alert-box.danger {
        background: linear-gradient(135deg, #f8d7da 0%, #ffcdd2 100%);
        border-left-color: #dc3545;
        animation: shake 0.5s;
    }
    
    .alert-box.success {
        background: linear-gradient(135deg, #d4edda 0%, #c8e6c9 100%);
        border-left-color: #28a745;
    }
    
    /* Status Badges - Enhanced */
    .badge {
        display: inline-block;
        padding: 8px 16px;
        border-radius: 25px;
        font-size: 0.85em;
        font-weight: bold;
        margin: 5px 0;
        animation: fadeIn 0.5s ease-out;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }
    
    .badge-water {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        color: #1565c0;
    }
    
    .badge-happy {
        background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
        color: #2e7d32;
    }
    
    .badge-alert {
        background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
        color: #c62828;
        animation: pulse 1.5s infinite;
    }
    
    .badge-warning {
        background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
        color: #f57c00;
    }
    
    /* Loading Animation */
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .loading-spinner {
        border: 4px solid #f3f3f3;
        border-top: 4px solid #4caf50;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
        margin: 20px auto;
    }
    
    /* Fade In Animations */
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes fadeInDown {
        from {
            opacity: 0;
            transform: translateY(-20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes slideInLeft {
        from {
            opacity: 0;
            transform: translateX(-30px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }
    
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-10px); }
        75% { transform: translateX(10px); }
    }
    
    @keyframes shine {
        0% { transform: translateX(-100%) translateY(-100%) rotate(45deg); }
        100% { transform: translateX(100%) translateY(100%) rotate(45deg); }
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }
    
    @keyframes rotate {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    
    @keyframes pulse-glow {
        0%, 100% { 
            transform: scale(1);
            filter: drop-shadow(0 0 10px rgba(255, 193, 7, 0.5));
        }
        50% { 
            transform: scale(1.1);
            filter: drop-shadow(0 0 20px rgba(255, 193, 7, 0.8));
        }
    }
    
    @keyframes moon-glow {
        0%, 100% { 
            transform: scale(1);
            filter: drop-shadow(0 0 10px rgba(200, 200, 255, 0.5));
        }
        50% { 
            transform: scale(1.05);
            filter: drop-shadow(0 0 15px rgba(200, 200, 255, 0.7));
        }
    }
    
    /* Animated Sun */
    .animated-sun {
        animation: rotate 20s linear infinite, pulse-glow 3s ease-in-out infinite;
        display: inline-block;
    }
    
    /* Animated Moon */
    .animated-moon {
        animation: float 4s ease-in-out infinite, moon-glow 3s ease-in-out infinite;
        display: inline-block;
    }
    
    /* Chat Messages - Enhanced */
    .chat-message {
        padding: 15px;
        border-radius: 15px;
        margin: 10px 0;
        animation: fadeIn 0.5s ease-out;
    }
    
    .chat-user {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        margin-left: 20%;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .chat-bot {
        background: linear-gradient(135deg, #f1f8e9 0%, #c8e6c9 100%);
        margin-right: 20%;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    /* Voice Button - Special Styling */
    .voice-button {
        background: linear-gradient(135deg, #4caf50 0%, #66bb6a 100%);
        color: white;
        border: none;
        padding: 15px 30px;
        border-radius: 50px;
        font-size: 1.1em;
        font-weight: bold;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(76, 175, 80, 0.4);
        transition: all 0.3s;
        animation: pulse 2s infinite;
    }
    
    .voice-button:hover {
        transform: scale(1.1);
        box-shadow: 0 6px 20px rgba(76, 175, 80, 0.6);
    }
    
    .voice-button.recording {
        background: linear-gradient(135deg, #f44336 0%, #e53935 100%);
        animation: pulse 0.5s infinite;
    }
    
    /* Streamlit Elements Override */
    .stButton > button {
        background: linear-gradient(135deg, #4caf50 0%, #66bb6a 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 1.5rem;
        font-weight: bold;
        transition: all 0.3s;
        box-shadow: 0 2px 8px rgba(76, 175, 80, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(76, 175, 80, 0.5);
    }
    
    /* Input Fields */
    .stTextInput > div > div > input {
        border: 2px solid #4caf50;
        border-radius: 10px;
        padding: 0.5rem;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #2e7d32;
        box-shadow: 0 0 10px rgba(76, 175, 80, 0.3);
    }
    
    /* Metric Cards */
    [data-testid="stMetricValue"] {
        color: #2e7d32 !important;
        font-weight: bold;
    }
    
    /* Info/Warning/Success Messages - Enhanced Visibility */
    .stAlert {
        border-radius: 10px;
        animation: fadeInDown 0.5s ease-out;
    }
    
    /* Info Boxes - High Contrast */
    div[data-testid="stAlert"] > div {
        background-color: rgba(255, 255, 255, 0.95) !important;
        border-left: 4px solid #2196f3 !important;
        color: #1b5e20 !important;
        font-weight: 500 !important;
    }
    
    /* Warning Boxes */
    div[data-testid="stAlert"] > div[data-baseweb="notification"] {
        background-color: rgba(255, 255, 255, 0.95) !important;
        border-left: 4px solid #ff9800 !important;
        color: #1b5e20 !important;
    }
    
    /* Success Boxes */
    div[data-testid="stAlert"] > div[data-baseweb="notification"][kind="success"] {
        background-color: rgba(255, 255, 255, 0.95) !important;
        border-left: 4px solid #4caf50 !important;
        color: #1b5e20 !important;
    }
    
    /* Error Boxes */
    div[data-testid="stAlert"] > div[data-baseweb="notification"][kind="error"] {
        background-color: rgba(255, 255, 255, 0.95) !important;
        border-left: 4px solid #f44336 !important;
        color: #1b5e20 !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Services
@st.cache_resource
def init_services():
    """Initialize all services (cached for performance)"""
    return {
        'weather': WeatherService(),
        'plant': PlantService(),
        'gemini': GeminiService(),      # For health analysis (vision)
        'huggingface': HuggingFaceService(),  # For plant identification only
        'groq': GroqService(),          # For fast chat responses
        'data': DataManager()
    }

services = init_services()
weather_service = services['weather']
plant_service = services['plant']
gemini_service = services['gemini']      # For health analysis
huggingface_service = services['huggingface']  # For plant identification
groq_service = services['groq']
data_manager = services['data']

# Location Detection Functions
def get_current_location():
    """Get current location using IP-based API (Free, no key required)"""
    # Known default locations from cloud providers (should be ignored)
    invalid_locations = ["The Dalles", "Dalles", "Unknown", "None", ""]
    
    try:
        # Try secure HTTPS first (ipapi.co - more reliable)
        response = requests.get("https://ipapi.co/json/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            city = data.get('city')
            country_name = data.get('country_name')
            country_code = data.get('country_code', '')
            
            # Validate we got actual data and it's not a default cloud location
            if city and country_name and city not in invalid_locations:
                return {
                    "city": city,
                    "country": country_name,
                    "country_code": country_code,
                    "lat": data.get('latitude'),
                    "lon": data.get('longitude'),
                    "region": data.get('region', '')
                }
    except Exception as e:
        print(f"Location detection (ipapi.co) failed: {e}")
        pass
    
    try:
        # Fallback to ip-api.com (HTTP, but works well)
        response = requests.get("http://ip-api.com/json/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                city = data.get('city')
                country = data.get('country')
                
                # Validate we got actual data and it's not a default cloud location
                if city and country and city not in invalid_locations:
                    return {
                        "city": city,
                        "country": country,
                        "country_code": data.get('countryCode', ''),
                        "lat": data.get('lat'),
                        "lon": data.get('lon'),
                        "region": data.get('regionName', '')
                    }
    except Exception as e:
        print(f"Location detection (ip-api.com) failed: {e}")
        pass
    
    # Final fallback - return default but log that detection failed
    print(f"⚠️ Location detection failed or returned invalid location, using default: {DEFAULT_CITY}, {DEFAULT_COUNTRY}")
    return {
        "city": DEFAULT_CITY,
        "country": DEFAULT_COUNTRY,
        "country_code": "PK",
        "lat": None,
        "lon": None,
        "region": ""
    }

def find_nearby_nurseries(lat, lon, radius_km=10):
    """
    Find nearby plant nurseries
    Uses Overpass API (OpenStreetMap) for free, no-key-required search
    Falls back to mock data if API fails (perfect for hackathon demo)
    """
    try:
        # Try to use Overpass API (OpenStreetMap - Free, no key required)
        overpass_url = "http://overpass-api.de/api/interpreter"
        
        # Query for plant nurseries, garden centers, and flower shops
        query = f"""
        [out:json][timeout:10];
        (
          node["shop"="garden_centre"](around:{radius_km*1000},{lat},{lon});
          node["amenity"="marketplace"]["name"~"plant|nursery|garden",i](around:{radius_km*1000},{lat},{lon});
          node["shop"~"florist|garden",i](around:{radius_km*1000},{lat},{lon});
        );
        out body;
        """
        
        response = requests.get(overpass_url, params={'data': query}, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            elements = data.get('elements', [])
            
            if elements:
                nurseries = []
                for elem in elements[:10]:  # Limit to 10 results
                    tags = elem.get('tags', {})
                    name = tags.get('name', 'Plant Nursery')
                    address = tags.get('addr:full') or tags.get('addr:street', 'Address not available')
                    
                    # Calculate distance (simple approximation)
                    elem_lat = elem.get('lat', lat)
                    elem_lon = elem.get('lon', lon)
                    distance_km = ((elem_lat - lat)**2 + (elem_lon - lon)**2)**0.5 * 111  # Rough km conversion
                    
                    nurseries.append({
                        "name": name,
                        "address": address,
                        "distance": f"{distance_km:.1f} km",
                        "phone": tags.get('phone', 'N/A'),
                        "rating": 4.0 + (hash(name) % 10) / 10,  # Mock rating
                        "lat": elem_lat,
                        "lon": elem_lon
                    })
                
                if nurseries:
                    return nurseries
    except Exception as e:
        print(f"Overpass API error: {e}")
        pass
    
    # Fallback to mock data with location-based coordinates (Perfect for hackathon)
    city_name = st.session_state.user_location.get('city', 'Sialkot')
    mock_nurseries = [
        {
            "name": f"Green Valley Plant Nursery",
            "address": f"Main Boulevard, {city_name}",
            "distance": "2.5 km",
            "phone": "+92 300 1234567",
            "rating": 4.5,
            "lat": lat + 0.02 if lat else 32.5,
            "lon": lon + 0.02 if lon else 74.5
        },
        {
            "name": f"Flora Garden Center",
            "address": f"Garden Road, {city_name}",
            "distance": "4.1 km",
            "phone": "+92 300 2345678",
            "rating": 4.2,
            "lat": lat - 0.03 if lat else 32.48,
            "lon": lon + 0.01 if lon else 74.52
        },
        {
            "name": f"Nature's Paradise",
            "address": f"City Center, {city_name}",
            "distance": "5.8 km",
            "phone": "+92 300 3456789",
            "rating": 4.7,
            "lat": lat + 0.01 if lat else 32.51,
            "lon": lon - 0.02 if lon else 74.48
        },
        {
            "name": f"Botanical Gardens Shop",
            "address": f"Highway Road, {city_name}",
            "distance": "7.2 km",
            "phone": "+92 300 4567890",
            "rating": 4.0,
            "lat": lat - 0.04 if lat else 32.46,
            "lon": lon - 0.01 if lon else 74.49
        },
        {
            "name": f"Green Thumb Nursery",
            "address": f"Residential Area, {city_name}",
            "distance": "8.5 km",
            "phone": "+92 300 5678901",
            "rating": 4.3,
            "lat": lat + 0.03 if lat else 32.53,
            "lon": lon + 0.03 if lon else 74.53
        }
    ]
    return mock_nurseries

# Initialize Session State
if 'plants' not in st.session_state:
    st.session_state.plants = data_manager.get_all_plants()
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Dashboard"
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = data_manager.get_chat_history(20)
if 'user_location' not in st.session_state:
    # Auto-detect location on first load
    detected_location = get_current_location()
    # Check if detected location is valid (not a cloud provider default)
    if detected_location.get('city') and detected_location.get('city') not in ["The Dalles", "Dalles", "Unknown"]:
        st.session_state.user_location = detected_location
    else:
        # Use defaults if detection failed or returned invalid location
        st.session_state.user_location = {"city": DEFAULT_CITY, "country": DEFAULT_COUNTRY, "lat": None, "lon": None, "country_code": "PK"}
if 'use_auto_location' not in st.session_state:
    st.session_state.use_auto_location = False
if 'location_detected' not in st.session_state:
    st.session_state.location_detected = False

# Sidebar Navigation
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 20px 0;">
        <h1 style="color: #2e7d32; margin: 0;">🌱</h1>
        <h2 style="color: #2e7d32; margin: 5px 0;">Smart Garden</h2>
        <p style="color: #666; font-size: 0.9em;">AI-Powered Plant Care</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Initialize page selector in session state if not exists
    if 'page_selector' not in st.session_state:
        st.session_state.page_selector = "🏠 Welcome"
    
    # Check if we need to switch pages (from Ask AI button) - must be done BEFORE widget creation
    if 'switch_to_page' in st.session_state:
        target_page = st.session_state.switch_to_page
        del st.session_state.switch_to_page
        # Set the page selector BEFORE creating the widget
        st.session_state.page_selector = target_page
    
    # Get page from radio button
    page_options = ["🏠 Welcome", "👤 User Profile", "📍 Location & Nurseries", "📊 Garden Dashboard", "🌱 Add a Plant", "🤖 AI Botanist"]
    # Use the session state value, but don't modify it after widget creation
    current_page = st.session_state.get('page_selector', "🏠 Welcome")
    default_index = page_options.index(current_page) if current_page in page_options else 0
    
    page = st.radio(
        "Navigate",
        page_options,
        index=default_index,
        label_visibility="collapsed",
        key="page_selector"
    )
    
    st.markdown("---")
    
    # User Profile Button
    user_profile = data_manager.get_user_profile()
    if user_profile.get('name'):
        st.markdown(f"""
        <div style="background: rgba(76, 175, 80, 0.2); padding: 10px; border-radius: 10px; margin-bottom: 15px;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 1.5em;">👤</span>
                <div>
                    <strong style="color: #2e7d32;">{user_profile.get('name', 'User')}</strong>
                    <div style="font-size: 0.85em; color: #666;">{user_profile.get('profession', 'Gardener')}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: rgba(255, 255, 255, 0.95); padding: 15px; border-radius: 10px; border-left: 4px solid #2196f3; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <p style="color: #1b5e20; font-weight: 500; margin: 0; font-size: 1em;">👤 <strong>Please complete your profile</strong> to get started!</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Garden Stats Section
    st.markdown("### 📊 Garden Stats")
    if st.session_state.plants:
        total_plants = len(st.session_state.plants)
        
        # Calculate plants that need water
        needs_water_count = 0
        healthy_count = 0
        
        for plant in st.session_state.plants:
            # Check if plant needs water (simplified logic)
            last_watered = plant.get('last_watered')
            watering_interval = plant.get('watering_interval_days', 3)
            
            if last_watered:
                from datetime import datetime, timedelta
                try:
                    last_watered_date = datetime.fromisoformat(last_watered)
                    days_since_watered = (datetime.now() - last_watered_date).days
                    if days_since_watered >= watering_interval:
                        needs_water_count += 1
                    else:
                        healthy_count += 1
                except:
                    needs_water_count += 1
            else:
                needs_water_count += 1
        
        # Display stats
        st.metric("🌿 Total Plants", total_plants)
        
        st.markdown("---")
        
        # Need Water Box
        st.markdown(f"""
        <div style="background: rgba(255, 152, 0, 0.2); padding: 15px; border-radius: 10px; margin: 10px 0; border-left: 4px solid #ff9800;">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 5px;">
                <span style="font-size: 1.5em;">💧</span>
                <strong style="color: #f57c00;">Need Water</strong>
            </div>
            <div style="font-size: 2em; font-weight: bold; color: #f57c00;">{needs_water_count}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Healthy Plants
        st.markdown(f"""
        <div style="background: rgba(76, 175, 80, 0.2); padding: 15px; border-radius: 10px; margin: 10px 0; border-left: 4px solid #4caf50;">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 5px;">
                <span style="font-size: 1.5em;">✅</span>
                <strong style="color: #2e7d32;">Healthy</strong>
            </div>
            <div style="font-size: 2em; font-weight: bold; color: #2e7d32;">{healthy_count}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: rgba(255, 255, 255, 0.95); padding: 15px; border-radius: 10px; border-left: 4px solid #2196f3; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <p style="color: #1b5e20; font-weight: 500; margin: 0; font-size: 1em;">🌱 <strong>No plants yet!</strong> Add your first plant to see stats.</p>
        </div>
        """, unsafe_allow_html=True)
    

# ==========================================
# PAGE 1: WELCOME PAGE
# ==========================================
if page == "🏠 Welcome":
    st.markdown("""
    <div style="text-align: center; padding: 40px 20px;">
        <h1 style="color: #ffffff; text-shadow: 2px 2px 4px rgba(0,0,0,0.5); font-size: 3.5em; margin-bottom: 20px;">🌱 Smart Garden App</h1>
        <p style="color: #ffffff; font-size: 1.5em; margin-bottom: 40px; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);">Your AI-Powered Plant Care Companion</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Features Section
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="background: rgba(255, 255, 255, 0.7); padding: 30px; border-radius: 15px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.2); backdrop-filter: blur(10px);">
            <div style="font-size: 3em; margin-bottom: 15px;">🤖</div>
            <h3 style="color: #1b5e20; font-weight: bold;">AI Botanist</h3>
            <p style="color: #2e7d32; font-weight: 500;">Get instant answers about your plants with our AI-powered assistant</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: rgba(255, 255, 255, 0.7); padding: 30px; border-radius: 15px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.2); backdrop-filter: blur(10px);">
            <div style="font-size: 3em; margin-bottom: 15px;">🌤️</div>
            <h3 style="color: #1b5e20; font-weight: bold;">Weather Alerts</h3>
            <p style="color: #2e7d32; font-weight: 500;">Smart alerts based on real-time weather data for optimal plant care</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="background: rgba(255, 255, 255, 0.7); padding: 30px; border-radius: 15px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.2); backdrop-filter: blur(10px);">
            <div style="font-size: 3em; margin-bottom: 15px;">📊</div>
            <h3 style="color: #1b5e20; font-weight: bold;">Garden Dashboard</h3>
            <p style="color: #2e7d32; font-weight: 500;">Track all your plants' health, watering schedule, and care needs</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Getting Started Section
    st.markdown("""
    <div style="background: rgba(255, 255, 255, 0.7); padding: 30px; border-radius: 15px; margin-top: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); backdrop-filter: blur(10px);">
        <h2 style="color: #1b5e20; text-align: center; margin-bottom: 20px; font-weight: bold;">🚀 Getting Started</h2>
        <div style="display: flex; flex-direction: column; gap: 15px;">
            <div style="display: flex; align-items: start; gap: 15px;">
                <span style="font-size: 2em;">1️⃣</span>
                <div>
                    <h4 style="color: #1b5e20; margin: 0; font-weight: bold;">Complete Your Profile</h4>
                    <p style="color: #2e7d32; margin: 5px 0; font-weight: 500;">Go to User Profile and enter your information to personalize your experience</p>
                </div>
            </div>
            <div style="display: flex; align-items: start; gap: 15px;">
                <span style="font-size: 2em;">2️⃣</span>
                <div>
                    <h4 style="color: #1b5e20; margin: 0; font-weight: bold;">Add Your First Plant</h4>
                    <p style="color: #2e7d32; margin: 5px 0; font-weight: 500;">Upload a photo or manually add a plant to start tracking its care</p>
                </div>
            </div>
            <div style="display: flex; align-items: start; gap: 15px;">
                <span style="font-size: 2em;">3️⃣</span>
                <div>
                    <h4 style="color: #1b5e20; margin: 0; font-weight: bold;">Explore Dashboard</h4>
                    <p style="color: #2e7d32; margin: 5px 0; font-weight: 500;">View your garden stats, weather alerts, and plant health status</p>
                </div>
            </div>
            <div style="display: flex; align-items: start; gap: 15px;">
                <span style="font-size: 2em;">4️⃣</span>
                <div>
                    <h4 style="color: #1b5e20; margin: 0; font-weight: bold;">Ask AI Botanist</h4>
                    <p style="color: #2e7d32; margin: 5px 0; font-weight: 500;">Get instant plant care advice using our AI-powered chatbot</p>
                </div>
            </div>
            <div style="display: flex; align-items: start; gap: 15px;">
                <span style="font-size: 2em;">5️⃣</span>
                <div>
                    <h4 style="color: #1b5e20; margin: 0; font-weight: bold;">Locate Nearby Nurseries & Trace Location</h4>
                    <p style="color: #2e7d32; margin: 5px 0; font-weight: 500;">Set your location and find nearby plant nurseries to buy new plants easily</p>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Footer with Credits
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background: rgba(27, 94, 32, 0.8); padding: 30px; border-radius: 15px; text-align: center; margin-top: 50px;">
        <h3 style="color: #ffffff; margin-bottom: 15px;">🌱 Smart Garden App</h3>
        <p style="color: #ffffff; font-size: 1.1em; margin: 10px 0;">
            <strong>Powered by:</strong> Haseeb, Zahra Zahid, Maira, and Zahra Mumtaz
        </p>
        <p style="color: rgba(255, 255, 255, 0.8); font-size: 0.9em; margin-top: 20px;">
            Built with ❤️ for plant lovers everywhere
        </p>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# PAGE 2: USER PROFILE
# ==========================================
elif page == "👤 User Profile":
    st.markdown('<h1 style="color: #ffffff; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">👤 User Profile</h1>', unsafe_allow_html=True)
    
    # Get current profile
    user_profile = data_manager.get_user_profile()
    
    # Profile Form
    with st.form("user_profile_form"):
        st.markdown("### 📝 Enter Your Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input(
                "Full Name *",
                value=user_profile.get('name', ''),
                placeholder="Enter your full name"
            )
            email = st.text_input(
                "Email Address *",
                value=user_profile.get('email', ''),
                placeholder="your.email@example.com"
            )
            phone = st.text_input(
                "Phone Number",
                value=user_profile.get('phone', ''),
                placeholder="+92 300 1234567"
            )
        
        with col2:
            profession = st.text_input(
                "Profession",
                value=user_profile.get('profession', ''),
                placeholder="e.g., Software Engineer, Teacher, etc."
            )
            location = st.text_input(
                "Location",
                value=user_profile.get('location', DEFAULT_CITY),
                placeholder="Your city"
            )
        
        st.markdown("<small>* Required fields</small>", unsafe_allow_html=True)
        
        submitted = st.form_submit_button("💾 Save Profile", use_container_width=True)
        
        if submitted:
            if name and email:
                profile_data = {
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "profession": profession,
                    "location": location,
                    "created_at": user_profile.get('created_at', datetime.now().isoformat())
                }
                saved_profile = data_manager.save_user_profile(profile_data)
                st.success("✅ Profile saved successfully!")
                st.balloons()
                st.markdown("""
                <div style="background: rgba(255, 255, 255, 0.95); padding: 15px; border-radius: 10px; border-left: 4px solid #4caf50; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <p style="color: #1b5e20; font-weight: 500; margin: 0; font-size: 1em;">💡 <strong>Your profile has been updated.</strong> You can now enjoy personalized plant care recommendations!</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background: rgba(255, 255, 255, 0.95); padding: 15px; border-radius: 10px; border-left: 4px solid #f44336; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <p style="color: #1b5e20; font-weight: 500; margin: 0; font-size: 1em;">❌ <strong>Please fill in at least Name and Email fields.</strong></p>
                </div>
                """, unsafe_allow_html=True)
    
    # Display Current Profile
    if user_profile.get('name'):
        st.markdown("---")
        st.markdown("### 👤 Current Profile")
        st.markdown(f"""
        <div style="background: rgba(255, 255, 255, 0.95); padding: 25px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
            <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 20px;">
                <div style="font-size: 3em; background: linear-gradient(135deg, #4caf50 0%, #66bb6a 100%); width: 80px; height: 80px; border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                    👤
                </div>
                <div>
                    <h2 style="color: #2e7d32; margin: 0;">{user_profile.get('name', 'User')}</h2>
                    <p style="color: #666; margin: 5px 0;">{user_profile.get('profession', 'Gardener')}</p>
                </div>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 20px;">
                <div>
                    <strong style="color: #2e7d32;">📧 Email:</strong>
                    <p style="color: #666; margin: 5px 0;">{user_profile.get('email', 'N/A')}</p>
                </div>
                <div>
                    <strong style="color: #2e7d32;">📱 Phone:</strong>
                    <p style="color: #666; margin: 5px 0;">{user_profile.get('phone', 'N/A')}</p>
                </div>
                <div>
                    <strong style="color: #2e7d32;">📍 Location:</strong>
                    <p style="color: #666; margin: 5px 0;">{user_profile.get('location', 'N/A')}</p>
                </div>
                <div>
                    <strong style="color: #2e7d32;">📅 Member Since:</strong>
                    <p style="color: #666; margin: 5px 0;">{user_profile.get('created_at', 'N/A')[:10] if user_profile.get('created_at') else 'N/A'}</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# PAGE 3: LOCATION & NURSERIES
# ==========================================
elif page == "📍 Location & Nurseries":
    st.markdown('<h1 style="color: #ffffff; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">📍 Location & Nurseries</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: #1b5e20; font-size: 1.1em;">Set your location and find nearby plant nurseries to buy new plants!</p>', unsafe_allow_html=True)
    
    # Location Detection Section
    st.markdown("### 🌍 Your Current Location")
    
    col_loc1, col_loc2 = st.columns([2, 1])
    
    with col_loc1:
        # Auto-detect location toggle
        use_auto = st.checkbox("📍 Auto-Detect My Location", value=st.session_state.use_auto_location, help="Automatically detect your location using IP address")
        
        if use_auto:
            st.session_state.use_auto_location = True
            if st.button("🔍 Detect Location", use_container_width=True):
                with st.spinner("Detecting your location..."):
                    location_data = get_current_location()
                    st.session_state.user_location = location_data
                    st.success(f"✅ Location detected: {location_data['city']}, {location_data['country']}")
        else:
            st.session_state.use_auto_location = False
    
    with col_loc2:
        # Manual location input
        st.markdown("**Or enter manually:**")
        manual_city = st.text_input("City", value=st.session_state.user_location.get('city', DEFAULT_CITY))
        manual_country = st.text_input("Country", value=st.session_state.user_location.get('country', DEFAULT_COUNTRY))
        
        if st.button("💾 Save Location", use_container_width=True):
            st.session_state.user_location = {
                "city": manual_city,
                "country": manual_country,
                "lat": st.session_state.user_location.get('lat'),
                "lon": st.session_state.user_location.get('lon')
            }
            st.success(f"✅ Location saved: {manual_city}, {manual_country}")
    
    # Display current location
    current_loc = st.session_state.user_location
    st.markdown(f"""
    <div style="background: rgba(255, 255, 255, 0.7); padding: 20px; border-radius: 15px; margin: 20px 0; backdrop-filter: blur(10px);">
        <h3 style="color: #1b5e20; margin-bottom: 10px;">📍 Current Location</h3>
        <p style="color: #2e7d32; font-size: 1.2em; font-weight: bold;">
            {current_loc.get('city', DEFAULT_CITY)}, {current_loc.get('country', DEFAULT_COUNTRY)}
        </p>
        {f"<p style='color: #666; font-size: 0.9em;'>Coordinates: {current_loc.get('lat', 'N/A')}, {current_loc.get('lon', 'N/A')}</p>" if current_loc.get('lat') else ""}
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Map Selection Section
    st.markdown("### 🗺️ Select Location on Map")
    st.markdown("""
    <div style="background: rgba(255, 255, 255, 0.95); padding: 15px; border-radius: 10px; border-left: 4px solid #2196f3; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        <p style="color: #1b5e20; font-weight: 500; margin: 0; font-size: 1em;">💡 <strong>Tip:</strong> Enter coordinates or use the map to select your exact location for better nursery recommendations</p>
    </div>
    """, unsafe_allow_html=True)
    
    col_map1, col_map2 = st.columns(2)
    
    with col_map1:
        map_lat = st.number_input("Latitude", value=current_loc.get('lat') or 32.4945, min_value=-90.0, max_value=90.0, step=0.0001, format="%.4f")
        map_lon = st.number_input("Longitude", value=current_loc.get('lon') or 74.5229, min_value=-180.0, max_value=180.0, step=0.0001, format="%.4f")
        
        if st.button("📍 Set Map Location", use_container_width=True):
            st.session_state.user_location['lat'] = map_lat
            st.session_state.user_location['lon'] = map_lon
            st.success(f"✅ Location set: {map_lat}, {map_lon}")
            st.rerun()
    
    with col_map2:
        # Simple map display using HTML/iframe (free, no API key needed)
        st.markdown("**📍 Your Location on Map**")
        if current_loc.get('lat') and current_loc.get('lon'):
            map_url = f"https://www.openstreetmap.org/export/embed.html?bbox={current_loc['lon']-0.01},{current_loc['lat']-0.01},{current_loc['lon']+0.01},{current_loc['lat']+0.01}&layer=mapnik&marker={current_loc['lat']},{current_loc['lon']}"
            st.markdown(f"""
            <iframe width="100%" height="300" frameborder="0" scrolling="no" marginheight="0" marginwidth="0" 
            src="{map_url}" style="border: 1px solid #ccc; border-radius: 10px;"></iframe>
            <br><small><a href="https://www.openstreetmap.org/?mlat={current_loc['lat']}&mlon={current_loc['lon']}&zoom=14" target="_blank">View Larger Map</a></small>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: rgba(255, 255, 255, 0.95); padding: 15px; border-radius: 10px; border-left: 4px solid #2196f3; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <p style="color: #1b5e20; font-weight: 500; margin: 0; font-size: 1em;">📍 <strong>Set coordinates above</strong> to view on map</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Nearby Nurseries Section
    st.markdown("### 🌿 Nearby Plant Nurseries")
    
    if current_loc.get('lat') and current_loc.get('lon'):
        # Find nearby nurseries
        with st.spinner("🔍 Finding nearby nurseries..."):
            nurseries = find_nearby_nurseries(current_loc['lat'], current_loc['lon'])
        
        if nurseries:
            st.success(f"✅ Found {len(nurseries)} nurseries near you!")
            
            # Display nurseries in cards
            for idx, nursery in enumerate(nurseries):
                st.markdown(f"""
                <div style="background: rgba(255, 255, 255, 0.7); padding: 20px; border-radius: 15px; margin: 15px 0; backdrop-filter: blur(10px); box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
                        <div>
                            <h3 style="color: #1b5e20; margin: 0;">🌱 {nursery['name']}</h3>
                            <p style="color: #666; margin: 5px 0;">📍 {nursery['address']}</p>
                        </div>
                        <div style="text-align: right;">
                            <div style="background: #4caf50; color: white; padding: 5px 10px; border-radius: 20px; font-weight: bold; margin-bottom: 5px;">
                                ⭐ {nursery['rating']}
                            </div>
                            <div style="color: #2e7d32; font-weight: bold;">📏 {nursery['distance']}</div>
                        </div>
                    </div>
                    <div style="display: flex; gap: 15px; margin-top: 15px;">
                        <div style="flex: 1;">
                            <strong style="color: #1b5e20;">📞 Phone:</strong>
                            <p style="color: #666; margin: 5px 0;">{nursery['phone']}</p>
                        </div>
                        <div style="flex: 1;">
                            <strong style="color: #1b5e20;">📍 Distance:</strong>
                            <p style="color: #666; margin: 5px 0;">{nursery['distance']} away</p>
                        </div>
                    </div>
                    <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #e0e0e0;">
                        <a href="https://www.google.com/maps/search/?api=1&query={nursery['lat']},{nursery['lon']}" target="_blank" 
                        style="background: linear-gradient(135deg, #4caf50 0%, #66bb6a 100%); color: white; padding: 10px 20px; border-radius: 8px; text-decoration: none; display: inline-block; font-weight: bold;">
                        🗺️ Get Directions
                        </a>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: rgba(255, 255, 255, 0.95); padding: 15px; border-radius: 10px; border-left: 4px solid #ff9800; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <p style="color: #1b5e20; font-weight: 500; margin: 0; font-size: 1em;">⚠️ <strong>No nurseries found nearby.</strong> Try adjusting your location.</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: rgba(255, 255, 255, 0.95); padding: 15px; border-radius: 10px; border-left: 4px solid #2196f3; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <p style="color: #1b5e20; font-weight: 500; margin: 0; font-size: 1em;">📍 <strong>Please set your location coordinates above</strong> to find nearby nurseries</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Tips Section
    st.markdown("---")
    st.markdown("### 💡 Tips for Buying Plants")
    st.markdown("""
    <div style="background: rgba(255, 255, 255, 0.7); padding: 20px; border-radius: 15px; backdrop-filter: blur(10px);">
        <ul style="color: #2e7d32; line-height: 2;">
            <li>🌱 <strong>Check plant health:</strong> Look for vibrant leaves and healthy roots</li>
            <li>💧 <strong>Ask about care:</strong> Nursery staff can provide specific care instructions</li>
            <li>🌡️ <strong>Consider your climate:</strong> Choose plants suitable for your local weather</li>
            <li>📅 <strong>Best time to buy:</strong> Spring and early fall are ideal for most plants</li>
            <li>💰 <strong>Compare prices:</strong> Visit multiple nurseries for the best deals</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# PAGE 4: GARDEN DASHBOARD
# ==========================================
elif page == "📊 Garden Dashboard":
    st.markdown('<h1 style="color: #ffffff; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">🌿 My Garden Dashboard</h1>', unsafe_allow_html=True)
    
    # Get Current Weather - Use user location if available
    user_city = st.session_state.user_location.get('city', DEFAULT_CITY)
    user_country = st.session_state.user_location.get('country', DEFAULT_COUNTRY)
    
    # Fix: If location is "The Dalles" (cloud provider default), use default location
    if user_city in ["The Dalles", "Dalles"]:
        user_city = DEFAULT_CITY
        user_country = DEFAULT_COUNTRY
        st.session_state.user_location = {"city": DEFAULT_CITY, "country": DEFAULT_COUNTRY, "lat": None, "lon": None, "country_code": "PK"}
        st.info("📍 Location set to default. Please set your location manually on the 'Location & Nurseries' page.")
    
    # Cache weather data to prevent repeated API calls
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def get_weather_data(city, country):
        return {
            'current': weather_service.get_current_weather(city, country),
            'forecast': weather_service.get_forecast(city, country, days=2),
            'rain_alert': weather_service.check_rain_alert(city, country, hours_ahead=24),
            'storm_alert': weather_service.check_storm_alert(city, country, hours_ahead=24)
        }
    
    with st.spinner("Loading weather data..."):
        weather_data = get_weather_data(user_city, user_country)
        current_weather = weather_data['current']
        forecast = weather_data['forecast']
        rain_alert = weather_data['rain_alert']
        storm_alert = weather_data['storm_alert']
    
    # Weather Banner with Animated Sun/Moon
    col1, col2, col3 = st.columns([2.5, 1, 1])
    
    # Determine if it's day or night
    current_hour = datetime.now().hour
    sunrise = current_weather.get('sunrise')
    sunset = current_weather.get('sunset')
    is_daytime = True
    
    if sunrise and sunset:
        sunrise_hour = sunrise.hour
        sunset_hour = sunset.hour
        is_daytime = sunrise_hour <= current_hour <= sunset_hour
    
    # Animated Sun/Moon based on time
    if is_daytime:
        sun_moon_icon = """
        <div style="text-align: center;">
            <span class="animated-sun" style="font-size: 4em;">☀️</span>
        </div>
        """
    else:
        sun_moon_icon = """
        <div style="text-align: center;">
            <span class="animated-moon" style="font-size: 4em;">🌙</span>
        </div>
        """
    
    with col1:
        weather_icon = current_weather.get('icon', '01d')
        temp = current_weather.get('temperature', 25)
        condition = current_weather.get('description', 'clear sky').title()
        feels_like = current_weather.get('feels_like', temp)
        humidity = current_weather.get('humidity', 60)
        cloud_cover = current_weather.get('cloud_cover', 0)
        
        st.markdown(f"""
        <div class="weather-banner">
            <h2>🌤️ {user_city} Weather</h2>
            <h1 style="font-size: 3em; margin: 10px 0;">{temp}°C</h1>
            <p style="font-size: 1.2em;">{condition} • Feels like {feels_like}°C</p>
            <p>💧 Humidity: {humidity}% • ☁️ Cloud Cover: {cloud_cover}%</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(sun_moon_icon, unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 10px; text-align: center; margin-top: 10px;">
            <div style="font-size: 0.9em; color: white; font-weight: bold;">Wind Speed</div>
            <div style="font-size: 1.5em; color: white; margin-top: 5px;">{current_weather.get('wind_speed', 0)} m/s</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        if sunrise and sunset:
            st.markdown(f"""
            <div style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 10px; text-align: center;">
                <div style="font-size: 1.2em; margin-bottom: 10px;">🌅</div>
                <div style="font-size: 0.9em; color: white; font-weight: bold;">Sunrise</div>
                <div style="font-size: 1.3em; color: white; margin-top: 5px;">{sunrise.strftime('%H:%M')}</div>
                <div style="font-size: 1.2em; margin: 15px 0 10px 0;">🌇</div>
                <div style="font-size: 0.9em; color: white; font-weight: bold;">Sunset</div>
                <div style="font-size: 1.3em; color: white; margin-top: 5px;">{sunset.strftime('%H:%M')}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 10px; text-align: center;">
                <div style="color: white;">Time data unavailable</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Alerts Section
    st.markdown('<h3 style="color: #1b5e20;">🚨 Alerts & Notifications</h3>', unsafe_allow_html=True)
    
    # Rain Alert
    if rain_alert.get('has_rain'):
        next_rain = rain_alert.get('next_rain')
        if next_rain:
            hours = next_rain.get('hours_from_now', 0)
            alert_msg = groq_service.generate_alert_message(
                "rain", 
                "your plants", 
                current_weather
            )
            st.markdown(f"""
            <div style="background: rgba(255, 255, 255, 0.95); padding: 15px; border-radius: 10px; border-left: 4px solid #ff9800; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <p style="color: #1b5e20; font-weight: 500; margin: 0; font-size: 1em;">🌧️ <strong>RAIN ALERT:</strong> {alert_msg}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Storm Alert
    if storm_alert.get('has_storm'):
        next_storm = storm_alert.get('next_storm')
        if next_storm:
            hours = next_storm.get('hours_from_now', 0)
            alert_msg = groq_service.generate_alert_message(
                "storm",
                "your outdoor plants",
                current_weather
            )
            st.markdown(f"""
            <div style="background: rgba(255, 255, 255, 0.95); padding: 15px; border-radius: 10px; border-left: 4px solid #f44336; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <p style="color: #1b5e20; font-weight: 500; margin: 0; font-size: 1em;">⚠️ <strong>STORM ALERT:</strong> {alert_msg}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Heat Alert
    if current_weather.get('temperature', 0) > 35:
        alert_msg = groq_service.generate_alert_message(
            "heat",
            "your plants",
            current_weather
        )
        st.markdown(f"""
        <div style="background: rgba(255, 255, 255, 0.95); padding: 15px; border-radius: 10px; border-left: 4px solid #ff9800; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <p style="color: #1b5e20; font-weight: 500; margin: 0; font-size: 1em;">☀️ <strong>HEAT ALERT:</strong> {alert_msg}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Plants Section
    st.markdown('<h3 style="color: #1b5e20;">🌿 Your Plants</h3>', unsafe_allow_html=True)
    
    if not st.session_state.plants:
        st.markdown("""
        <div style="background: rgba(255, 255, 255, 0.95); padding: 15px; border-radius: 10px; border-left: 4px solid #2196f3; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <p style="color: #1b5e20; font-weight: 500; margin: 0; font-size: 1em;">🌱 <strong>No plants yet!</strong> Go to 'Add a Plant' to start your garden.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Refresh plants from database
        st.session_state.plants = data_manager.get_all_plants()
        
        # Responsive grid: 2 columns for better card visibility
        num_cols = min(2, len(st.session_state.plants)) if len(st.session_state.plants) > 0 else 1
        cols = st.columns(num_cols)
        
        for idx, plant in enumerate(st.session_state.plants):
            with cols[idx % num_cols]:
                # Calculate watering status
                watering_status = plant_service.calculate_watering_schedule(
                    plant.get('name', 'Plant'),
                    plant.get('watering_interval_days', 3),
                    plant.get('last_watered'),
                    current_weather,
                    forecast
                )
                
                # Get sun exposure estimate
                sun_exposure = weather_service.get_sun_exposure_estimate(
                    plant.get('placement', 'Indoor Window'),
                    current_weather,
                    plant.get('sun_preference', 'Morning Sun')
                )
                
                # Determine water status
                if watering_status.get('needs_water'):
                    if watering_status.get('urgency') == 'high':
                        water_status = "Needs Water Today"
                        water_color = "#f57c00"  # Orange
                    else:
                        water_status = "Water Soon"
                        water_color = "#ff9800"  # Light orange
                else:
                    water_status = "Well Watered"
                    water_color = "#4caf50"  # Green
                
                # Get sun hours and create progress bar
                sun_hours = sun_exposure.get('sun_hours', 0)
                max_sun_hours = 8  # Maximum expected sun hours
                sun_percentage = min(100, (sun_hours / max_sun_hours) * 100) if max_sun_hours > 0 else 0
                
                # Temperature status
                temp = current_weather.get('temperature', 25)
                if temp > 35:
                    temp_status = "Too Hot!"
                    temp_color = "#f44336"  # Red
                elif temp > 30:
                    temp_status = "Warm"
                    temp_color = "#ff9800"  # Orange
                elif temp < 15:
                    temp_status = "Too Cold"
                    temp_color = "#2196f3"  # Blue
                else:
                    temp_status = "Comfortable"
                    temp_color = "#4caf50"  # Green
                
                # Plant category (simple detection)
                plant_name_lower = plant.get('name', '').lower()
                if any(word in plant_name_lower for word in ['rose', 'flower', 'lily', 'tulip', 'daisy']):
                    category = "🌸 Flower"
                    category_color = "#e91e63"
                elif any(word in plant_name_lower for word in ['tree', 'oak', 'pine', 'maple']):
                    category = "🌳 Tree"
                    category_color = "#8bc34a"
                else:
                    category = "🌱 Plant"
                    category_color = "#4caf50"
                
                # Check for weather alerts for this plant
                placement = plant.get('placement', '')
                weather_alert = ""
                if 'Outdoor' in placement or 'Open Roof' in placement or 'Balcony' in placement:
                    if storm_alert.get('has_storm'):
                        weather_alert = '<div style="background: #ffebee; border-left: 4px solid #f44336; padding: 8px; margin: 10px 0; border-radius: 4px;"><strong>⚠️ Storm Alert:</strong> Move indoors!</div>'
                    elif rain_alert.get('has_rain'):
                        weather_alert = '<div style="background: #fff3e0; border-left: 4px solid #ff9800; padding: 8px; margin: 10px 0; border-radius: 4px;"><strong>🌧️ Rain Alert:</strong> Consider shelter</div>'
                    elif temp > 35:
                        weather_alert = '<div style="background: #fff3e0; border-left: 4px solid #ff9800; padding: 8px; margin: 10px 0; border-radius: 4px;"><strong>☀️ Heat Alert:</strong> Provide extra water</div>'
                
                # Plant Card using Streamlit components (no HTML code boxes)
                # Wrap in a styled container
                st.markdown('<div class="plant-card">', unsafe_allow_html=True)
                
                # Display weather alert if exists
                if weather_alert:
                    st.markdown(weather_alert, unsafe_allow_html=True)
                
                # Plant name and category
                col_name, col_cat = st.columns([3, 1])
                with col_name:
                    st.markdown(f"### {plant.get('name', 'Unknown Plant')}")
                with col_cat:
                    st.markdown(f'<span style="background: {category_color}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.85em; font-weight: bold;">{category}</span>', unsafe_allow_html=True)
                
                # Location
                st.caption(f"📍 {plant.get('placement', 'Unknown Location')}")
                
                # Status indicators in a styled box
                st.markdown(f"""
                <div style="background: #f5f5f5; padding: 12px; border-radius: 8px; margin: 10px 0;">
                    <div style="margin-bottom: 10px;">
                        <div style="display: flex; justify-content: space-between;">
                            <span style="font-weight: bold; color: #333;">💧 Water Status:</span>
                            <span style="color: {water_color}; font-weight: bold;">{water_status}</span>
                        </div>
                    </div>
                    <div style="margin-bottom: 10px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                            <span style="font-weight: bold; color: #333;">☀️ Sunlight:</span>
                            <span style="color: #333;">Getting {sun_hours}hrs sun</span>
                        </div>
                    </div>
                    <div>
                        <div style="display: flex; justify-content: space-between;">
                            <span style="font-weight: bold; color: #333;">🌡 Temperature:</span>
                            <span style="color: {temp_color}; font-weight: bold;">{temp_status}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Sunlight progress bar
                st.progress(sun_percentage / 100)
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Quick action buttons
                col_btn1, col_btn2, col_btn3 = st.columns(3)
                with col_btn1:
                    if st.button("💬 Ask AI", key=f"ask_{plant.get('id')}", use_container_width=True):
                        # Store plant name for AI Botanist context
                        plant_name = plant.get('name')
                        st.session_state.selected_plant = plant_name
                        st.session_state.ask_about_plant = plant_name
                        # Set flag to switch page (will be processed before widget creation on rerun)
                        st.session_state.switch_to_page = "🤖 AI Botanist"
                        st.rerun()
                
                with col_btn2:
                    if st.button("💧 Water", key=f"water_{plant.get('id')}", use_container_width=True):
                        data_manager.mark_watered(plant.get('id'))
                        st.session_state.plants = data_manager.get_all_plants()
                        st.success(f"✅ {plant.get('name')} marked as watered!")
                        st.rerun()
                
                with col_btn3:
                    if st.button("🗑️ Remove", key=f"remove_{plant.get('id')}", use_container_width=True):
                        data_manager.delete_plant(plant.get('id'))
                        st.session_state.plants = data_manager.get_all_plants()
                        st.success(f"🗑️ {plant.get('name')} removed")
                        st.rerun()
                
                st.markdown("---")

# ==========================================
# PAGE 2: ADD A PLANT
# ==========================================
elif page == "🌱 Add a Plant":
    st.markdown('<h1 style="color: #ffffff; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">🌱 Add a New Plant</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: #1b5e20; font-size: 1.1em;">Upload a photo and let AI identify your plant, or add it manually.</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        st.markdown("### 📷 Plant Photo")
        uploaded_file = st.file_uploader(
            "Upload a clear photo of your plant",
            type=['jpg', 'jpeg', 'png'],
            help="Take or upload a clear photo for best AI identification results"
        )
        
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="Your Plant", use_container_width=True)
            
            if st.button("🔍 Identify with AI", type="primary", use_container_width=True):
                with st.spinner("🤖 Hugging Face AI is identifying your plant..."):
                    identification = huggingface_service.identify_plant(image)
                    
                    # Store in session state for form
                    plant_name = identification.get('plant_name', '')
                    st.session_state.identified_name = plant_name
                    st.session_state.identified_scientific = identification.get('scientific_name', '')
                    st.session_state.identified_description = identification.get('description', '')
                    st.session_state.identified_care_level = identification.get('care_level', 'Moderate')
                    
                    # Show full response for debugging
                    full_response = identification.get('full_response', '')
                    if full_response:
                        with st.expander("🔍 View AI Analysis Details", expanded=False):
                            st.text(full_response)
                    
                    st.success(f"✅ Plant Identified: **{plant_name}**")
                    st.markdown(f"""
                    <div style="background: rgba(255, 255, 255, 0.95); padding: 15px; border-radius: 10px; border-left: 4px solid #2196f3; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                        <p style="color: #1b5e20; font-weight: 500; margin: 0; font-size: 1em;"><strong>{plant_name}</strong></p>
                        <p style="color: #2e7d32; margin: 10px 0 0 0; font-size: 0.95em;">{identification.get('description', '')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Warning if it says Rose but might be wrong
                    if 'rose' in plant_name.lower() and ('tomato' in full_response.lower() or 'solanum' in full_response.lower()):
                        st.markdown("""
                        <div style="background: rgba(255, 255, 255, 0.95); padding: 15px; border-radius: 10px; border-left: 4px solid #ff9800; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                            <p style="color: #1b5e20; font-weight: 500; margin: 0; font-size: 1em;">⚠️ <strong>The AI response mentions tomato but identified as Rose.</strong> Please verify the identification is correct.</p>
                        </div>
                        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 📝 Plant Details")
        
        with st.form("add_plant_form", clear_on_submit=True):
            # Pre-fill with AI identification if available
            plant_name = st.text_input(
                "Plant Name *",
                value=st.session_state.get('identified_name', ''),
                help="Common name of your plant"
            )
            
            scientific_name = st.text_input(
                "Scientific Name",
                value=st.session_state.get('identified_scientific', ''),
                help="Optional scientific name"
            )
            
            description = st.text_area(
                "Description",
                value=st.session_state.get('identified_description', ''),
                help="Any notes about this plant"
            )
            
            col_form1, col_form2 = st.columns(2)
            
            with col_form1:
                placement = st.selectbox(
                    "Where is it placed? *",
                    ["Open Roof", "Balcony", "Indoor Window"],
                    help="Location affects sun exposure calculations"
                )
            
            with col_form2:
                sun_preference = st.selectbox(
                    "Sun Exposure *",
                    ["Morning Sun", "Afternoon Shade", "Full Sun"],
                    help="How much direct sunlight does it get?"
                )
            
            watering_interval = st.slider(
                "Watering Interval (Days) *",
                min_value=1,
                max_value=14,
                value=3,
                help="How often should this plant be watered?"
            )
            
            location = st.text_input(
                "Location (City)",
                value=DEFAULT_CITY,
                help="City where this plant is located"
            )
            
            notes = st.text_area(
                "Additional Notes",
                help="Any special care instructions or notes"
            )
            
            submitted = st.form_submit_button("✅ Add Plant to Garden", type="primary", use_container_width=True)
            
            if submitted:
                if not plant_name:
                    st.markdown("""
                    <div style="background: rgba(255, 255, 255, 0.95); padding: 15px; border-radius: 10px; border-left: 4px solid #f44336; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                        <p style="color: #1b5e20; font-weight: 500; margin: 0; font-size: 1em;">❌ <strong>Please enter a plant name</strong></p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # Save image if uploaded
                    image_path = ""
                    if uploaded_file:
                        # Create images directory if it doesn't exist
                        os.makedirs("plant_images", exist_ok=True)
                        image_path = f"plant_images/{plant_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                        image.save(image_path)
                    
                    # Create plant data
                    plant_data = {
                        "name": plant_name,
                        "scientific_name": scientific_name,
                        "description": description,
                        "care_level": st.session_state.get('identified_care_level', 'Moderate'),
                        "location": location,
                        "placement": placement,
                        "sun_preference": sun_preference,
                        "watering_interval_days": watering_interval,
                        "last_watered": None,  # Will be set when first watered
                        "image_path": image_path,
                        "notes": notes
                    }
                    
                    # Save to database
                    new_plant = data_manager.add_plant(plant_data)
                    st.session_state.plants = data_manager.get_all_plants()
                    
                    # Clear session state
                    if 'identified_name' in st.session_state:
                        del st.session_state.identified_name
                    
                    st.balloons()
                    st.success(f"🌱 **{plant_name}** has been added to your garden!")
                    st.markdown("""
                    <div style="background: rgba(255, 255, 255, 0.95); padding: 15px; border-radius: 10px; border-left: 4px solid #2196f3; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                        <p style="color: #1b5e20; font-weight: 500; margin: 0; font-size: 1em;">💡 <strong>Tip:</strong> Go to Dashboard to see your plant's care status and alerts.</p>
                    </div>
                    """, unsafe_allow_html=True)

# ==========================================
# PAGE 3: AI BOTANIST CHAT
# ==========================================
elif page == "🤖 AI Botanist":
    st.markdown('<h1 style="color: #ffffff; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">🤖 AI Botanist Chat</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: #1b5e20; font-size: 1.1em;">Ask me anything about your plants! Upload a photo for health diagnosis or use voice commands.</p>', unsafe_allow_html=True)
    
    # Show selected plant context if coming from Ask AI button
    if 'ask_about_plant' in st.session_state and st.session_state.ask_about_plant:
        plant_name = st.session_state.ask_about_plant
        st.success(f"💬 You're asking about **{plant_name}**. Ask any question about this plant below!")
        # Pre-fill a suggested question
        suggested_question = f"How is my {plant_name} doing?"
        st.markdown(f"""
        <div style="background: rgba(255, 255, 255, 0.95); padding: 15px; border-radius: 10px; border-left: 4px solid #2196f3; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <p style="color: #1b5e20; font-weight: 500; margin: 0; font-size: 1em;">💡 <strong>Suggested question:</strong> <em>'{suggested_question}'</em> - Type this or ask your own question!</p>
        </div>
        """, unsafe_allow_html=True)
        # Store for potential auto-fill (optional)
        if 'prefill_question' not in st.session_state:
            st.session_state.prefill_question = suggested_question
    
    # Voice Command Interface - Native Streamlit Audio Input
    st.markdown("### 🎤 Voice Command")
    st.markdown("**Speak your question instead of typing!** Try: *'How is my Rose doing?'* or *'Why are my leaves yellow?'*")
    
    # Native Streamlit Audio Input (No FFmpeg required, works out of the box)
    audio_value = st.audio_input("🎤 Record your question", label_visibility="visible")
    
    if audio_value:
        # Play back for confirmation
        st.audio(audio_value, format="audio/wav")
        
        # Process audio with speech recognition
        if SPEECH_RECOGNITION_AVAILABLE:
            with st.spinner("🎤 Transcribing your voice..."):
                try:
                    # Initialize Recognizer
                    recognizer = sr.Recognizer()
                    
                    # Convert the Streamlit audio file to data SpeechRecognition can read
                    # Streamlit audio_input returns a BytesIO-like object
                    with sr.AudioFile(audio_value) as source:
                        # Adjust for ambient noise
                        recognizer.adjust_for_ambient_noise(source, duration=0.5)
                        audio_data = recognizer.record(source)
                    
                    # Use Google's Free Speech API
                    try:
                        voice_text = recognizer.recognize_google(audio_data)
                        st.session_state.voice_question = voice_text
                        st.success(f"🗣️ **You said:** {voice_text}")
                        st.balloons()
                        st.markdown("""
                        <div style="background: rgba(255, 255, 255, 0.95); padding: 15px; border-radius: 10px; border-left: 4px solid #2196f3; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                            <p style="color: #1b5e20; font-weight: 500; margin: 0; font-size: 1em;">💡 <strong>Your question is ready!</strong> Scroll down to see the response.</p>
                        </div>
                        """, unsafe_allow_html=True)
                    except sr.UnknownValueError:
                        st.markdown("""
                        <div style="background: rgba(255, 255, 255, 0.95); padding: 15px; border-radius: 10px; border-left: 4px solid #ff9800; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                            <p style="color: #1b5e20; font-weight: 500; margin: 0; font-size: 1em;">⚠️ <strong>Could not understand audio.</strong> Please speak more clearly and try again.</p>
                        </div>
                        """, unsafe_allow_html=True)
                    except sr.RequestError as e:
                        st.markdown(f"""
                        <div style="background: rgba(255, 255, 255, 0.95); padding: 15px; border-radius: 10px; border-left: 4px solid #f44336; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                            <p style="color: #1b5e20; font-weight: 500; margin: 0; font-size: 1em;">❌ <strong>Could not reach Google Speech service:</strong> {e}. Please try typing your question instead.</p>
                        </div>
                        """, unsafe_allow_html=True)
                    except Exception as e:
                        st.markdown(f"""
                        <div style="background: rgba(255, 255, 255, 0.95); padding: 15px; border-radius: 10px; border-left: 4px solid #f44336; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                            <p style="color: #1b5e20; font-weight: 500; margin: 0; font-size: 1em;">❌ <strong>Error processing audio:</strong> {e}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                except Exception as e:
                    error_msg = str(e)
                    st.markdown(f"""
                    <div style="background: rgba(255, 255, 255, 0.95); padding: 15px; border-radius: 10px; border-left: 4px solid #f44336; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                        <p style="color: #1b5e20; font-weight: 500; margin: 0; font-size: 1em;">❌ <strong>Error processing audio:</strong> {error_msg}</p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: rgba(255, 255, 255, 0.95); padding: 15px; border-radius: 10px; border-left: 4px solid #2196f3; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <p style="color: #1b5e20; font-weight: 500; margin: 0; font-size: 1em;">💡 <strong>Speech recognition requires:</strong> SpeechRecognition. Install with: <code>pip install SpeechRecognition</code></p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Display chat history
    chat_container = st.container()
    
    with chat_container:
        for chat in st.session_state.chat_history[-10:]:  # Show last 10 messages
            if chat.get('user_message'):
                with st.chat_message("user"):
                    st.write(chat['user_message'])
            
            if chat.get('bot_response'):
                with st.chat_message("assistant"):
                    st.write(chat['bot_response'])
    
    # Check if voice question exists
    voice_question = st.session_state.get('voice_question', None)
    
    # Chat input
    typed_question = st.chat_input("Ask about your plants (e.g., 'Why are my leaves turning yellow?')")
    
    # Use voice question if available, otherwise use typed question
    user_question = voice_question if voice_question else typed_question
    
    if user_question:
        # Clear voice question after using it
        if 'voice_question' in st.session_state:
            del st.session_state.voice_question
        # Add user message to chat
        with st.chat_message("user"):
            st.write(user_question)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("🤖 AI Botanist is thinking..."):
                # Initialize plants_context for chat history
                plants_context = ""
                if st.session_state.plants:
                    plant_names = [p.get('name', '') for p in st.session_state.plants]
                    plants_context = f"User's plants: {', '.join(plant_names)}"
                
                # Add selected plant context if user came from Ask AI button
                selected_plant_context = ""
                if 'selected_plant' in st.session_state and st.session_state.selected_plant:
                    selected_plant = st.session_state.selected_plant
                    selected_plant_context = f"\n\nIMPORTANT: The user is specifically asking about their '{selected_plant}' plant. Focus your answer on this plant."
                    # Find plant details if available
                    for p in st.session_state.plants:
                        if p.get('name') == selected_plant:
                            selected_plant_context += f"\n\nPlant Details:\n- Name: {p.get('name')}\n- Placement: {p.get('placement', 'Unknown')}\n- Sun Preference: {p.get('sun_preference', 'Unknown')}\n- Watering Interval: Every {p.get('watering_interval_days', 3)} days\n- Last Watered: {p.get('last_watered', 'Not recorded')}"
                            break
                
                # Regular chat (image upload feature removed)
                # Get current weather for context - use detected location
                user_city = st.session_state.user_location.get('city', DEFAULT_CITY)
                user_country = st.session_state.user_location.get('country', DEFAULT_COUNTRY)
                current_weather = weather_service.get_current_weather(user_city, user_country)
                weather_context = f"Current weather in {user_city}, {user_country}: {current_weather.get('temperature', 25)}°C, {current_weather.get('description', 'clear')}"
                
                full_context = f"{weather_context}. {plants_context}{selected_plant_context}" if plants_context else f"{weather_context}{selected_plant_context}"
                response = groq_service.chat_about_plant(user_question, full_context)
                
                st.write(response)
                
                # Save to chat history
                data_manager.add_chat_message(user_question, response, plants_context)
                st.session_state.chat_history = data_manager.get_chat_history(20)

# Footer (shown on all pages except Welcome which has its own footer)
if page != "🏠 Welcome":
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 20px; margin-top: 50px; background: rgba(27, 94, 32, 0.8); border-radius: 15px;">
        <p style="color: #ffffff; font-size: 1.1em; margin: 10px 0;">
            <strong>🌱 Smart Garden App</strong> | Powered by: <strong>Haseeb, Zahra Zahid, Maira, and Zahra Mumtaz</strong>
        </p>
        <p style="color: rgba(255, 255, 255, 0.8); font-size: 0.9em; margin-top: 10px;">
            Built with Streamlit, Google Gemini, and OpenWeatherMap
        </p>
    </div>
    """, unsafe_allow_html=True)

