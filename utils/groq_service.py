"""
Groq AI Service Module
Handles all Groq API interactions for fast chat responses
Uses Llama 3 models for ultra-fast responses
"""
from groq import Groq
import config

class GroqService:
    def __init__(self):
        # Access API key dynamically from config module (supports secrets.toml)
        self.api_key = config.GROQ_API_KEY
        if self.api_key:
            try:
                self.client = Groq(api_key=self.api_key)
                self.model = "llama-3.3-70b-versatile"  # Latest Groq model - fast and smart
            except Exception as e:
                print(f"Groq initialization error: {e}")
                self.client = None
                self.model = None
        else:
            self.client = None
            self.model = None
    
    def chat_about_plant(self, user_message, plant_context=""):
        """
        Chat with AI botanist using Groq (ultra-fast)
        Returns: AI response
        """
        if not self.client:
            return "🌱 I'm here to help with your plant care questions! However, the Groq API key is not configured. Please set your GROQ_API_KEY in Streamlit Cloud secrets (Settings → Secrets) to enable AI chat responses."
        
        try:
            system_prompt = f"""You are an expert botanist and plant care advisor. You help users with their gardening questions in a friendly, knowledgeable way.

Plant context: {plant_context if plant_context else "General plant care"}

Provide helpful, accurate advice. If you're unsure, say so. Always prioritize plant health and safety. Keep responses concise but informative."""
            
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_message,
                    }
                ],
                model=self.model,
                temperature=0.7,
                max_tokens=500
            )
            
            response = chat_completion.choices[0].message.content.strip()
            if not response:
                return "I received an empty response. Please try asking your question again."
            return response
        except Exception as e:
            error_msg = str(e)
            print(f"Groq chat error: {error_msg}")
            
            # User-friendly error messages
            if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                return "🔑 **API Key Error**: Please check your Groq API key in Streamlit Cloud secrets (Settings → Secrets). Make sure GROQ_API_KEY is set correctly."
            elif "rate limit" in error_msg.lower() or "quota" in error_msg.lower():
                return "⏱️ **Rate Limit**: Too many requests. Please wait a moment and try again."
            elif "model" in error_msg.lower():
                return "🤖 **Model Error**: The AI model is temporarily unavailable. Please try again in a moment."
            else:
                return f"⚠️ **Error**: {error_msg}\n\nPlease try again or check your API configuration in Streamlit Cloud secrets."
    
    def generate_alert_message(self, alert_type, plant_name, weather_data):
        """
        Generate user-friendly alert messages using Groq
        Returns: polished alert message
        """
        if not self.client:
            return self._get_default_alert(alert_type, plant_name, weather_data)
        
        try:
            if alert_type == "rain":
                prompt = f"""Generate a friendly, helpful alert message for a garden app user.
                
Situation: Rain is expected soon in {weather_data.get('city', 'your area')}.
Plant: {plant_name}
Weather: {weather_data.get('description', 'rainy conditions')}

Write a short, warm message (2-3 sentences) telling the user to move their outdoor plant to shelter.
Be conversational and caring, like a helpful friend."""
            
            elif alert_type == "storm":
                prompt = f"""Generate an urgent but calm alert message for a garden app user.

Situation: Severe weather (thunderstorm/hail) is expected in {weather_data.get('city', 'your area')}.
Plant: {plant_name}
Weather: {weather_data.get('description', 'severe conditions')}

Write a clear, urgent message (2-3 sentences) telling the user to immediately move their outdoor plant indoors.
Be direct but not alarming."""
            
            elif alert_type == "heat":
                prompt = f"""Generate a helpful reminder for a garden app user.

Situation: Very hot weather ({weather_data.get('temperature', 35)}°C) and intense sun.
Plant: {plant_name}
Location: Outdoor/Open area

Write a friendly reminder (2-3 sentences) to check if the plant needs extra water or shade.
Be helpful and caring."""
            
            else:
                return self._get_default_alert(alert_type, plant_name, weather_data)
            
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful garden assistant. Generate friendly, concise alert messages."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                temperature=0.7,
                max_tokens=200
            )
            
            return chat_completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"Alert generation error: {e}")
            return self._get_default_alert(alert_type, plant_name, weather_data)
    
    def _get_default_alert(self, alert_type, plant_name, weather_data):
        """Default alert messages when Groq is not available"""
        if alert_type == "rain":
            return f"🌧️ Rain Alert: Rain is expected in {weather_data.get('city', 'your area')} soon. Your {plant_name} is outdoors - consider moving it under shelter!"
        elif alert_type == "storm":
            return f"⚠️ Storm Alert: Severe weather is approaching {weather_data.get('city', 'your area')}. Please move your {plant_name} indoors immediately!"
        elif alert_type == "heat":
            return f"☀️ Heat Alert: It's very hot ({weather_data.get('temperature', 35)}°C) and sunny. Your {plant_name} may need extra water or shade. Check the soil moisture!"
        else:
            return f"Alert for {plant_name}: Please check your plant."

