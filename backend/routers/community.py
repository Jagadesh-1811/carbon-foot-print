from fastapi import APIRouter
from models.firebase_admin import get_db

router = APIRouter()

# ─── Mock global stats (real values come from Firestore aggregation) ───────────
MOCK_GLOBAL_STATS = {
    "total_users": 48_291,
    "total_co2_saved_tonnes": 12_847,
    "trees_equivalent": 214_933,
    "cities_active": 87,
    "active_challenges": 12,
    "avg_reduction_percent": 23,
}

MOCK_LEADERBOARD = [
    {"rank": 1, "displayName": "Aria Chen",      "totalCO2Saved": 1240, "level": 8,  "streak": 92, "badges": ["🌿", "🚲", "🏆"]},
    {"rank": 2, "displayName": "Marcus O.",       "totalCO2Saved": 1108, "level": 7,  "streak": 74, "badges": ["🌿", "🥗", "⭐"]},
    {"rank": 3, "displayName": "Priya Patel",     "totalCO2Saved":  987, "level": 7,  "streak": 61, "badges": ["🌿", "💡", "🏆"]},
    {"rank": 4, "displayName": "Leo Müller",      "totalCO2Saved":  876, "level": 6,  "streak": 55, "badges": ["🌿", "🚲"]},
    {"rank": 5, "displayName": "Amara Diallo",    "totalCO2Saved":  743, "level": 6,  "streak": 48, "badges": ["🌿", "🥗"]},
    {"rank": 6, "displayName": "James Park",      "totalCO2Saved":  698, "level": 5,  "streak": 40, "badges": ["🌿"]},
    {"rank": 7, "displayName": "Sofia Rossi",     "totalCO2Saved":  612, "level": 5,  "streak": 33, "badges": ["🌿", "💡"]},
    {"rank": 8, "displayName": "Chen Wei",        "totalCO2Saved":  541, "level": 4,  "streak": 28, "badges": ["🌿"]},
    {"rank": 9, "displayName": "Fatima Al-Said",  "totalCO2Saved":  489, "level": 4,  "streak": 21, "badges": ["🌿"]},
    {"rank": 10, "displayName": "Noah Williams",  "totalCO2Saved":  412, "level": 3,  "streak": 14, "badges": ["🌿"]},
]


def _db_available() -> bool:
    return get_db() is not None


# ─── Endpoints ────────────────────────────────────────────────────────────────
@router.get("/stats", summary="Get global community impact statistics")
async def get_community_stats():
    """
    Returns platform-wide impact numbers shown on the landing page.
    Falls back to realistic mock data when Firebase is not connected.
    """
    if not _db_available():
        return MOCK_GLOBAL_STATS

    # When Firestore is connected, aggregate from users collection
    db = get_db()
    try:
        users_ref = db.collection("users").stream()
        total_users = 0
        total_saved = 0.0
        for doc in users_ref:
            u = doc.to_dict()
            total_users += 1
            total_saved += u.get("totalCO2Saved", 0)

        return {
            "total_users": total_users,
            "total_co2_saved_tonnes": round(total_saved / 1000, 1),
            "trees_equivalent": int(total_saved / 21),   # 1 tree ≈ 21 kg CO2/year
            "cities_active": MOCK_GLOBAL_STATS["cities_active"],
            "active_challenges": MOCK_GLOBAL_STATS["active_challenges"],
            "avg_reduction_percent": MOCK_GLOBAL_STATS["avg_reduction_percent"],
        }
    except Exception:
        return MOCK_GLOBAL_STATS


@router.get("/leaderboard", summary="Get top users by CO₂ saved")
async def get_leaderboard(limit: int = 10):
    """
    Returns the top N users ranked by total CO₂ saved.
    Falls back to mock leaderboard when Firebase is not connected.
    """
    if not _db_available():
        return {"leaderboard": MOCK_LEADERBOARD[:limit]}

    db = get_db()
    try:
        users_ref = (
            db.collection("users")
            .order_by("totalCO2Saved", direction="DESCENDING")
            .limit(limit)
            .stream()
        )
        leaderboard = []
        for i, doc in enumerate(users_ref, start=1):
            u = doc.to_dict()
            leaderboard.append(
                {
                    "rank": i,
                    "uid": doc.id,
                    "displayName": u.get("displayName", "Anonymous"),
                    "totalCO2Saved": u.get("totalCO2Saved", 0),
                    "level": u.get("level", 1),
                    "badges": u.get("badges", []),
                    "streak": u.get("streak", 0),
                }
            )
        return {"leaderboard": leaderboard}
    except Exception:
        return {"leaderboard": MOCK_LEADERBOARD[:limit]}


@router.get("/challenges", summary="List active community challenges")
async def get_challenges():
    """Returns a list of currently active community challenges."""
    return {
        "challenges": [
            {
                "id": "c1",
                "title": "🌍 Zero Meat Week",
                "description": "Eat plant-based for 7 days",
                "reward": "🏆 Green Champion Badge",
                "participants": 1247,
                "ends_in_days": 4,
                "co2_saved_avg": "3.5 kg per person",
            },
            {
                "id": "c2",
                "title": "🚶 Walk 10K Steps Daily",
                "description": "Walk or cycle instead of driving for a week",
                "reward": "👟 Eco Walker Badge",
                "participants": 893,
                "ends_in_days": 4,
                "co2_saved_avg": "2.1 kg per person",
            },
            {
                "id": "c3",
                "title": "🛒 Zero Plastic Week",
                "description": "Avoid single-use plastics for 7 days",
                "reward": "🌊 Ocean Guardian Badge",
                "participants": 724,
                "ends_in_days": 4,
                "co2_saved_avg": "1.2 kg per person",
            },
        ]
    }
