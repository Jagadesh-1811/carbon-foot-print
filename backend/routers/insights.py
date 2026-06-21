from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import os, random

router = APIRouter()

# ─── Lazy Gemini init ─────────────────────────────────────────────────────────
_gemini_model = None

def get_gemini():
    global _gemini_model
    if _gemini_model is None:
        api_key = os.getenv("GEMINI_API_KEY", "")
        if api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                _gemini_model = genai.GenerativeModel("gemini-1.5-flash")
                print("[Gemini] Model loaded OK")
            except Exception as e:
                print(f"[Gemini] Init failed: {e}")
    return _gemini_model


# ─── Request schema ───────────────────────────────────────────────────────────
class InsightRequest(BaseModel):
    user_id:                      str
    total_co2_kg_per_year:        Optional[float] = None
    transport_co2:                Optional[float] = None
    food_co2:                     Optional[float] = None
    energy_co2:                   Optional[float] = None
    flights_co2:                  Optional[float] = None
    shopping_co2:                 Optional[float] = None
    diet_type:                    Optional[str]   = None
    transport_km_per_day:         Optional[float] = None
    electricity_kwh_per_month:    Optional[float] = None
    flights_per_year:             Optional[float] = None
    shopping_spend_usd_per_month: Optional[float] = None


# ─── Fallback bank (no emojis) ────────────────────────────────────────────────
FALLBACK_TIPS = [
    {"title": "Use public transport or cycle",    "impact": "Save up to 8 kg CO2",    "difficulty": "Easy",   "category": "transport", "accentColor": "#00C896"},
    {"title": "Try 3 meat-free days per week",    "impact": "Save up to 5 kg CO2",    "difficulty": "Easy",   "category": "food",      "accentColor": "#4FFFB0"},
    {"title": "Unplug idle devices at night",     "impact": "Save up to 2 kg CO2",    "difficulty": "Easy",   "category": "energy",    "accentColor": "#F5C842"},
    {"title": "Air-dry laundry instead of dryer", "impact": "Save 2.4 kg CO2",        "difficulty": "Easy",   "category": "energy",    "accentColor": "#F5C842"},
    {"title": "Buy second-hand clothing",         "impact": "Save up to 6 kg CO2",    "difficulty": "Medium", "category": "shopping",  "accentColor": "#3B9EFF"},
    {"title": "Replace one flight with a train",  "impact": "Save 200+ kg CO2",       "difficulty": "Hard",   "category": "transport", "accentColor": "#00C896"},
    {"title": "Lower thermostat by 2 degrees",    "impact": "Save 4 kg CO2/month",    "difficulty": "Easy",   "category": "energy",    "accentColor": "#F5C842"},
    {"title": "Switch to LED bulbs throughout",   "impact": "Save up to 10 kg CO2",   "difficulty": "Easy",   "category": "energy",    "accentColor": "#F5C842"},
    {"title": "Shop local and seasonal produce",  "impact": "Save 1.8 kg CO2",        "difficulty": "Easy",   "category": "food",      "accentColor": "#4FFFB0"},
    {"title": "Carpool to work twice a week",     "impact": "Save 12 kg CO2/month",   "difficulty": "Medium", "category": "transport", "accentColor": "#00C896"},
]

FUN_FACTS = [
    "A mature tree absorbs about 21 kg of CO2 per year.",
    "The average car emits 4.6 tonnes of CO2 per year — cycling cuts that to nearly zero.",
    "Beef production creates 27 kg CO2 per 100 g of protein vs 0.3 kg for tofu.",
    "One transatlantic flight emits more CO2 than 3 months of average driving.",
    "LED bulbs use 75% less energy than incandescent and last 25x longer.",
    "Oceans absorb 25% of all CO2 emitted — healthy oceans are our greatest climate ally.",
    "Producing 1 kg of beef requires 15,000 litres of water and emits 27 kg CO2.",
    "Working from home one day per week saves roughly 150 kg CO2 per year.",
]


def _build_gemini_prompt(req: InsightRequest) -> str:
    lines = [
        "You are an expert sustainability coach. Based on the user's carbon footprint data below,",
        "generate exactly 4 highly specific, actionable recommendations.",
        "",
        "User carbon data:",
        f"  Total annual footprint: {req.total_co2_kg_per_year or 'unknown'} kg CO2",
        f"  Transport: {req.transport_co2 or 'unknown'} kg CO2",
        f"  Food/diet: {req.food_co2 or 'unknown'} kg CO2 (diet: {req.diet_type or 'unknown'})",
        f"  Energy: {req.energy_co2 or 'unknown'} kg CO2 ({req.electricity_kwh_per_month or '?'} kWh/mo)",
        f"  Flights: {req.flights_co2 or 'unknown'} kg CO2 ({req.flights_per_year or '?'} flights/yr)",
        f"  Shopping: {req.shopping_co2 or 'unknown'} kg CO2 (${req.shopping_spend_usd_per_month or '?'}/mo)",
        "",
        "Return ONLY a JSON array with exactly 4 objects. No markdown, no explanation, just raw JSON.",
        'Each object must have: "title" (string, max 50 chars), "impact" (string, e.g. "Save 5 kg CO2"), "difficulty" (one of: Easy/Medium/Hard), "category" (one of: transport/food/energy/shopping/general).',
        "NO emojis in any field. Be specific to the user's highest-emission categories.",
    ]
    return "\n".join(lines)


async def _gemini_insights(req: InsightRequest):
    model = get_gemini()
    if not model:
        return None

    try:
        prompt = _build_gemini_prompt(req)
        response = model.generate_content(prompt)
        text = response.text.strip()

        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        import json
        raw = json.loads(text)

        accent_map = {
            "transport": "#00C896",
            "food":      "#4FFFB0",
            "energy":    "#F5C842",
            "shopping":  "#3B9EFF",
            "general":   "#9B8FFF",
        }

        tips = []
        for item in raw[:4]:
            cat = item.get("category", "general")
            tips.append({
                "title":       item.get("title", ""),
                "impact":      item.get("impact", ""),
                "difficulty":  item.get("difficulty", "Easy"),
                "category":    cat,
                "accentColor": accent_map.get(cat, "#00C896"),
            })
        return tips

    except Exception as e:
        print(f"[Gemini] Insight generation failed: {e}")
        return None


# ─── Endpoints ────────────────────────────────────────────────────────────────
@router.post("/ai", summary="Get Gemini AI-powered personalised insights")
async def get_ai_insights(req: InsightRequest):
    """
    Accepts carbon breakdown data and returns Gemini-generated personalised
    recommendations. Falls back to curated static tips if Gemini is unavailable.
    """
    tips = await _gemini_insights(req)

    if not tips:
        # Use top-scoring categories from breakdown as seed
        all_tips = FALLBACK_TIPS.copy()
        random.shuffle(all_tips)
        tips = all_tips[:4]

    return {
        "user_id":              req.user_id,
        "daily_recommendations": tips,
        "fun_fact":             random.choice(FUN_FACTS),
        "powered_by":           "gemini-1.5-flash" if get_gemini() else "static-fallback",
    }


@router.get("/{user_id}", summary="Get static personalised insights for a user")
async def get_insights(user_id: str, category: Optional[str] = None):
    """
    Returns daily recommendations filtered by category (static fallback endpoint).
    """
    cats = {"transport", "food", "energy", "shopping"}
    if category and category in cats:
        pool = [t for t in FALLBACK_TIPS if t["category"] == category]
    else:
        pool = FALLBACK_TIPS.copy()

    random.shuffle(pool)
    return {
        "user_id":               user_id,
        "daily_recommendations": pool[:4],
        "fun_fact":              random.choice(FUN_FACTS),
        "powered_by":            "static-fallback",
    }
