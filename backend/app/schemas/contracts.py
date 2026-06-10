from pydantic import BaseModel, Field, field_validator
from typing import Any
import math
class AHPWeights(BaseModel):
    ph: float = Field(..., ge=0.0, le=1.0, description="Soil pH factor weight metrics")
    slope: float = Field(..., ge=0.0, le=1.0, description="Topographic slope constraint weight")
    water: float = Field(..., ge=0.0, le=1.0, description="Hydro proximity criteria weight")
    @field_validator("water", mode="after")
    @classmethod
    def validate_weights_sum(cls, v: float, info: Any) -> float:
        """Enforces Analytical Hierarchy Process validation contract (Σw_i == 1.0)."""
        data = info.data
        if "ph" in data and "slope" in data:
            total_sum = data["ph"] + data["slope"] + v
            if not math.isclose(total_sum, 1.0, abs_tol=1e-5):
                raise ValueError(f"Analytical priority constraints must sum up to exactly 1.0. Got: {total_sum}")
        return v
class OptimizationRequest(BaseModel):
    crop_id: str = Field(..., description="Target crop workspace registration signature")
    weights: AHPWeights
