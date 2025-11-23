"""
Hugging Face AI Service Module
Handles all Hugging Face API interactions for plant identification and health analysis
Uses vision-language models for image understanding
"""
import requests
import config
from PIL import Image
import io
import base64
from datetime import datetime

class HuggingFaceService:
    def __init__(self):
        # Access API key dynamically from config module (supports secrets.toml)
        self.api_key = config.HUGGINGFACE_API_KEY
        # Use BLIP2 for better vision-language understanding
        # Falls back to BLIP if BLIP2 is not available
        # Use Visual Question Answering model for better plant identification
        self.identification_model = "dandelin/vilt-b32-finetuned-vqa"
        self.health_model = "Salesforce/blip-image-captioning-large"
        
        # Silently handle missing API key (optional feature)
        # No error message needed - features will gracefully degrade
    
    def _image_to_base64(self, image):
        """Convert PIL Image to base64 string"""
        if isinstance(image, bytes):
            image = Image.open(io.BytesIO(image))
        elif not isinstance(image, Image.Image):
            if hasattr(image, 'read'):
                image.seek(0)
                image = Image.open(image)
            else:
                image = Image.open(image)
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Save to bytes
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        img_bytes = buffered.getvalue()
        
        return base64.b64encode(img_bytes).decode('utf-8')
    
    def _query_huggingface(self, image_base64, model_name, prompt=None):
        """Query Hugging Face Inference API - Using new router endpoint"""
        # Use new router endpoint (old api-inference.huggingface.co is deprecated)
        API_URL = f"https://router.huggingface.co/models/{model_name}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        # For BLIP models, we send the image
        # Some models support prompts, but BLIP-image-captioning doesn't
        # We'll use the caption and then process it
        
        try:
            # Decode base64 to bytes
            image_bytes = base64.b64decode(image_base64)
            
            response = requests.post(API_URL, headers=headers, data=image_bytes, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return result
            elif response.status_code == 503:
                # Model is loading, wait and retry
                print("⏳ Model is loading, please wait...")
                return {"error": "Model is loading, please try again in a moment"}
            else:
                return {"error": f"API Error: {response.status_code} - {response.text}"}
        except requests.exceptions.Timeout:
            return {"error": "Request timeout. Please try again."}
        except Exception as e:
            return {"error": f"Error: {str(e)}"}
    
    def identify_plant(self, image):
        """
        Identify plant from uploaded image using Hugging Face VQA Model
        Returns: dict with plant name and confidence
        """
        if not self.api_key:
            return self._get_mock_identification()
        
        try:
            # Convert image to bytes for VQA model
            if isinstance(image, bytes):
                image_bytes = image
            else:
                # Convert PIL Image to bytes
                if not isinstance(image, Image.Image):
                    if hasattr(image, 'read'):
                        image.seek(0)
                        image = Image.open(image)
                    else:
                        image = Image.open(image)
                
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                
                buffered = io.BytesIO()
                image.save(buffered, format="JPEG")
                image_bytes = buffered.getvalue()
            
            # Use VQA model with specific questions
            print("🔍 Querying Hugging Face VQA for plant identification...")
            
            # Question 1: What kind of plant is this?
            result1 = self._query_vqa(image_bytes, "What kind of plant is this?")
            
            # Question 2: What is the common name of this plant?
            result2 = self._query_vqa(image_bytes, "What is the common name of this plant?")
            
            # Extract answers
            plant_name = "Unknown Plant"
            if isinstance(result1, list) and len(result1) > 0:
                plant_name = result1[0].get('answer', 'Unknown Plant')
            elif isinstance(result2, list) and len(result2) > 0:
                plant_name = result2[0].get('answer', 'Unknown Plant')
            
            # Clean up the plant name
            plant_name = plant_name.strip()
            if not plant_name or plant_name.lower() in ['unknown', 'i don\'t know', 'i cannot']:
                plant_name = "Unknown Plant"
            
            print(f"📝 Identified: {plant_name}")
            
            return {
                "plant_name": plant_name,
                "scientific_name": "Unknown",
                "description": f"This appears to be a {plant_name.lower()}.",
                "care_level": "Moderate",
                "confidence": "Medium",
                "full_response": f"Plant identified as: {plant_name}",
                "source": "Hugging Face VQA"
            }
            
        except Exception as e:
            print(f"❌ Plant identification error: {e}")
            return self._get_mock_identification()
    
    def _query_vqa(self, image_bytes, question):
        """Query Hugging Face VQA model with image and question"""
        API_URL = f"https://router.huggingface.co/models/{self.identification_model}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        try:
            # VQA model expects JSON with image and question
            import json
            import base64
            
            # Encode image to base64
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')
            
            payload = {
                "inputs": {
                    "image": image_b64,
                    "question": question
                }
            }
            
            response = requests.post(
                API_URL, 
                headers=headers, 
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 503:
                return {"error": "Model is loading, please try again in a moment"}
            else:
                # Try alternative format (raw bytes)
                response = requests.post(
                    API_URL,
                    headers=headers,
                    data=image_bytes,
                    params={"question": question},
                    timeout=30
                )
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"API Error: {response.status_code}"}
        except Exception as e:
            return {"error": f"Error: {str(e)}"}
    
    def _extract_plant_name(self, caption):
        """Extract plant name from caption"""
        caption_lower = caption.lower()
        
        # Common plant keywords
        plant_keywords = {
            'tomato': 'Tomato Plant',
            'rose': 'Rose',
            'snake plant': 'Snake Plant',
            'aloe': 'Aloe Vera',
            'pothos': 'Pothos',
            'philodendron': 'Philodendron',
            'basil': 'Basil',
            'mint': 'Mint',
            'lavender': 'Lavender',
            'sunflower': 'Sunflower',
            'cactus': 'Cactus',
            'fern': 'Fern',
            'ivy': 'Ivy',
            'jade': 'Jade Plant',
            'spider plant': 'Spider Plant'
        }
        
        # Check for plant keywords
        for keyword, plant_name in plant_keywords.items():
            if keyword in caption_lower:
                return plant_name
        
        # If no match, try to extract from first few words
        words = caption.split()[:5]
        if words:
            return ' '.join(words).title()
        
        return "Unknown Plant"
    
    def _enhance_identification(self, caption):
        """Enhance identification using text generation"""
        # Use Hugging Face text generation to get more details
        # For now, return None and use basic extraction
        # Can be enhanced later with a text generation model
        return None
    
    def analyze_plant_health(self, image, user_question=""):
        """
        Analyze plant health from image and user question
        Returns: AI-generated diagnosis and recommendations
        """
        if not self.api_key:
            return {
                "analysis": "⚠️ Hugging Face API is not configured. Please check your API key in the .env file.",
                "timestamp": str(datetime.now()),
                "error": "API not configured"
            }
        
        try:
            # Convert image to base64
            image_base64 = self._image_to_base64(image)
            
            # Get image caption
            print("🔍 Querying Hugging Face for health analysis...")
            result = self._query_huggingface(image_base64, self.health_model)
            
            if "error" in result:
                error_msg = result['error']
                print(f"❌ Hugging Face API Error: {error_msg}")
                return {
                    "analysis": f"⚠️ **API Error**: {error_msg}\n\nPlease check your Hugging Face API key in the `.env` file and ensure it's valid.",
                    "timestamp": str(datetime.now()),
                    "error": error_msg
                }
            
            # Extract caption
            if isinstance(result, list) and len(result) > 0:
                caption = result[0].get('generated_text', '')
            elif isinstance(result, dict):
                caption = result.get('generated_text', '')
            else:
                caption = str(result)
            
            print(f"📝 Hugging Face Health Caption: {caption[:200]}...")
            
            # Enhance the analysis with health-specific information
            analysis = self._create_health_analysis(caption, user_question)
            
            return {
                "analysis": analysis,
                "timestamp": str(datetime.now()),
                "error": None,
                "source": "Hugging Face"
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Health analysis error: {error_msg}")
            return {
                "analysis": f"⚠️ **Error**: {error_msg}\n\nPlease try again or check your API configuration.",
                "timestamp": str(datetime.now()),
                "error": error_msg
            }
    
    def _create_health_analysis(self, caption, user_question):
        """Create detailed health analysis from caption"""
        analysis_parts = []
        
        # Add user question context
        if user_question:
            analysis_parts.append(f"**Your Question**: {user_question}\n")
        
        # Analyze caption for health indicators
        caption_lower = caption.lower()
        
        # Health status
        if any(word in caption_lower for word in ['healthy', 'green', 'vibrant', 'thriving', 'good']):
            health_status = "**Health Status**: Good to Excellent"
        elif any(word in caption_lower for word in ['yellow', 'wilting', 'drooping', 'brown', 'dying']):
            health_status = "**Health Status**: Fair to Poor - Needs Attention"
        else:
            health_status = "**Health Status**: Requires Assessment"
        
        analysis_parts.append(health_status)
        analysis_parts.append("\n**Visual Analysis**:")
        analysis_parts.append(caption)
        
        # Add recommendations based on common issues
        if 'yellow' in caption_lower:
            analysis_parts.append("\n**Possible Causes**:")
            analysis_parts.append("- Overwatering or underwatering")
            analysis_parts.append("- Nutrient deficiency")
            analysis_parts.append("- Insufficient light")
            analysis_parts.append("\n**Recommendations**:")
            analysis_parts.append("1. Check soil moisture - water only when top inch is dry")
            analysis_parts.append("2. Ensure adequate drainage")
            analysis_parts.append("3. Provide balanced fertilizer")
            analysis_parts.append("4. Move to brighter location if needed")
        
        if 'brown' in caption_lower or 'dry' in caption_lower:
            analysis_parts.append("\n**Possible Causes**:")
            analysis_parts.append("- Underwatering")
            analysis_parts.append("- Low humidity")
            analysis_parts.append("- Too much direct sunlight")
            analysis_parts.append("\n**Recommendations**:")
            analysis_parts.append("1. Increase watering frequency")
            analysis_parts.append("2. Mist leaves to increase humidity")
            analysis_parts.append("3. Provide shade during hottest hours")
        
        if 'healthy' in caption_lower or 'green' in caption_lower:
            analysis_parts.append("\n**Maintenance Tips**:")
            analysis_parts.append("1. Continue current care routine")
            analysis_parts.append("2. Monitor for any changes")
            analysis_parts.append("3. Prune dead leaves regularly")
            analysis_parts.append("4. Fertilize during growing season")
        
        return "\n".join(analysis_parts)
    
    def _get_mock_identification(self):
        """Fallback mock identification"""
        return {
            "plant_name": "Unknown Plant",
            "scientific_name": "Unknown",
            "description": "Could not identify plant. Please check your Hugging Face API key.",
            "care_level": "Moderate",
            "confidence": "Low",
            "full_response": "API not configured",
            "source": "Mock"
        }

