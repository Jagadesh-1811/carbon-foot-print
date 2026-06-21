from pydantic import BaseModel, Field
from typing import Literal, Optional, List


class CarbonInput(BaseModel):
    transport_km_per_day: float = Field(
        ..., ge=0, le=1000, description="Daily km traveled by car/bike/transit"
    )
    diet_type: Literal["vegan", "vegetarian", "omnivore", "meat_heavy"] = Field(
        ..., description="Primary diet type"
    )
    electricity_kwh_per_month: float = Field(
        ..., ge=0, le=5000, description="Monthly electricity consumption in kWh"
    )
    flights_per_year: int = Field(
        ..., ge=0, le=100, description="Number of flights (short-haul average)"
    )
    shopping_spend_usd_per_month: float = Field(
        ..., ge=0, le=10000, description="Monthly discretionary shopping in USD"
    )


class CarbonBreakdown(BaseModel):
    transport: float
    food: float
    energy: float
    flights: float
    shopping: float


class CarbonResult(BaseModel):
    total_co2_kg_per_year: float
    breakdown: CarbonBreakdown
    vs_global_average_percent: float
    reduction_potential_kg: float
    grade: str  # A, B, C, D, F
    tips: List[str]


class GoalCreate(BaseModel):
    user_id: str
    title: str
    target_kg: float = Field(..., gt=0, description="Target CO2 reduction in kg")
    deadline_days: int = Field(..., ge=7, le=365, description="Days until deadline")


class ActivityLog(BaseModel):
    user_id: str
    activity_type: Literal["transport", "food", "energy", "shopping"]
    description: str
    co2_kg: float = Field(..., ge=0)
    saved_kg: float = Field(..., ge=0)
