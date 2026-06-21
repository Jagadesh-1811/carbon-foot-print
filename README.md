# 🌿 EcoTrace — AI-Powered Carbon Footprint Tracker

> **Challenge Vertical:** Sustainability / Smart Environmental Assistant  
> **Stack:** Python · FastAPI · Google Firebase · Gemini AI · Vanilla JS · HTML/CSS

---

## 📌 Overview

**EcoTrace** is a real-world, production-grade web application that helps individuals measure, understand, and actively reduce their personal carbon footprint. It combines:

- 🤖 **Gemini AI** for personalized, data-driven eco-recommendations
- 🔥 **Firebase Auth** for secure Google Sign-In
- 🗄️ **Firestore** for real-time persistent user data
- 📊 **Interactive dashboards** with live carbon tracking
- 🏆 **Gamification** — streaks, badges, leaderboards, and $TRACE rewards
- 🌍 **Community impact** — see collective savings across the platform

---

## 🎯 Chosen Vertical

> **Sustainability — Smart Environmental Assistant**

EcoTrace acts as a personalized sustainability coach. It:
- Accepts user lifestyle inputs (transport, diet, energy, flights, shopping)
- Calculates a detailed CO₂ breakdown with a letter grade (A–F)
- Uses **Gemini 1.5 Flash** to generate specific, actionable eco-tips tailored to that user's biggest emission categories
- Tracks progress over time, awards points, and shows community standings

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     FRONTEND (HTML/CSS/JS)               │
│  login · dashboard · calculator · goals · rewards ·     │
│  community · settings · support · terms · privacy        │
└───────────────────┬─────────────────────────────────────┘
                    │  HTTP / REST API
                    ▼
┌─────────────────────────────────────────────────────────┐
│               BACKEND  (FastAPI / Python)                │
│  /api/carbon    — CO₂ calculator & grade engine          │
│  /api/insights  — Gemini AI personalized tips            │
│  /api/goals     — Goal creation & progress tracking      │
│  /api/community — Leaderboard & global stats             │
│  /api/users     — Auth, profile, rewards ($TRACE)        │
└───────┬───────────────────────────┬─────────────────────┘
        │                           │
        ▼                           ▼
┌───────────────┐         ┌─────────────────────┐
│  Google       │         │   Google Gemini AI   │
│  Firebase     │         │   (gemini-1.5-flash) │
│  · Auth       │         │   Personalized tips  │
│  · Firestore  │         └─────────────────────┘
└───────────────┘
```

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔐 **Google Sign-In** | Real Firebase OAuth popup — no fake auth |
| 🧮 **Carbon Calculator** | 5-category breakdown: transport, food, energy, flights, shopping |
| 🤖 **AI Insights** | Gemini generates 4 personalized tips based on YOUR footprint |
| 🎯 **Goal Tracking** | Set CO₂ reduction goals with deadlines and progress bars |
| 🏆 **Gamification** | Earn $TRACE tokens, badges, streaks, and level up |
| 🌍 **Community** | Global leaderboard, challenges, and collective impact stats |
| 🎁 **Rewards Store** | Redeem $TRACE for real eco-rewards |
| ⚙️ **Settings** | Edit profile, dark mode toggle, notification preferences |
| 📱 **Responsive** | Works on mobile, tablet, and desktop |

---

## 🚀 Running Locally

### Prerequisites

- Python 3.10+
- A Firebase project with:
  - Authentication → Google Sign-In enabled
  - Firestore database created
  - Service account key downloaded
- A Google Gemini API key ([get one here](https://aistudio.google.com/app/apikey))

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/ecotrace-carbon-tracker.git
cd ecotrace-carbon-tracker

# 2. Create a virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r backend/requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your Firebase project ID, service account path, and Gemini key

# 5. Place your Firebase service account key
# Download from Firebase Console → Project Settings → Service Accounts
# Save as: backend/your-project-firebase-adminsdk.json
# Update GOOGLE_APPLICATION_CREDENTIALS in .env

# 6. Start the server
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 7. Open in browser
# http://localhost:8000
```

---

## 🔑 Firebase Setup Guide

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Create a project (or use existing)
3. Enable **Authentication → Sign-in method → Google**
4. Create a **Firestore Database** (start in test mode for local dev)
5. Go to **Project Settings → Service Accounts → Generate new private key**
6. Save the JSON file in `backend/` and update `GOOGLE_APPLICATION_CREDENTIALS` in `.env`
7. Update the Firebase client config in `frontend/templates/login.html` (lines 251–259) with your project's values

---

## 🤖 How Gemini AI Powers Insights

When a user submits their carbon calculator results:

1. The frontend sends the full CO₂ breakdown to `POST /api/insights/ai`
2. The backend builds a structured prompt with the user's data:
   ```
   Transport: 1,240 kg CO2/yr | Food: 2,500 kg (omnivore) | Energy: 480 kg | Flights: 510 kg
   ```
3. **Gemini 1.5 Flash** returns 4 highly specific recommendations targeting the user's biggest emission sources
4. If Gemini is unavailable (no API key), the system falls back to a curated static tip bank

**Example AI output:**
> "Replace your two short-haul flights with EU rail — saves ~510 kg CO₂/year and often costs less."

---

## 📂 Project Structure

```
ecotrace-carbon-tracker/
├── backend/
│   ├── main.py                    # FastAPI app, routing, middleware
│   ├── requirements.txt           # Python dependencies
│   ├── .env.example               # Environment variable template
│   ├── models/
│   │   ├── firebase_admin.py      # Firestore client initialization
│   │   └── schemas.py             # Pydantic request/response models
│   └── routers/
│       ├── carbon.py              # CO₂ calculator engine
│       ├── insights.py            # Gemini AI recommendations
│       ├── goals.py               # Goal creation & tracking
│       ├── community.py           # Leaderboard & challenges
│       └── users.py               # Auth, profile, $TRACE rewards
├── frontend/
│   ├── templates/                 # Jinja2 HTML pages
│   │   ├── index.html             # Landing page
│   │   ├── login.html             # Auth (Google Sign-In)
│   │   ├── dashboard.html         # User dashboard
│   │   ├── calculator.html        # Carbon footprint calculator
│   │   ├── goals.html             # Goal tracking
│   │   ├── rewards.html           # $TRACE rewards store
│   │   ├── settings.html          # User settings
│   │   └── ...                    # Privacy, terms, support pages
│   └── static/
│       ├── css/                   # Stylesheets
│       └── js/
│           └── api.js             # Frontend API client
├── .gitignore
├── .env.example
└── README.md
```

---

## 🔒 Security Considerations

- **No secrets in code** — all credentials via environment variables (`.env`)
- **Firebase ID token verification** — backend validates Google tokens server-side using `firebase_admin.auth.verify_id_token()`
- **Input validation** — all API inputs validated via Pydantic with field constraints (ge, le, max_length)
- **CORS** — configured via `CORS_ORIGINS` environment variable; locked down for production
- **Service account key** — excluded from version control via `.gitignore`
- **Password hashing** — PBKDF2-SHA256 with random salt for email/password auth fallback

---

## 🧪 API Testing

Once running, visit the interactive API docs:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Quick Test

```bash
# Calculate carbon footprint
curl -X POST http://localhost:8000/api/carbon/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "transport_km_per_day": 25,
    "diet_type": "omnivore",
    "electricity_kwh_per_month": 250,
    "flights_per_year": 2,
    "shopping_spend_usd_per_month": 200
  }'

# Get community stats
curl http://localhost:8000/api/community/stats

# Health check
curl http://localhost:8000/health
```

---

## 📊 Emission Factors Used

| Category | Factor | Source |
|---|---|---|
| Car transport | 0.21 kg CO₂/km | EPA / IPCC AR6 |
| Electricity | 0.40 kg CO₂/kWh | IEA Global Average 2023 |
| Short-haul flight | 255 kg CO₂/flight | IPCC AR6 |
| Shopping | 0.50 kg CO₂/USD | EPA lifecycle data |
| Vegan diet | 1,000 kg CO₂/year | Oxford Food & Climate |
| Omnivore diet | 2,500 kg CO₂/year | Oxford Food & Climate |

---

## 💡 Assumptions

1. **Transport** assumes a typical petrol/gasoline car (0.21 kg CO₂/km); EVs would be lower
2. **Electricity** uses the global average grid factor — India/USA/EU grids differ significantly
3. **Flights** are averaged as short-haul; long-haul would be higher
4. **Shopping** uses a simplified spend-based factor; actual varies by product type
5. The **$TRACE reward system** is a gamification layer — tokens have no monetary value in this prototype
6. **Firestore** is used as the primary database; the app includes a full in-memory fallback for demo/testing without Firebase credentials

---

## 🌱 What Makes This Stand Out

- **Real AI integration** — not just keyword matching, but actual Gemini context-aware recommendations
- **Real authentication** — Firebase Google OAuth (not a mock)
- **Graceful degradation** — works without Firebase or Gemini with realistic mock data
- **Gamification** — behavioral psychology drives sustained engagement
- **Production patterns** — environment config, error handling, Pydantic validation, modular routers
- **Accessibility** — semantic HTML, keyboard navigable, proper ARIA labels

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.

---

*Built with 💚 for the planet — EcoTrace 2025*
