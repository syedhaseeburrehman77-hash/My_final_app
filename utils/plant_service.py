"""
Plant Service Module
Handles plant data retrieval from Perenual API and plant care logic
"""
import requests
import json
import config
from datetime import datetime, timedelta

class PlantService:
    def __init__(self):
        # Access API key dynamically from config module (supports secrets.toml)
        self.api_key = config.PERENUAL_API_KEY
        self.base_url = config.PERENUAL_BASE_URL
        
    def search_plant(self, query):
        """
        Search for plant information by name
        Returns: list of matching plants
        """
        if not self.api_key:
            return self._get_mock_plant_data(query)
            
        try:
            url = f"{self.base_url}/species-list"
            params = {
                "key": self.api_key,
                "q": query,
                "page": 1
            }
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("data", [])
            else:
                return self._get_mock_plant_data(query)
        except Exception as e:
            print(f"Plant API Error: {e}")
            return self._get_mock_plant_data(query)
    
    def get_plant_details(self, plant_id):
        """
        Get detailed information about a specific plant
        Returns: dict with plant care details
        """
        if not self.api_key:
            return self._get_mock_plant_details()
            
        try:
            url = f"{self.base_url}/species/details/{plant_id}"
            params = {"key": self.api_key}
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                return self._get_mock_plant_details()
        except Exception as e:
            print(f"Plant Details API Error: {e}")
            return self._get_mock_plant_details()
    
    def calculate_watering_schedule(self, plant_name, base_interval_days, last_watered, weather_data, forecast_data):
        """
        Smart water reminder calculation based on weather
        Returns: dict with watering status and recommendations
        """
        if not last_watered:
            return {
                "needs_water": True,
                "days_since_watered": 0,
                "message": "New plant! Water it now to get started.",
                "urgency": "high"
            }
        
        # Calculate days since last watering
        if isinstance(last_watered, str):
            last_watered = datetime.fromisoformat(last_watered)
        days_since = (datetime.now() - last_watered).days
        
        # Check if it rained recently (last 24 hours)
        recent_rain = False
        if forecast_data:
            for item in forecast_data[:8]:  # Check last 24 hours (8 x 3-hour intervals)
                if item.get("precipitation", 0) > 0:
                    recent_rain = True
                    break
        
        # Adjust interval based on temperature
        current_temp = weather_data.get("temperature", 25)
        adjusted_interval = base_interval_days
        
        if current_temp > 35:
            adjusted_interval = max(1, base_interval_days - 1)  # Water more frequently in heat
        elif current_temp < 15:
            adjusted_interval = base_interval_days + 1  # Water less frequently in cold
        
        # Check if rain is expected soon
        rain_expected = False
        if forecast_data:
            for item in forecast_data[:4]:  # Next 12 hours
                if item.get("precipitation", 0) > 0:
                    rain_expected = True
                    break
        
        # Determine watering status
        needs_water = False
        urgency = "low"
        message = ""
        
        if recent_rain:
            needs_water = False
            message = "✅ Recent rain detected. No need to water yet."
            urgency = "low"
        elif rain_expected:
            needs_water = False
            message = "🌧️ Rain expected soon. Hold off on watering."
            urgency = "low"
        elif days_since >= adjusted_interval:
            needs_water = True
            if days_since >= adjusted_interval + 1:
                urgency = "high"
                message = f"💧 Needs water! It's been {days_since} days (recommended: every {adjusted_interval} days)."
            else:
                urgency = "medium"
                message = f"💧 Time to water! It's been {days_since} days."
        else:
            days_until = adjusted_interval - days_since
            needs_water = False
            message = f"✅ Happy! Next watering in {days_until} day(s)."
            urgency = "low"
        
        return {
            "needs_water": needs_water,
            "days_since_watered": days_since,
            "adjusted_interval": adjusted_interval,
            "message": message,
            "urgency": urgency,
            "recent_rain": recent_rain,
            "rain_expected": rain_expected
        }
    
    def get_plant_care_tips(self, plant_name, plant_type="general"):
        """
        Get general care tips for a plant
        Returns: dict with care information
        """
        care_tips = {
            "Rose": {
                "watering": "Water deeply 2-3 times per week. Keep soil moist but not waterlogged.",
                "sunlight": "Needs 6+ hours of direct sunlight daily.",
                "temperature": "Prefers 15-25°C. Protect from extreme heat.",
                "fertilizer": "Fertilize monthly during growing season."
            },
            "Tomato": {
                "watering": "Water daily in hot weather. Keep soil consistently moist.",
                "sunlight": "Needs full sun (8+ hours daily).",
                "temperature": "Thrives in 18-27°C. Protect from frost.",
                "fertilizer": "Fertilize every 2 weeks with balanced fertilizer."
            },
            "Money Plant": {
                "watering": "Water when top inch of soil is dry (every 5-7 days).",
                "sunlight": "Bright indirect light. Can tolerate low light.",
                "temperature": "Prefers 18-24°C. Avoid cold drafts.",
                "fertilizer": "Fertilize monthly during spring/summer."
            },
            "Fern": {
                "watering": "Keep soil consistently moist. Water every 2-3 days.",
                "sunlight": "Bright indirect light. Avoid direct sun.",
                "temperature": "Prefers 18-22°C. High humidity preferred.",
                "fertilizer": "Fertilize monthly with diluted fertilizer."
            }
        }
        
        # Try to find specific tips, otherwise return general
        if plant_name in care_tips:
            return care_tips[plant_name]
        else:
            return {
                "watering": "Water when top soil feels dry. Adjust based on weather.",
                "sunlight": "Most plants prefer bright indirect light.",
                "temperature": "Keep in comfortable room temperature (18-25°C).",
                "fertilizer": "Fertilize monthly during growing season."
            }
    
    def _get_mock_plant_data(self, query):
        """Fallback mock plant data for testing"""
        mock_plants = {
            "rose": [{"id": 1, "common_name": "Rose", "scientific_name": "Rosa"}],
            "tomato": [{"id": 2, "common_name": "Tomato", "scientific_name": "Solanum lycopersicum"}],
            "money": [{"id": 3, "common_name": "Money Plant", "scientific_name": "Epipremnum aureum"}]
        }
        
        query_lower = query.lower()
        for key, plants in mock_plants.items():
            if key in query_lower:
                return plants
        return [{"id": 999, "common_name": query, "scientific_name": "Unknown"}]
    
    def _get_mock_plant_details(self):
        """Fallback mock plant details for testing"""
        return {
            "watering": "Moderate",
            "sunlight": "Full sun to partial shade",
            "hardiness": {"min": 5, "max": 9},
            "care_level": "Easy"
        }

