from fastapi import APIRouter
from models.schemas import CarbonInput, CarbonResult, CarbonBreakdown
from typing import List

router = APIRouter()

# ─── Emission Factors ─────────────────────────────────────────────────────────
DIET_FACTORS = {
    "vegan":        1000.0,   # kg CO2/year
    "vegetarian":   1500.0,
    "omnivore":     2500.0,
    "meat_heavy":   3300.0,
}

TRANSPORT_FACTOR   = 0.21    # kg CO2 per km  (average petrol car)
ELECTRICITY_FACTOR = 0.40    # kg CO2 per kWh (global avg grid)
FLIGHT_FACTOR      = 255.0   # kg CO2 per short-haul flight
SHOPPING_FACTOR    = 0.50    # kg CO2 per USD spent

GLOBAL_AVERAGE_KG  = 4000.0  # kg CO2/year global average per person

# ─── Grade Thresholds ─────────────────────────────────────────────────────────
GRADE_THRESHOLDS = [
    (1500,          "A"),
    (2500,          "B"),
    (3500,          "C"),
    (5000,          "D"),
    (float("inf"),  "F"),
]


def get_grade(total: float) -> str:
    for threshold, grade in GRADE_THRESHOLDS:
        if total <= threshold:
            return grade
    return "F"


def get_tips(breakdown: CarbonBreakdown, diet_type: str) -> List[str]:
    tips = []
    if breakdown.transport > 1000:
        tips.append(
            "Switch to public transport or cycling for short trips — "
            "cuts transport emissions by up to 70%."
        )
    if diet_type in ("omnivore", "meat_heavy"):
        tips.append(
            "Try 3 meat-free days per week — "
            "this alone can save approx 500 kg CO2/year."
        )
    if breakdown.energy > 800:
        tips.append(
            "Switch to LED bulbs and unplug idle devices — "
            "saves up to 200 kg CO2/year."
        )
    if breakdown.flights > 500:
        tips.append(
            "Replace one long-haul flight with a train — "
            "saves approx 1.5 tonnes CO2 per trip."
        )
    if breakdown.shopping > 300:
        tips.append(
            "Buy second-hand and repair instead of replace — "
            "reduces shopping footprint by 40%."
        )
    if not tips:
        tips.append(
            "Great work! Keep tracking your activities to maintain your low-carbon lifestyle."
        )
    return tips


# ─── Endpoints ────────────────────────────────────────────────────────────────
@router.post("/calculate", response_model=CarbonResult, summary="Calculate carbon footprint")
async def calculate_footprint(data: CarbonInput) -> CarbonResult:
    """
    Accepts lifestyle inputs and returns a detailed CO₂ breakdown,
    letter grade, comparison to global average, and personalised tips.
    """
    transport_co2 = data.transport_km_per_day * 365 * TRANSPORT_FACTOR
    food_co2      = DIET_FACTORS[data.diet_type]
    energy_co2    = data.electricity_kwh_per_month * 12 * ELECTRICITY_FACTOR
    flight_co2    = data.flights_per_year * FLIGHT_FACTOR
    shopping_co2  = data.shopping_spend_usd_per_month * 12 * SHOPPING_FACTOR

    total = transport_co2 + food_co2 + energy_co2 + flight_co2 + shopping_co2

    breakdown = CarbonBreakdown(
        transport=round(transport_co2, 1),
        food=round(food_co2, 1),
        energy=round(energy_co2, 1),
        flights=round(flight_co2, 1),
        shopping=round(shopping_co2, 1),
    )

    # Best-case baseline: vegan + no car + renewable energy + no flights
    baseline_min      = 1200.0
    reduction_potential = max(0.0, round(total - baseline_min, 1))
    vs_global           = round(((total - GLOBAL_AVERAGE_KG) / GLOBAL_AVERAGE_KG) * 100, 1)

    return CarbonResult(
        total_co2_kg_per_year=round(total, 1),
        breakdown=breakdown,
        vs_global_average_percent=vs_global,
        reduction_potential_kg=reduction_potential,
        grade=get_grade(total),
        tips=get_tips(breakdown, data.diet_type),
    )


@router.get("/factors", summary="Get emission factor reference values")
async def get_factors():
    """Returns the emission factors used in calculations for transparency."""
    return {
        "transport_kg_per_km":         TRANSPORT_FACTOR,
        "electricity_kg_per_kwh":      ELECTRICITY_FACTOR,
        "flight_kg_per_short_haul":    FLIGHT_FACTOR,
        "shopping_kg_per_usd":         SHOPPING_FACTOR,
        "diet_kg_per_year":            DIET_FACTORS,
        "global_average_kg_per_year":  GLOBAL_AVERAGE_KG,
        "source": "IPCC AR6, IEA 2023, EPA emission factors",
    }

@router.get("/dashboard/{user_id}", summary="Get dashboard summary")
async def get_dashboard(user_id: str):
    """Returns a real-time summary for the dashboard."""
    from routers.users import _db_available, MOCK_USERS
    from models.firebase_admin import get_db
    
    if _db_available():
        try:
            db = get_db()
            doc = db.collection("users").document(user_id).get()
            if doc.exists:
                u = doc.to_dict()
                return {
                    "total_co2_saved_kg": u.get("total_co2_saved_kg", 0.0),
                    "current_streak_days": u.get("current_streak_days", 1),
                    "eco_level": u.get("eco_level", 1),
                    "badges_earned": u.get("badges_earned", [1]),
                    "monthly_savings": u.get("monthly_savings", [15.2, 24.8, 20.1, 35.6, 42.0, 10.5, 14.8])
                }
        except Exception as e:
            print(f"[WARNING] Error fetching dashboard user from firestore: {e}")
            
    # Fallback to mock users
    if user_id in MOCK_USERS:
        u = MOCK_USERS[user_id]
        return {
            "total_co2_saved_kg": u.get("total_co2_saved_kg", 0.0),
            "current_streak_days": u.get("current_streak_days", 1),
            "eco_level": u.get("eco_level", 1),
            "badges_earned": u.get("badges_earned", [1]),
            "monthly_savings": u.get("monthly_savings", [15.2, 24.8, 20.1, 35.6, 42.0, 10.5, 14.8])
        }
        
    return {
        "total_co2_saved_kg": 420.5,
        "current_streak_days": 15,
        "eco_level": 4,
        "badges_earned": [1, 2, 3, 4, 5, 6, 7, 8],
        "monthly_savings": [15.2, 24.8, 20.1, 35.6, 42.0, 10.5, 14.8]
    }

from pydantic import BaseModel

class SaveCarbonRequest(BaseModel):
    user_id: str
    total_co2_kg_per_year: float
    saved_kg: float

@router.post("/save")
async def save_carbon_result(data: SaveCarbonRequest):
    from routers.users import _db_available, MOCK_USERS, generate_impact_id, DEFAULT_AVATAR
    from models.firebase_admin import get_db
    
    saved = data.saved_kg
    earned_trace = int(saved)
    
    # Generate default fallback info if user needs initialization
    name = data.user_id.split("-")[0].capitalize()
    email = data.user_id.replace("-", "@")
    if "@" not in email:
        email = f"{data.user_id}@ecotrace.org"
    
    if _db_available():
        db = get_db()
        ref = db.collection("users").document(data.user_id)
        doc = ref.get()
        if doc.exists:
            u = doc.to_dict()
            new_co2 = u.get("total_co2_saved_kg", 0.0) + saved
            new_balance = u.get("trace_balance", 4850) + earned_trace
            new_level = int(new_co2 / 100) + 1
            
            ref.update({
                "total_co2_saved_kg": round(new_co2, 2),
                "trace_balance": new_balance,
                "eco_level": new_level
            })
            return {"status": "success", "new_balance": new_balance, "total_saved": new_co2}
        else:
            # Auto-create user doc in database if not present
            user_data = {
                "uid": data.user_id,
                "displayName": name,
                "email": email.lower(),
                "eco_level": 1,
                "eco_title": "Eco Enthusiast",
                "total_co2_saved_kg": round(saved, 2),
                "current_streak_days": 1,
                "avatar_url": DEFAULT_AVATAR,
                "badges_earned": [1],
                "impact_id": generate_impact_id(name),
                "trace_balance": 4850 + earned_trace
            }
            ref.set(user_data)
            return {"status": "success", "new_balance": user_data["trace_balance"], "total_saved": user_data["total_co2_saved_kg"]}
    else:
        if data.user_id in MOCK_USERS:
            u = MOCK_USERS[data.user_id]
            new_co2 = u.get("total_co2_saved_kg", 0.0) + saved
            new_balance = u.get("trace_balance", 4850) + earned_trace
            new_level = int(new_co2 / 100) + 1
            
            MOCK_USERS[data.user_id]["total_co2_saved_kg"] = round(new_co2, 2)
            MOCK_USERS[data.user_id]["trace_balance"] = new_balance
            MOCK_USERS[data.user_id]["eco_level"] = new_level
            return {"status": "success", "new_balance": new_balance, "total_saved": new_co2}
        else:
            # Auto-create in mock dict
            user_data = {
                "uid": data.user_id,
                "displayName": name,
                "email": email.lower(),
                "eco_level": 1,
                "eco_title": "Eco Enthusiast",
                "total_co2_saved_kg": round(saved, 2),
                "current_streak_days": 1,
                "avatar_url": DEFAULT_AVATAR,
                "badges_earned": [1],
                "impact_id": generate_impact_id(name),
                "trace_balance": 4850 + earned_trace
            }
            MOCK_USERS[data.user_id] = user_data
            return {"status": "success", "new_balance": user_data["trace_balance"], "total_saved": user_data["total_co2_saved_kg"]}
