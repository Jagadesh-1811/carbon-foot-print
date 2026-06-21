from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import os
import time

from routers import carbon, insights, goals, community, users
from models.firebase_admin import init_firebase

load_dotenv()

# ─── Firebase Initialization ─────────────────────────────────────────────────
try:
    init_firebase()
except Exception as e:
    print(f"[WARNING] Firebase init skipped: {e}")

# ─── Application ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="EcoTrace API",
    description=(
        "AI-powered carbon footprint tracking platform. "
        "Track, reduce, and gamify your environmental impact. "
        "Powered by Google Gemini AI and Firebase."
    ),
    version="1.0.0",
    contact={
        "name": "EcoTrace",
        "url": "https://github.com/YOUR_USERNAME/ecotrace-carbon-tracker",
    },
    license_info={
        "name": "MIT",
    },
    docs_url="/docs",
    redoc_url="/redoc",
)

# Mount static files and templates from frontend directory using absolute paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))

app.mount("/static", StaticFiles(directory=os.path.join(FRONTEND_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(FRONTEND_DIR, "templates"))

# ─── CORS ────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(carbon.router,    prefix="/api/carbon",    tags=["Carbon Calculator"])
app.include_router(insights.router,  prefix="/api/insights",  tags=["AI Insights"])
app.include_router(goals.router,     prefix="/api/goals",     tags=["Goals"])
app.include_router(community.router, prefix="/api/community", tags=["Community"])
app.include_router(users.router,     prefix="/api/users",     tags=["Users"])


@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/calculator", response_class=HTMLResponse)
async def calculator_page(request: Request):
    return templates.TemplateResponse("calculator.html", {"request": request})

@app.get("/goals", response_class=HTMLResponse)
async def goals_page(request: Request):
    return templates.TemplateResponse("goals.html", {"request": request})

@app.get("/rewards", response_class=HTMLResponse)
async def rewards_page(request: Request):
    return templates.TemplateResponse("rewards.html", {"request": request})

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    return templates.TemplateResponse("settings.html", {"request": request})

@app.get("/terms", response_class=HTMLResponse)
async def terms_page(request: Request):
    return templates.TemplateResponse("terms.html", {"request": request})

@app.get("/privacy", response_class=HTMLResponse)
async def privacy_page(request: Request):
    return templates.TemplateResponse("privacy.html", {"request": request})


@app.get("/support", response_class=HTMLResponse)
async def support_page(request: Request):
    return templates.TemplateResponse("support.html", {"request": request})

@app.get("/services", response_class=HTMLResponse)
async def services_page(request: Request):
    return templates.TemplateResponse("services.html", {"request": request})



@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Carbon Footprint API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
