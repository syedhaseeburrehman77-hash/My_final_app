"""
Configuration file for Smart Garden App
Loads environment variables from Streamlit secrets (Cloud) or .env file (Local)
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file (for local development)
load_dotenv()

def get_secret(key_name, default=""):
    """
    Get secret from Streamlit secrets (Cloud) or environment variable (Local)
    Priority: st.secrets > .env file > default
    
    This function is called at runtime when Streamlit is already initialized
    """
    # Try Streamlit secrets first (for Streamlit Cloud and local secrets.toml)
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and st.secrets:
            # Try nested format: st.secrets["api"]["key_name"]
            try:
                if "api" in st.secrets:
                    value = st.secrets["api"].get(key_name.lower(), "")
                    if value:
                        return value
            except:
                pass
            
            # Try direct format: st.secrets["KEY_NAME"]
            try:
                value = st.secrets.get(key_name, "")
                if value:
                    return value
            except:
                pass
            
            # Try lowercase direct: st.secrets["key_name"]
            try:
                value = st.secrets.get(key_name.lower(), "")
                if value:
                    return value
            except:
                pass
    except:
        pass
    
    # Fallback to environment variable (for local .env file)
    return os.getenv(key_name, default)

# API Keys
# These will be loaded at runtime when Streamlit is initialized
# Priority: Streamlit Cloud secrets > .streamlit/secrets.toml > .env file > empty string
# IMPORTANT: Never commit API keys to GitHub!

# We'll use a function that gets called after Streamlit initializes
# For now, set to empty - they'll be loaded dynamically
OPENWEATHER_API_KEY = ""
GEMINI_API_KEY = ""
GROQ_API_KEY = ""
PERENUAL_API_KEY = ""
HUGGINGFACE_API_KEY = ""

# Default Settings
DEFAULT_LOCATION = os.getenv("DEFAULT_LOCATION", "Sialkot,PK")
DEFAULT_CITY = "Sialkot"
DEFAULT_COUNTRY = "PK"

def load_api_keys():
    """
    Load API keys from secrets or environment variables
    Call this function after Streamlit is initialized (in app.py)
    """
    global OPENWEATHER_API_KEY, GEMINI_API_KEY, GROQ_API_KEY, PERENUAL_API_KEY, HUGGINGFACE_API_KEY, DEFAULT_LOCATION
    
    # Try multiple key name formats
    OPENWEATHER_API_KEY = (
        get_secret("OPENWEATHER_API_KEY") or 
        get_secret("openweather_key") or 
        get_secret("openweather_api_key") or
        os.getenv("OPENWEATHER_API_KEY", "")
    )
    
    GEMINI_API_KEY = (
        get_secret("GEMINI_API_KEY") or 
        get_secret("gemini_key") or 
        get_secret("gemini_api_key") or
        os.getenv("GEMINI_API_KEY", "")
    )
    
    GROQ_API_KEY = (
        get_secret("GROQ_API_KEY") or 
        get_secret("groq_key") or 
        get_secret("groq_api_key") or
        os.getenv("GROQ_API_KEY", "")
    )
    
    PERENUAL_API_KEY = (
        get_secret("PERENUAL_API_KEY") or 
        get_secret("perenual_key") or 
        get_secret("perenual_api_key") or
        os.getenv("PERENUAL_API_KEY", "")
    )
    
    HUGGINGFACE_API_KEY = (
        get_secret("HUGGINGFACE_API_KEY") or 
        get_secret("huggingface_key") or 
        get_secret("huggingface_api_key") or
        os.getenv("HUGGINGFACE_API_KEY", "")
    )
    
    DEFAULT_LOCATION = (
        get_secret("DEFAULT_LOCATION") or 
        get_secret("default_location") or
        os.getenv("DEFAULT_LOCATION", "Sialkot,PK")
    )

# API Endpoints
OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"
PERENUAL_BASE_URL = "https://perenual.com/api"

# Data Storage
PLANTS_DB_FILE = "plants_database.json"
CHAT_HISTORY_FILE = "chat_history.json"

# App Settings
WATERING_CHECK_TIME = "08:00"  # Daily check time
MAX_PLANTS = 50  # Maximum number of plants user can add

