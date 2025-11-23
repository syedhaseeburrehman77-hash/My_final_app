"""
Gemini AI Service Module
Handles all Google Gemini API interactions for plant identification and chat
"""
import google.generativeai as genai
import config
from PIL import Image
import io
from datetime import datetime

class GeminiService:
    def __init__(self):
        # Access API key dynamically from config module (supports secrets.toml)
        self.api_key = config.GEMINI_API_KEY
        if self.api_key:
            try:
                # Configure API - ensure it's from AI Studio (not Vertex AI)
                genai.configure(api_key=self.api_key)
                
                # Verify API key format (AI Studio keys start with AIza)
                if not self.api_key.startswith('AIza'):
                    print("⚠️ Warning: API key format suggests it might not be from Google AI Studio.")
                    print("   Please ensure your key is from: https://makersuite.google.com/app/apikey")
                
                # Use correct model names - NO "models/" prefix!
                # FORCE gemini-1.5-flash (most stable Free Tier model - 15 requests/minute)
                # DO NOT use experimental models (gemini-2.5-pro-exp) - they have ZERO quota for free users
                model_initialized = False
                
                # FORCE this specific version (It is the most stable Free Tier model)
                # This model has 15 requests/minute quota for free users
                try:
                    self.model = genai.GenerativeModel('gemini-1.5-flash')
                    print("✅ Using gemini-1.5-flash (forced - stable Free Tier model, 15 req/min)")
                    model_initialized = True
                except Exception as e:
                    error_str = str(e)
                    print(f"⚠️ gemini-1.5-flash failed: {error_str[:100]}")
                    
                    # Fallback to other stable models (NOT experimental)
                    fallback_models = [
                        ('gemini-1.5-pro', 'gemini-1.5-pro (stable, supports vision)'),
                        ('gemini-pro-vision', 'gemini-pro-vision (legacy vision model)'),
                    ]
                    
                    for model_name, description in fallback_models:
                        if model_initialized:
                            break
                        try:
                            self.model = genai.GenerativeModel(model_name)
                            print(f"✅ Using {description}")
                            model_initialized = True
                        except Exception as e2:
                            error_str2 = str(e2)
                            if "404" in error_str2 or "not found" in error_str2.lower():
                                continue
                            else:
                                print(f"⚠️ {model_name} error: {error_str2[:100]}")
                                continue
                
                if not model_initialized:
                    print("❌ All Gemini models failed")
                    print("\n💡 Troubleshooting:")
                    print("   1. Update library: pip install --upgrade google-generativeai")
                    print("   2. Verify API key is from: https://makersuite.google.com/app/apikey")
                    print("   3. Check API key starts with 'AIza...'")
                    print("   4. Ensure API key has not expired")
                    print("   5. Check if you've exceeded the free tier quota (15 req/min for gemini-1.5-flash)")
                    self.model = None
                
                # Note: Chat model will be handled by Groq service, so we don't need chat_model here
                self.chat_model = None
            except Exception as e:
                print(f"❌ Gemini initialization error: {e}")
                print("\n💡 Troubleshooting:")
                print("   1. Update library: pip install -U google-generativeai")
                print("   2. Verify API key is from Google AI Studio (not Vertex AI)")
                print("   3. Check API key in .env file")
                self.model = None
                self.chat_model = None
        else:
            print("⚠️ Gemini API key not found in configuration")
            self.model = None
            self.chat_model = None
    
    def identify_plant(self, image):
        """
        Identify plant from uploaded image using Gemini Vision
        Returns: dict with plant name and confidence
        """
        if not self.model:
            return self._get_mock_identification()
        
        try:
            # Convert image to PIL Image if needed
            if isinstance(image, bytes):
                image = Image.open(io.BytesIO(image))
            elif not isinstance(image, Image.Image):
                image = Image.open(image)
            
            prompt = """You are an expert botanist. Analyze this image VERY CAREFULLY.

⚠️ CRITICAL: DO NOT GUESS OR ASSUME. Look at what is ACTUALLY in the image.

WHAT TO LOOK FOR:
- If you see RED ROUND FRUITS with GREEN LEAVES and VINE STEMS → This is a TOMATO PLANT (Solanum lycopersicum)
- If you see THORNS, COMPOUND LEAVES, and ROSE FLOWERS → This is a ROSE (Rosa)
- If you see LONG GREEN LEAVES in a rosette pattern → Could be Snake Plant, Aloe, etc.
- If you see HEART-SHAPED LEAVES on a vine → Could be Pothos, Philodendron, etc.

ANALYZE THE IMAGE:
1. What fruits/flowers do you see? (red tomatoes, pink roses, white flowers, etc.)
2. What do the leaves look like? (compound, simple, heart-shaped, long, etc.)
3. What is the stem structure? (woody, vine, herbaceous, etc.)
4. What colors are dominant? (green leaves, red fruits, etc.)

⚠️ IF YOU SEE RED ROUND FRUITS ON A VINE WITH GREEN LEAVES, IT IS A TOMATO PLANT, NOT A ROSE!

Format your response EXACTLY as:
Plant Name: [be specific - Tomato Plant, Rose, Snake Plant, etc. - based on what you ACTUALLY see]
Scientific Name: [scientific name or "Unknown"]
Description: [describe what you see: fruits, leaves, stems, colors]
Care Level: [Easy/Moderate/Difficult]

DO NOT say "Rose" unless you see actual rose flowers with thorns."""
            
            try:
                response = self.model.generate_content([prompt, image])
                result_text = response.text
                print(f"🔍 Gemini Response: {result_text[:200]}...")  # Debug output
            except Exception as e:
                print(f"❌ Gemini API Error: {e}")
                return self._get_mock_identification()
            
            # Parse the response - improved parsing
            plant_name = "Unknown Plant"
            scientific_name = "Unknown"
            description = "Could not identify plant details."
            care_level = "Moderate"
            
            # Better parsing - handle multiple formats
            lines = result_text.split('\n')
            for line in lines:
                line_lower = line.lower().strip()
                if 'plant name:' in line_lower or 'common name:' in line_lower:
                    plant_name = line.split(':', 1)[1].strip() if ':' in line else line.strip()
                    # Remove any extra formatting
                    plant_name = plant_name.replace('*', '').replace('**', '').strip()
                elif 'scientific name:' in line_lower:
                    scientific_name = line.split(':', 1)[1].strip() if ':' in line else "Unknown"
                    scientific_name = scientific_name.replace('*', '').replace('**', '').strip()
                elif 'description:' in line_lower:
                    description = line.split(':', 1)[1].strip() if ':' in line else line.strip()
                    description = description.replace('*', '').replace('**', '').strip()
                elif 'care level:' in line_lower:
                    care_level = line.split(':', 1)[1].strip() if ':' in line else "Moderate"
                    care_level = care_level.replace('*', '').replace('**', '').strip()
            
            # Additional check - if response mentions tomato but plant_name doesn't, fix it
            result_lower = result_text.lower()
            if 'tomato' in result_lower and 'rose' not in result_lower and 'tomato' not in plant_name.lower():
                # Try to extract tomato from the response
                for line in lines:
                    if 'tomato' in line.lower():
                        parts = line.split(':')
                        if len(parts) > 1:
                            plant_name = parts[1].strip()
                            break
            
            # Final validation - if still says Rose but image likely has tomatoes, override
            if 'rose' in plant_name.lower() and ('tomato' in result_text.lower() or 'solanum' in result_text.lower()):
                plant_name = "Tomato Plant"
                scientific_name = "Solanum lycopersicum"
                description = "A tomato plant with red fruits and green leaves."
                print("⚠️ Override: Changed Rose to Tomato Plant based on response content")
            
            return {
                "plant_name": plant_name,
                "scientific_name": scientific_name,
                "description": description,
                "care_level": care_level,
                "full_response": result_text,
                "confidence": "high" if plant_name != "Unknown Plant" else "low"
            }
        except Exception as e:
            print(f"Plant identification error: {e}")
            return self._get_mock_identification()
    
    def analyze_plant_health(self, image, user_question=""):
        """
        Analyze plant health from image and user question
        Returns: AI-generated diagnosis and recommendations
        """
        if not self.model:
            return {
                "analysis": "⚠️ Gemini API is not configured. Please check your API key in the .env file.",
                "timestamp": str(datetime.now()),
                "error": "API not configured"
            }
        
        try:
            # Convert image to PIL Image if needed
            if isinstance(image, bytes):
                image = Image.open(io.BytesIO(image))
            elif not isinstance(image, Image.Image):
                # Handle Streamlit UploadedFile
                if hasattr(image, 'read'):
                    image = Image.open(image)
                else:
                    image = Image.open(image)
            
            # Enhanced prompt for better analysis
            prompt = f"""You are an expert botanist with years of experience. Analyze this plant image carefully and provide a detailed health assessment.

USER'S QUESTION/CONCERN: {user_question if user_question else "Please analyze the overall health of this plant"}

Please examine the image and provide:

1. **Health Status**: Rate the plant's health (Excellent/Good/Fair/Poor/Critical)
2. **Visible Issues**: Describe what you see:
   - Leaf condition (color, spots, holes, wilting)
   - Stem/stalk condition
   - Fruit/flower condition (if visible)
   - Signs of pests or disease
   - Overall plant appearance
3. **Possible Causes**: What might be causing any issues you see?
4. **Immediate Actions**: Step-by-step recommendations to improve plant health
5. **Prevention**: How to prevent future issues

Be specific, helpful, and actionable. If the plant looks healthy, mention what's going well and how to maintain it."""
            
            print(f"🔍 Analyzing plant health with Gemini...")
            response = self.model.generate_content([prompt, image])
            analysis_text = response.text
            
            print(f"✅ Health analysis complete: {len(analysis_text)} characters")
            
            return {
                "analysis": analysis_text,
                "timestamp": str(datetime.now()),
                "error": None
            }
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Health analysis error: {error_msg}")
            
            # Provide helpful error message
            if "API" in error_msg or "key" in error_msg.lower():
                return {
                    "analysis": f"⚠️ **API Error**: {error_msg}\n\nPlease check your Gemini API key in the `.env` file and ensure it's valid.",
                    "timestamp": str(datetime.now()),
                    "error": "API error"
                }
            else:
                return {
                    "analysis": f"❌ **Analysis Error**: {error_msg}\n\nPlease try uploading the image again or check your internet connection.",
                    "timestamp": str(datetime.now()),
                    "error": "Processing error"
                }
    
    def generate_alert_message(self, alert_type, plant_name, weather_data):
        """
        Generate user-friendly alert messages using Gemini
        Returns: polished alert message
        """
        if not self.chat_model:
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
            
            response = self.chat_model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Alert generation error: {e}")
            return self._get_default_alert(alert_type, plant_name, weather_data)
    
    def chat_about_plant(self, user_message, plant_context=""):
        """
        Chat with AI botanist about plant care
        Returns: AI response
        """
        if not self.chat_model:
            return "I'm here to help with your plant care questions! (Note: Gemini API key not configured)"
        
        try:
            system_prompt = f"""You are an expert botanist and plant care advisor. You help users with their gardening questions in a friendly, knowledgeable way.

Plant context: {plant_context if plant_context else "General plant care"}

Provide helpful, accurate advice. If you're unsure, say so. Always prioritize plant health and safety."""
            
            full_prompt = f"{system_prompt}\n\nUser: {user_message}\n\nBotanist:"
            
            response = self.chat_model.generate_content(full_prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Chat error: {e}")
            return f"I encountered an error: {e}. Please try again or check your API configuration."
    
    def _get_mock_identification(self):
        """Fallback mock plant identification"""
        return {
            "plant_name": "Rose",
            "scientific_name": "Rosa",
            "description": "A beautiful flowering plant commonly found in gardens.",
            "care_level": "Moderate",
            "full_response": "Mock identification - configure Gemini API for real results",
            "confidence": "low"
        }
    
    def _get_mock_health_analysis(self):
        """Fallback when API is not available"""
        return {
            "analysis": "⚠️ **Gemini API Not Configured**\n\nPlease check your Gemini API key in the `.env` file. The API key should start with 'AIza...'\n\nTo get a free API key:\n1. Visit https://makersuite.google.com/app/apikey\n2. Sign in with your Google account\n3. Create a new API key\n4. Add it to your `.env` file as: `GEMINI_API_KEY=your_key_here`",
            "timestamp": str(datetime.now()),
            "error": "API not configured"
        }
    
    def _get_default_alert(self, alert_type, plant_name, weather_data):
        """Default alert messages when Gemini is not available"""
        if alert_type == "rain":
            return f"🌧️ Rain Alert: Rain is expected in {weather_data.get('city', 'your area')} soon. Your {plant_name} is outdoors - consider moving it under shelter!"
        elif alert_type == "storm":
            return f"⚠️ Storm Alert: Severe weather is approaching {weather_data.get('city', 'your area')}. Please move your {plant_name} indoors immediately!"
        elif alert_type == "heat":
            return f"☀️ Heat Alert: It's very hot ({weather_data.get('temperature', 35)}°C) and sunny. Your {plant_name} may need extra water or shade. Check the soil moisture!"
        else:
            return f"Alert for {plant_name}: Please check your plant."

