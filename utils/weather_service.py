"""
Weather Service Module
Handles all weather-related API calls and data processing
Uses OpenWeatherMap API (free tier)
"""
import requests
import json
from datetime import datetime, timedelta
import config

class WeatherService:
    def __init__(self):
        # Access API key dynamically from config module (supports secrets.toml)
        self.api_key = config.OPENWEATHER_API_KEY
        self.base_url = config.OPENWEATHER_BASE_URL
        
    def get_current_weather(self, city=None, country_code="PK"):
        if city is None:
            city = config.DEFAULT_CITY
        """
        Get current weather conditions for a city
        Returns: dict with temperature, condition, humidity, cloud cover, etc.
        """
        if not self.api_key:
            return self._get_mock_weather()
            
        try:
            url = f"{self.base_url}/weather"
            params = {
                "q": f"{city},{country_code}",
                "appid": self.api_key,
                "units": "metric"
            }
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "temperature": round(data["main"]["temp"]),
                    "feels_like": round(data["main"]["feels_like"]),
                    "condition": data["weather"][0]["main"],
                    "description": data["weather"][0]["description"],
                    "humidity": data["main"]["humidity"],
                    "cloud_cover": data.get("clouds", {}).get("all", 0),
                    "wind_speed": data.get("wind", {}).get("speed", 0),
                    "icon": data["weather"][0]["icon"],
                    "city": data["name"],
                    "country": data["sys"]["country"],
                    "sunrise": datetime.fromtimestamp(data["sys"]["sunrise"]),
                    "sunset": datetime.fromtimestamp(data["sys"]["sunset"]),
                    "timestamp": datetime.now()
                }
            else:
                return self._get_mock_weather()
        except Exception as e:
            print(f"Weather API Error: {e}")
            return self._get_mock_weather()
    
    def get_forecast(self, city=None, country_code="PK", days=3):
        if city is None:
            city = config.DEFAULT_CITY
        """
        Get weather forecast for next N days
        Returns: list of forecast data
        """
        if not self.api_key:
            return self._get_mock_forecast()
            
        try:
            url = f"{self.base_url}/forecast"
            params = {
                "q": f"{city},{country_code}",
                "appid": self.api_key,
                "units": "metric"
            }
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                forecasts = []
                for item in data["list"][:days*8]:  # 8 forecasts per day (3-hour intervals)
                    forecasts.append({
                        "datetime": datetime.fromtimestamp(item["dt"]),
                        "temperature": round(item["main"]["temp"]),
                        "condition": item["weather"][0]["main"],
                        "description": item["weather"][0]["description"],
                        "precipitation": item.get("rain", {}).get("3h", 0),
                        "cloud_cover": item.get("clouds", {}).get("all", 0),
                        "humidity": item["main"]["humidity"]
                    })
                return forecasts
            else:
                return self._get_mock_forecast()
        except Exception as e:
            print(f"Forecast API Error: {e}")
            return self._get_mock_forecast()
    
    def check_rain_alert(self, city=None, country_code="PK", hours_ahead=24):
        if city is None:
            city = config.DEFAULT_CITY
        """
        Check if rain is expected in the next N hours
        Returns: dict with rain alert info
        """
        forecast = self.get_forecast(city, country_code, days=2)
        current_time = datetime.now()
        
        rain_alerts = []
        for item in forecast:
            time_diff = (item["datetime"] - current_time).total_seconds() / 3600
            if 0 <= time_diff <= hours_ahead:
                if item["precipitation"] > 0 or "rain" in item["description"].lower():
                    rain_alerts.append({
                        "time": item["datetime"],
                        "hours_from_now": round(time_diff, 1),
                        "intensity": "Heavy" if item["precipitation"] > 5 else "Light",
                        "description": item["description"]
                    })
        
        return {
            "has_rain": len(rain_alerts) > 0,
            "alerts": rain_alerts,
            "next_rain": rain_alerts[0] if rain_alerts else None
        }
    
    def check_storm_alert(self, city=None, country_code="PK", hours_ahead=24):
        if city is None:
            city = config.DEFAULT_CITY
        """
        Check for severe weather (thunderstorm, hail, etc.)
        Returns: dict with storm alert info
        """
        forecast = self.get_forecast(city, country_code, days=2)
        current_time = datetime.now()
        
        storm_keywords = ["thunderstorm", "storm", "hail", "extreme"]
        storm_alerts = []
        
        for item in forecast:
            time_diff = (item["datetime"] - current_time).total_seconds() / 3600
            if 0 <= time_diff <= hours_ahead:
                condition_lower = item["condition"].lower()
                desc_lower = item["description"].lower()
                
                if any(keyword in condition_lower or keyword in desc_lower for keyword in storm_keywords):
                    storm_alerts.append({
                        "time": item["datetime"],
                        "hours_from_now": round(time_diff, 1),
                        "condition": item["condition"],
                        "description": item["description"]
                    })
        
        return {
            "has_storm": len(storm_alerts) > 0,
            "alerts": storm_alerts,
            "next_storm": storm_alerts[0] if storm_alerts else None
        }
    
    def get_sun_exposure_estimate(self, placement, current_weather, user_sun_preference):
        """
        Estimate sun exposure based on weather data and user input
        Returns: dict with sun exposure analysis
        """
        cloud_cover = current_weather.get("cloud_cover", 0)
        current_hour = datetime.now().hour
        current_minute = datetime.now().minute
        sunrise = current_weather.get("sunrise")
        sunset = current_weather.get("sunset")
        temperature = current_weather.get("temperature", 25)
        
        # Determine if it's daytime
        is_daytime = True
        hours_since_sunrise = 0
        if sunrise and sunset:
            sunrise_hour = sunrise.hour
            sunrise_minute = sunrise.minute
            sunset_hour = sunset.hour
            sunset_minute = sunset.minute
            
            current_time_minutes = current_hour * 60 + current_minute
            sunrise_time_minutes = sunrise_hour * 60 + sunrise_minute
            sunset_time_minutes = sunset_hour * 60 + sunset_minute
            
            is_daytime = sunrise_time_minutes <= current_time_minutes <= sunset_time_minutes
            if is_daytime:
                hours_since_sunrise = (current_time_minutes - sunrise_time_minutes) / 60.0
        
        # Calculate sun intensity based on time of day and cloud cover
        sun_intensity = "Low"
        sun_hours = 0
        
        if not is_daytime:
            sun_intensity = "None"
            sun_hours = 0
        else:
            # Morning (0-4 hours after sunrise): Lower intensity
            # Midday (4-8 hours after sunrise): Peak intensity
            # Afternoon (8+ hours after sunrise): Medium-high intensity
            
            if hours_since_sunrise < 4:
                # Morning sun is gentler
                if cloud_cover < 20:
                    sun_intensity = "Medium"
                    sun_hours = 2 + (4 - hours_since_sunrise) * 0.5  # Estimate remaining sun hours
                elif cloud_cover < 50:
                    sun_intensity = "Low"
                    sun_hours = 1 + (4 - hours_since_sunrise) * 0.3
                else:
                    sun_intensity = "Low"
                    sun_hours = 0.5
            elif hours_since_sunrise < 8:
                # Peak sun hours (midday)
                if cloud_cover < 20:
                    sun_intensity = "High"
                    sun_hours = 4 + (8 - hours_since_sunrise) * 0.5
                elif cloud_cover < 50:
                    sun_intensity = "Medium"
                    sun_hours = 2 + (8 - hours_since_sunrise) * 0.3
                else:
                    sun_intensity = "Low"
                    sun_hours = 1
            else:
                # Afternoon
                if cloud_cover < 20:
                    sun_intensity = "Medium-High"
                    sun_hours = max(0, (sunset_time_minutes - current_time_minutes) / 60.0)
                elif cloud_cover < 50:
                    sun_intensity = "Medium"
                    sun_hours = max(0, (sunset_time_minutes - current_time_minutes) / 60.0) * 0.7
                else:
                    sun_intensity = "Low"
                    sun_hours = max(0, (sunset_time_minutes - current_time_minutes) / 60.0) * 0.4
        
        # Placement-based logic
        placement_impact = {
            "Open Roof": {"sun_multiplier": 1.0, "exposure": "Full"},
            "Balcony": {"sun_multiplier": 0.7, "exposure": "Partial"},
            "Indoor Window": {"sun_multiplier": 0.4, "exposure": "Indirect"}
        }
        
        placement_data = placement_impact.get(placement, {"sun_multiplier": 0.5, "exposure": "Unknown"})
        
        # Adjust sun hours based on placement
        adjusted_sun_hours = sun_hours * placement_data["sun_multiplier"]
        
        # Calculate actual exposure - consider temperature and time of day
        actual_exposure = "Moderate"
        risk_level = "None"
        
        if not is_daytime:
            actual_exposure = "No Sun (Night)"
            risk_level = "None"
        elif sun_intensity == "High" and placement_data["exposure"] == "Full":
            # Only show overheating risk if it's actually hot AND peak sun hours
            if temperature > 35 and hours_since_sunrise >= 4:
                actual_exposure = "Very High - Risk of Overheating"
                risk_level = "High"
            elif temperature > 30:
                actual_exposure = "High - Monitor Temperature"
                risk_level = "Medium"
            else:
                actual_exposure = "High - Good Conditions"
                risk_level = "Low"
        elif sun_intensity == "High" and placement_data["exposure"] == "Partial":
            actual_exposure = "High - Monitor closely"
            risk_level = "Low"
        elif sun_intensity in ["Medium-High", "Medium"]:
            actual_exposure = "Moderate - Good conditions"
            risk_level = "None"
        else:
            actual_exposure = "Low - May need more light"
            risk_level = "None"
        
        return {
            "sun_intensity": sun_intensity,
            "cloud_cover": cloud_cover,
            "placement": placement,
            "estimated_exposure": actual_exposure,
            "is_daytime": is_daytime,
            "sun_hours": round(adjusted_sun_hours, 1),
            "risk_level": risk_level,
            "recommendation": self._get_sun_recommendation(actual_exposure, temperature, is_daytime, hours_since_sunrise)
        }
    
    def _get_sun_recommendation(self, exposure, temperature, is_daytime, hours_since_sunrise):
        """Generate recommendation based on sun exposure, temperature, and time of day"""
        if not is_daytime:
            return "🌙 Night time - No sun exposure"
        
        if "Very High" in exposure and temperature > 35:
            return "⚠️ High heat and intense sun! Consider moving to shade or providing extra water."
        elif "Very High" in exposure:
            return "☀️ Very sunny conditions. Ensure adequate watering."
        elif "High" in exposure and "Monitor" in exposure:
            return "☀️ High sun exposure. Monitor temperature and water needs."
        elif "High" in exposure:
            return "✅ Good sun exposure. Monitor soil moisture."
        elif "Moderate" in exposure:
            return "✅ Moderate conditions. Plant should be comfortable."
        elif "Low" in exposure:
            return "🌥️ Limited sunlight. Consider moving to brighter location if plant needs more light."
        else:
            return "✅ Conditions are suitable for your plant."
    
    def _get_mock_weather(self):
        """Fallback mock weather data for testing"""
        return {
            "temperature": 32,
            "feels_like": 35,
            "condition": "Clear",
            "description": "clear sky",
            "humidity": 60,
            "cloud_cover": 10,
            "wind_speed": 5,
            "icon": "01d",
            "city": config.DEFAULT_CITY,
            "country": "PK",
            "sunrise": datetime.now().replace(hour=6, minute=0),
            "sunset": datetime.now().replace(hour=18, minute=0),
            "timestamp": datetime.now()
        }
    
    def _get_mock_forecast(self):
        """Fallback mock forecast data for testing"""
        forecasts = []
        for i in range(8):
            forecasts.append({
                "datetime": datetime.now() + timedelta(hours=i*3),
                "temperature": 30 + (i % 3),
                "condition": "Clear" if i < 4 else "Rain",
                "description": "clear sky" if i < 4 else "light rain",
                "precipitation": 0 if i < 4 else 2.5,
                "cloud_cover": 10 if i < 4 else 80,
                "humidity": 60
            })
        return forecasts

