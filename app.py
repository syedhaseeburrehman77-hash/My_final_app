import streamlit as st
import os
import json
import requests
from datetime import datetime, timedelta
from PIL import Image
import google.generativeai as genai
from groq import Groq

# ==========================================
# 1. CONFIGURATION & SECRETS
# ==========================================
st.set_page_config(
    page_title="Smart Garden App",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Function to get keys safely
def get_secret(key):
    if key in st.secrets:
        return st.secrets[key]
    if os.getenv(key):
        return os.getenv(key)
    return None

# Load Keys
OPENWEATHER_API_KEY = get_secret("OPENWEATHER_API_KEY")
GEMINI_API_KEY = get_secret("GEMINI_API_KEY")
GROQ_API_KEY = get_secret("GROQ_API_KEY")
DEFAULT_CITY = "Sialkot"
DEFAULT_COUNTRY = "PK"

# Custom CSS
st.markdown("""
<style>
    .stApp {background: linear-gradient(135deg, #1b5e20 0%, #2e7d32 25%, #4caf50 50%, #66bb6a 75%, #81c784 100%); background-attachment: fixed;}
    .main .block-container {background: rgba(255, 255, 255, 0.95); border-radius: 20px; padding: 2rem; margin-top: 1rem;}
    .plant-card {background: linear-gradient(135deg, #ffffff 0%, #f1f8e9 100%); padding: 20px; border-radius: 15px; border-left: 5px solid #4caf50; margin-bottom: 20px;}
    .weather-banner {background: linear-gradient(135deg, #66bb6a 0%, #81c784 100%); color: white; padding: 25px; border-radius: 15px;}
    h1, h2, h3 {color: #1b5e20 !important;}
    section[data-testid="stSidebar"] {background: linear-gradient(180deg, #1b5e20 0%, #2e7d32 100%);}
    section[data-testid="stSidebar"] * {color: white !important;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. BACKEND SERVICES (LOGIC CLASSES)
# ==========================================

class DataManager:
    """Handles saving/loading plants to a simple JSON file"""
    def __init__(self, db_file='plants_db.json'):
        self.db_file = db_file
    
    def get_all_plants(self):
        if not os.path.exists(self.db_file): return []
        try:
            with open(self.db_file, 'r') as f: return json.load(f)
        except: return []

    def add_plant(self, plant_data):
        plants = self.get_all_plants()
        plant_data['id'] = int(datetime.now().timestamp()) # Unique ID
        plants.append(plant_data)
        with open(self.db_file, 'w') as f: json.dump(plants, f)
        return plant_data

    def delete_plant(self, plant_id):
        plants = self.get_all_plants()
        plants = [p for p in plants if p.get('id') != plant_id]
        with open(self.db_file, 'w') as f: json.dump(plants, f)

    def mark_watered(self, plant_id):
        plants = self.get_all_plants()
        for p in plants:
            if p.get('id') == plant_id:
                p['last_watered'] = datetime.now().isoformat()
        with open(self.db_file, 'w') as f: json.dump(plants, f)

    def get_user_profile(self):
        # Mock profile for hackathon (or save to json if needed)
        if os.path.exists("user_profile.json"):
            with open("user_profile.json", "r") as f: return json.load(f)
        return {"name": "", "email": "", "location": DEFAULT_CITY}

    def save_user_profile(self, data):
        with open("user_profile.json", "w") as f: json.dump(data, f)
    
    def get_chat_history(self, limit=10):
        if not os.path.exists("chat_history.json"): return []
        with open("chat_history.json", "r") as f: 
            hist = json.load(f)
            return hist[-limit:]
            
    def add_chat_message(self, user_msg, bot_msg, context=""):
        hist = self.get_chat_history(100)
        hist.append({"user_message": user_msg, "bot_response": bot_msg, "context": context})
        with open("chat_history.json", "w") as f: json.dump(hist, f)


class WeatherService:
    """Handles OpenWeatherMap API"""
    def get_current_weather(self, city):
        if not OPENWEATHER_API_KEY: return {"temperature": 25, "description": "No Key"}
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
            data = requests.get(url).json()
            if data.get("cod") != 200: return None
            return {
                "temperature": data['main']['temp'],
                "description": data['weather'][0]['description'],
                "humidity": data['main']['humidity'],
                "icon": data['weather'][0]['icon']
            }
        except: return None

    def get_forecast(self, city, days=2):
        # Simple forecast implementation
        return []


class GroqService:
    """Handles Chatbot (Fast)"""
    def chat_about_plant(self, query, context):
        if not GROQ_API_KEY: return "⚠️ Groq API Key missing."
        try:
            client = Groq(api_key=GROQ_API_KEY)
            completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": f"You are an expert botanist. Context: {context}. Keep answers short and helpful."},
                    {"role": "user", "content": query}
                ],
                model="llama-3.3-70b-versatile",
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"AI Error: {e}"


class HuggingFaceService:
    """Handles Image Identification"""
    def identify_plant(self, image):
        # Using Google Gemini as fallback if HF is complex to setup in one file
        # or implement simple HF API call here
        if not GEMINI_API_KEY: return {"plant_name": "API Key Missing"}
        
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(["Identify this plant name only.", image])
            return {"plant_name": response.text.strip()}
        except Exception as e:
            return {"plant_name": "Unknown Plant"}


class PlantService:
    """Handles Watering Logic"""
    def calculate_watering_schedule(self, name, interval, last_watered, weather, forecast):
        needs_water = False
        if not last_watered:
            needs_water = True
        else:
            try:
                last_date = datetime.fromisoformat(str(last_watered))
                days_diff = (datetime.now() - last_date).days
                if days_diff >= int(interval):
                    needs_water = True
            except:
                needs_water = True
        
        # Weather Logic Override
        if weather and 'rain' in weather.get('description', '').lower():
            needs_water = False # Don't water if raining
        
        return {"needs_water": needs_water}


# Initialize all services
data_manager = DataManager()
weather_service = WeatherService()
groq_service = GroqService()
huggingface_service = HuggingFaceService()
plant_service = PlantService()

# ==========================================
# 3. MAIN UI LOGIC
# ==========================================

# Initialize Session State
if 'plants' not in st.session_state: st.session_state.plants = data_manager.get_all_plants()
if 'user_location' not in st.session_state: st.session_state.user_location = {"city": DEFAULT_CITY, "country": DEFAULT_COUNTRY}
if 'chat_history' not in st.session_state: st.session_state.chat_history = data_manager.get_chat_history()

# --- SIDEBAR ---
with st.sidebar:
    st.header("🌱 Smart Garden")
    page = st.radio("Navigate", ["🏠 Welcome", "👤 User Profile", "📍 Location", "📊 Dashboard", "🌱 Add Plant", "🤖 AI Botanist"])

# --- PAGE: WELCOME ---
if page == "🏠 Welcome":
    st.title("🌱 Smart Garden App")
    st.markdown("### Your AI-Powered Plant Care Companion")
    st.info("Features: 🤖 AI Chatbot | 🌤️ Weather Alerts | 📊 Watering Tracker")
    st.write("Go to **Add Plant** to start!")

# --- PAGE: PROFILE ---
elif page == "👤 User Profile":
    st.title("👤 User Profile")
    prof = data_manager.get_user_profile()
    with st.form("prof"):
        name = st.text_input("Name", value=prof.get('name', ''))
        loc = st.text_input("City", value=prof.get('location', DEFAULT_CITY))
        if st.form_submit_button("Save"):
            data_manager.save_user_profile({"name": name, "location": loc})
            st.success("Saved!")
            st.session_state.user_location = {"city": loc, "country": "PK"}

# --- PAGE: LOCATION ---
elif page == "📍 Location":
    st.title("📍 Location & Nurseries")
    loc = st.session_state.user_location
    st.write(f"Current Location: **{loc.get('city')}**")
    
    st.markdown("### Nearby Nurseries (Demo)")
    st.markdown(f"""
    - **Green Valley Nursery**: Main Road, {loc.get('city')} (2km away)
    - **Flora Center**: City Park, {loc.get('city')} (5km away)
    """)

# --- PAGE: DASHBOARD ---
elif page == "📊 Dashboard":
    st.title("🌿 Dashboard")
    city = st.session_state.user_location.get('city', DEFAULT_CITY)
    weather = weather_service.get_current_weather(city)
    
    if weather:
        st.markdown(f"""
        <div class="weather-banner">
            <h2>🌤️ {city}: {weather.get('temperature')}°C</h2>
            <p>{weather.get('description').title()} | Humidity: {weather.get('humidity')}%</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("### Your Plants")
    if not st.session_state.plants:
        st.warning("No plants yet.")
    else:
        cols = st.columns(2)
        for i, p in enumerate(st.session_state.plants):
            with cols[i%2]:
                status = plant_service.calculate_watering_schedule(p['name'], p['watering_interval_days'], p['last_watered'], weather, None)
                color = "#f44336" if status['needs_water'] else "#4caf50"
                text = "Needs Water" if status['needs_water'] else "Happy"
                
                st.markdown(f"""
                <div class="plant-card">
                    <div style="display:flex; justify-content:space-between;">
                        <h3>{p['name']}</h3>
                        <span style="background:{color}; color:white; padding:5px 10px; border-radius:10px;">{text}</span>
                    </div>
                    <p>📍 {p['placement']} | ☀️ {p['sun_preference']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("💧 Water", key=f"w{i}"):
                    data_manager.mark_watered(p['id'])
                    st.session_state.plants = data_manager.get_all_plants()
                    st.rerun()
                if st.button("🗑️ Delete", key=f"d{i}"):
                    data_manager.delete_plant(p['id'])
                    st.session_state.plants = data_manager.get_all_plants()
                    st.rerun()

# --- PAGE: ADD PLANT ---
elif page == "🌱 Add Plant":
    st.title("🌱 Add New Plant")
    c1, c2 = st.columns([1, 2])
    
    uploaded = st.file_uploader("Image")
    ai_name = ""
    
    if uploaded:
        st.image(uploaded, width=200)
        if st.button("🔍 Identify AI"):
            with st.spinner("Analyzing..."):
                res = huggingface_service.identify_plant(Image.open(uploaded))
                ai_name = res.get('plant_name')
                st.success(f"Identified: {ai_name}")

    with st.form("add"):
        name = st.text_input("Name", value=ai_name)
        loc = st.selectbox("Location", ["Outdoor", "Indoor", "Balcony"])
        sun = st.selectbox("Sun", ["Full Sun", "Shade"])
        days = st.slider("Water Days", 1, 14, 3)
        if st.form_submit_button("Save Plant"):
            data_manager.add_plant({
                "name": name, "placement": loc, "sun_preference": sun, 
                "watering_interval_days": days, "last_watered": None
            })
            st.success("Added!")

# --- PAGE: AI BOTANIST ---
elif page == "🤖 AI Botanist":
    st.title("🤖 AI Botanist")
    
    for c in st.session_state.chat_history:
        with st.chat_message("user"): st.write(c['user_message'])
        with st.chat_message("assistant"): st.write(c['bot_response'])
        
    st.markdown("### 🎤 Voice")
    audio = st.audio_input("Record")
    
    user_in = st.chat_input("Ask about plants...")
    final_q = None
    
    if audio:
        try:
            import speech_recognition as sr
            r = sr.Recognizer()
            with sr.AudioFile(audio) as source:
                data = r.record(source)
                final_q = r.recognize_google(data)
        except: st.error("Voice Error")

    if user_in: final_q = user_in
    
    if final_q:
        with st.chat_message("user"): st.write(final_q)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                city = st.session_state.user_location.get('city', DEFAULT_CITY)
                weather = weather_service.get_current_weather(city)
                ctx = f"Location: {city}. Weather: {weather}."
                ans = groq_service.chat_about_plant(final_q, ctx)
                st.write(ans)
                data_manager.add_chat_message(final_q, ans, ctx)
