# 🚀 Setup & Deployment Guide

## 📋 Prerequisites

- Python 3.8+ (for local development)
- GitHub account (for deployment)
- API keys (see below)

---

## 🔑 Step 1: Get API Keys

### Required Keys

1. **OpenWeatherMap API** (Required)
   - Visit: https://openweathermap.org/api
   - Sign up (free)
   - Get API key from dashboard
   - Free tier: 1,000 calls/day

2. **Groq API** (Required)
   - Visit: https://console.groq.com/
   - Sign up (free)
   - Create API key
   - Free tier: Generous limits

### Optional Keys

3. **Google Gemini API** (Optional - for plant identification)
   - Visit: https://makersuite.google.com/app/apikey
   - Sign in with Google
   - Create API key
   - Free tier available

4. **Hugging Face API** (Optional - backup plant identification)
   - Visit: https://huggingface.co/settings/tokens
   - Create access token
   - Free tier available

---

## 💻 Step 2: Local Development Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Create `.streamlit/secrets.toml` File

Create a folder `.streamlit` in your project root, then create `secrets.toml`:

```toml
[api]
openweather_key = "your_openweather_api_key_here"
groq_key = "your_groq_api_key_here"
gemini_key = "your_gemini_api_key_here"
huggingface_key = "your_huggingface_api_key_here"
perenual_key = ""
default_location = "Sialkot,PK"
```

**Important**: Replace `your_xxx_api_key_here` with your actual keys!

### 3. Run the App

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

---

## ☁️ Step 3: Deploy to Streamlit Cloud

### 1. Push to GitHub

Make sure your code is pushed to GitHub (this repository).

**Important**: Never commit `.env` or `.streamlit/secrets.toml` files! They are already in `.gitignore`.

### 2. Go to Streamlit Cloud

1. Visit: https://share.streamlit.io
2. Sign in with GitHub
3. Click "New app"
4. Select your repository
5. Set main file: `app.py`

### 3. Add Secrets in Streamlit Cloud

1. In your app settings, go to **"Secrets"** tab
2. Paste this format:

```toml
[api]
openweather_key = "your_openweather_api_key_here"
groq_key = "your_groq_api_key_here"
gemini_key = "your_gemini_api_key_here"
huggingface_key = "your_huggingface_api_key_here"
perenual_key = ""
default_location = "Sialkot,PK"
```

3. Replace with your actual API keys
4. Click **"Save"**

### 4. Deploy!

1. Click **"Deploy"** or **"Redeploy"**
2. Wait 1-2 minutes
3. Your app will be live! 🎉

---

## 🔒 Security Notes

✅ **DO:**
- Use Streamlit Cloud secrets for deployment
- Use `.streamlit/secrets.toml` for local development
- Keep API keys private
- Never commit secrets to GitHub

❌ **DON'T:**
- Hardcode API keys in code
- Commit `.env` or `secrets.toml` files
- Share API keys publicly

---

## 🐛 Troubleshooting

### App won't start locally
- Check if `secrets.toml` exists in `.streamlit/` folder
- Verify API keys are correct (no extra spaces)
- Make sure all dependencies are installed: `pip install -r requirements.txt`

### API errors on Streamlit Cloud
- Verify secrets are set correctly in Streamlit Cloud dashboard
- Check API key format (no quotes needed in TOML)
- Ensure API keys are active and not expired

### Weather shows wrong location
- Set your location manually in the app: "📍 Location & Nurseries" page
- Update `default_location` in secrets if needed

---

## 📞 Need Help?

Check the main [README.md](README.md) for more information.

---

**Ready to deploy? Follow Step 3 above!** 🚀

