"""
Data Manager Module
Handles storage and retrieval of plant data and chat history
Uses JSON files for simplicity (can be upgraded to SQLite later)
"""
import json
import os
from datetime import datetime
from config import PLANTS_DB_FILE, CHAT_HISTORY_FILE

# User profile file
USER_PROFILE_FILE = "data/user_profile.json"

class DataManager:
    def __init__(self):
        self.plants_file = PLANTS_DB_FILE
        self.chat_file = CHAT_HISTORY_FILE
        self.user_file = USER_PROFILE_FILE
        self._ensure_files_exist()
    
    def _ensure_files_exist(self):
        """Create JSON files if they don't exist"""
        if not os.path.exists(self.plants_file):
            self._save_plants([])
        if not os.path.exists(self.chat_file):
            self._save_chat_history([])
        if not os.path.exists(self.user_file):
            self._save_user_profile({})
    
    def _save_plants(self, plants):
        """Save plants list to JSON file"""
        try:
            with open(self.plants_file, 'w', encoding='utf-8') as f:
                json.dump(plants, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving plants: {e}")
    
    def _load_plants(self):
        """Load plants list from JSON file"""
        try:
            with open(self.plants_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading plants: {e}")
            return []
    
    def add_plant(self, plant_data):
        """
        Add a new plant to the database
        plant_data should include: name, location, placement, sun_preference, etc.
        """
        plants = self._load_plants()
        
        # Generate unique ID
        new_id = max([p.get('id', 0) for p in plants] + [0]) + 1
        
        plant = {
            "id": new_id,
            "name": plant_data.get("name", "Unknown Plant"),
            "scientific_name": plant_data.get("scientific_name", ""),
            "description": plant_data.get("description", ""),
            "care_level": plant_data.get("care_level", "Moderate"),
            "location": plant_data.get("location", "Sialkot"),
            "placement": plant_data.get("placement", "Indoor Window"),  # Open Roof, Balcony, Indoor Window
            "sun_preference": plant_data.get("sun_preference", "Morning Sun"),  # Morning Sun, Afternoon Shade, Full Sun
            "watering_interval_days": plant_data.get("watering_interval_days", 3),
            "last_watered": plant_data.get("last_watered", None),
            "image_path": plant_data.get("image_path", ""),
            "added_date": datetime.now().isoformat(),
            "notes": plant_data.get("notes", "")
        }
        
        plants.append(plant)
        self._save_plants(plants)
        return plant
    
    def get_all_plants(self):
        """Get all plants from database"""
        return self._load_plants()
    
    def get_plant(self, plant_id):
        """Get a specific plant by ID"""
        plants = self._load_plants()
        for plant in plants:
            if plant.get('id') == plant_id:
                return plant
        return None
    
    def update_plant(self, plant_id, updates):
        """Update plant information"""
        plants = self._load_plants()
        for i, plant in enumerate(plants):
            if plant.get('id') == plant_id:
                plants[i].update(updates)
                self._save_plants(plants)
                return plants[i]
        return None
    
    def delete_plant(self, plant_id):
        """Delete a plant from database"""
        plants = self._load_plants()
        plants = [p for p in plants if p.get('id') != plant_id]
        self._save_plants(plants)
        return True
    
    def mark_watered(self, plant_id):
        """Mark plant as watered (update last_watered timestamp)"""
        return self.update_plant(plant_id, {
            "last_watered": datetime.now().isoformat()
        })
    
    def _save_chat_history(self, history):
        """Save chat history to JSON file"""
        try:
            with open(self.chat_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving chat history: {e}")
    
    def _load_chat_history(self):
        """Load chat history from JSON file"""
        try:
            with open(self.chat_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading chat history: {e}")
            return []
    
    def add_chat_message(self, user_message, bot_response, plant_context=""):
        """Add a chat message to history"""
        history = self._load_chat_history()
        
        chat_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_message": user_message,
            "bot_response": bot_response,
            "plant_context": plant_context
        }
        
        history.append(chat_entry)
        # Keep only last 100 messages
        if len(history) > 100:
            history = history[-100:]
        
        self._save_chat_history(history)
        return chat_entry
    
    def get_chat_history(self, limit=50):
        """Get recent chat history"""
        history = self._load_chat_history()
        return history[-limit:] if limit else history
    
    # User Profile Methods
    def _save_user_profile(self, profile):
        """Save user profile to JSON file"""
        try:
            os.makedirs(os.path.dirname(self.user_file), exist_ok=True)
            with open(self.user_file, 'w', encoding='utf-8') as f:
                json.dump(profile, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving user profile: {e}")
    
    def _load_user_profile(self):
        """Load user profile from JSON file"""
        try:
            if os.path.exists(self.user_file):
                with open(self.user_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading user profile: {e}")
            return {}
    
    def save_user_profile(self, profile_data):
        """Save or update user profile"""
        profile = {
            "name": profile_data.get("name", ""),
            "email": profile_data.get("email", ""),
            "phone": profile_data.get("phone", ""),
            "profession": profile_data.get("profession", ""),
            "location": profile_data.get("location", ""),
            "created_at": profile_data.get("created_at", datetime.now().isoformat()),
            "updated_at": datetime.now().isoformat()
        }
        self._save_user_profile(profile)
        return profile
    
    def get_user_profile(self):
        """Get current user profile"""
        return self._load_user_profile()
    
    def is_user_logged_in(self):
        """Check if user has a profile"""
        profile = self._load_user_profile()
        return bool(profile.get("name") or profile.get("email"))

