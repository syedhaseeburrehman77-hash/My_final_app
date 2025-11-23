# 🌱 Smart Garden App

An AI-powered plant care application that helps you manage your garden using weather data, AI plant identification, and smart care reminders.

## ✨ Features

- **📊 Garden Dashboard**: Real-time weather, plant status cards, and intelligent alerts
- **🌱 AI Plant Identification**: Upload photos to identify plants automatically
- **🤖 AI Botanist Chat**: Get personalized plant care advice
- **📍 Location & Nurseries**: Find nearby plant nurseries
- **👤 User Profile**: Track your garden progress

## 🚀 Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd Smart_Garden_app
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up API keys** (see [SETUP.md](SETUP.md))

4. **Run the app**
   ```bash
   streamlit run app.py
   ```

### Streamlit Cloud Deployment

1. **Push to GitHub** (this repository)

2. **Go to [Streamlit Cloud](https://share.streamlit.io)**

3. **Connect your GitHub repository**

4. **Add secrets** in Streamlit Cloud dashboard:
   - Go to Settings → Secrets
   - Paste the TOML format (see [SETUP.md](SETUP.md))

5. **Deploy!** Your app will be live in minutes.

## 🔑 Required API Keys

- **OpenWeatherMap**: Weather data (free tier available)
- **Groq**: Fast AI chatbot responses (free tier available)
- **Google Gemini**: Plant identification (optional, free tier available)
- **Hugging Face**: Plant identification backup (optional, free tier available)

Get your API keys and setup instructions in [SETUP.md](SETUP.md).

## 📁 Project Structure

```
Smart_Garden_app/
├── app.py                 # Main Streamlit application
├── config.py              # Configuration (API keys loaded from secrets)
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── SETUP.md               # Setup and deployment guide
├── utils/                 # Service modules
│   ├── weather_service.py
│   ├── plant_service.py
│   ├── gemini_service.py
│   ├── groq_service.py
│   ├── huggingface_service.py
│   └── data_manager.py
└── .gitignore            # Git ignore rules (protects API keys)
```

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **AI/ML**: Google Gemini, Groq, Hugging Face
- **Weather**: OpenWeatherMap API
- **Storage**: JSON files

## 📝 License

Open source - available for personal and educational use.

## 🙏 Credits

**Team**: Haseeb, Zahra Zahid, Maira, Zahra Mumtaz

Built with ❤️ for plant lovers everywhere! 🌱
