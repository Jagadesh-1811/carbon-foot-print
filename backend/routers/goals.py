from fastapi import APIRouter, HTTPException
from models.schemas import GoalCreate
from models.firebase_admin import get_db
from datetime import datetime, timedelta

router = APIRouter()


def _db_available() -> bool:
    """Check if Firestore is initialized."""
    return get_db() is not None


# ─── Endpoints ────────────────────────────────────────────────────────────────
@router.post("/", summary="Create a new carbon-reduction goal")
async def create_goal(data: GoalCreate):
    """Creates a goal in Firestore for a given user."""
    if not _db_available():
        # Return mock success when Firebase not yet configured
        return {
            "goal_id": "mock-goal-001",
            "message": "Goal created (mock — configure Firebase to persist)",
            "goal": {
                "userId": data.user_id,
                "title": data.title,
                "targetKg": data.target_kg,
                "currentKg": 0.0,
                "deadlineDays": data.deadline_days,
                "completed": False,
            },
        }

    db = get_db()
    deadline = datetime.utcnow() + timedelta(days=data.deadline_days)
    goal_data = {
        "userId": data.user_id,
        "title": data.title,
        "targetKg": data.target_kg,
        "currentKg": 0.0,
        "deadline": deadline,
        "completed": False,
        "createdAt": datetime.utcnow(),
    }
    _, ref = db.collection("goals").add(goal_data)
    return {"goal_id": ref.id, "message": "Goal created successfully ✅"}


@router.get("/{user_id}", summary="Get all active goals for a user")
async def get_user_goals(user_id: str):
    """Fetches all incomplete goals for the user from Firestore."""
    if not _db_available():
        # Return demo goals when Firebase not configured
        return {
            "goals": [
                {
                    "id": "demo-1",
                    "title": "Reduce Transport CO₂",
                    "targetKg": 50,
                    "currentKg": 32,
                    "progress_percent": 64,
                    "completed": False,
                },
                {
                    "id": "demo-2",
                    "title": "Cut Food Emissions",
                    "targetKg": 30,
                    "currentKg": 18,
                    "progress_percent": 60,
                    "completed": False,
                },
            ]
        }

    db = get_db()
    goals_ref = (
        db.collection("goals")
        .where("userId", "==", user_id)
        .where("completed", "==", False)
        .stream()
    )
    goals = []
    for doc in goals_ref:
        g = doc.to_dict()
        g["id"] = doc.id
        g["progress_percent"] = (
            round((g["currentKg"] / g["targetKg"]) * 100, 1)
            if g.get("targetKg", 0) > 0
            else 0
        )
        goals.append(g)
    return {"goals": goals}


@router.patch("/{goal_id}/progress", summary="Update goal progress")
async def update_progress(goal_id: str, added_kg: float):
    """Adds `added_kg` to the goal's current progress and marks complete if reached."""
    if not _db_available():
        return {"message": "Mock update — Firebase not configured", "added_kg": added_kg}

    db = get_db()
    ref = db.collection("goals").document(goal_id)
    doc = ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Goal not found")

    data = doc.to_dict()
    new_current = round(data["currentKg"] + added_kg, 2)
    completed = new_current >= data["targetKg"]
    ref.update({"currentKg": new_current, "completed": completed})
    return {
        "goal_id": goal_id,
        "new_current_kg": new_current,
        "target_kg": data["targetKg"],
        "completed": completed,
    }


@router.delete("/{goal_id}", summary="Delete a goal")
async def delete_goal(goal_id: str):
    if not _db_available():
        return {"message": "Mock delete — Firebase not configured"}
    db = get_db()
    db.collection("goals").document(goal_id).delete()
    return {"message": f"Goal {goal_id} deleted ✅"}
