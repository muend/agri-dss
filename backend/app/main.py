import json
from contextlib import asynccontextmanager

import asyncio
import numpy as np
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.schemas.contracts import OptimizationRequest
from app.core.ingestion import IngestionEngine

# ════════════════════════════════════════════════════════════════
# CROP-SPECIFIC ANALYTICAL MATRIX
#
# The crop_id token is a live computational switch, not metadata.
# Each registry entry defines an ecological modulation profile that
# transforms the baseline criteria matrix X = [x1_ph, x2_slope,
# x3_water] BEFORE the weighted overlay executes, so the three crops
# exhibit distinctly different spatial behaviors:
#
#   CRP-01 Olive      — exponential reward on pH and slope criteria
#                       (concave power-law boost: thrives on mild
#                       slopes and alkaline soil chemistry).
#   CRP-02 Citrus     — severe hydrographic penalty: cells with
#                       x3_water < 0.4 have their water criterion
#                       crushed by a 0.2 multiplier.
#   CRP-03 Greenhouse — absolute flatness constraint: terrain
#                       steepness (1 - x2_slope) above the strict
#                       0.35 ceiling forces the final score to zero.
#
# Final fused expression:  S_c = f(X, crop_id) · Wᵀ
# ════════════════════════════════════════════════════════════════

CROP_MATRIX = {
    "CRP-01": {
        "label": "Olea Europaea (Olive Matrix)",
        "ph_exponent": 0.60,        # x^0.6 — concave reward lifting strong-pH cells
        "slope_exponent": 0.70,     # x^0.7 — concave reward tolerating mild slopes
        "water_floor": None,
        "water_penalty": 1.0,
        "steepness_ceiling": None,
    },
    "CRP-02": {
        "label": "Citrus Sinensis (Orchard Grid)",
        "ph_exponent": 1.0,
        "slope_exponent": 1.0,
        "water_floor": 0.40,        # severe penalty threshold on x3_water
        "water_penalty": 0.20,      # multiplier applied below the floor
        "steepness_ceiling": None,
    },
    "CRP-03": {
        "label": "Solanum Lycopersicum (Greenhouse)",
        "ph_exponent": 1.0,
        "slope_exponent": 1.0,
        "water_floor": None,
        "water_penalty": 1.0,
        "steepness_ceiling": 0.35,  # max permissible steepness = 1 - x2_slope
    },
}


def apply_crop_modulation(local_gdf, crop_id: str, w: np.ndarray) -> np.ndarray:
    """Transform the criteria matrix per crop profile and fuse the overlay.

    Computes S_c = f(X, crop_id) · Wᵀ as vectorized NumPy operations:
    the criteria matrix X (N×3) is modulated by the crop profile, then
    collapsed against the AHP weight vector in a single dot product.
    Any hard ecological constraint is applied as a multiplicative
    binary mask on the fused result.
    """
    profile = CROP_MATRIX[crop_id]

    x1 = local_gdf["x1_ph"].to_numpy(dtype=np.float64)
    x2 = local_gdf["x2_slope"].to_numpy(dtype=np.float64)
    x3 = local_gdf["x3_water"].to_numpy(dtype=np.float64)

    # ── CRP-01: exponential (power-law) reward on pH and slope. ──
    x1_mod = np.power(x1, profile["ph_exponent"])
    x2_mod = np.power(x2, profile["slope_exponent"])

    # ── CRP-02: severe hydrographic proximity penalty. ──
    if profile["water_floor"] is not None:
        x3_mod = np.where(
            x3 < profile["water_floor"],
            x3 * profile["water_penalty"],
            x3,
        )
    else:
        x3_mod = x3

    # ── Fused weighted overlay: (N×3) @ (3,) → (N,). ──
    x_matrix = np.column_stack((x1_mod, x2_mod, x3_mod))
    scores = x_matrix @ w

    # ── CRP-03: absolute flatness constraint (hard zero mask). ──
    if profile["steepness_ceiling"] is not None:
        steepness = 1.0 - x2
        flat_mask = (steepness <= profile["steepness_ceiling"]).astype(np.float64)
        scores = scores * flat_mask

    return np.clip(scores, 0.0, 1.0)


# Global in-memory cache registry container
GLOBAL_WORKSPACE = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-caches spatial geometry registries inside system memory at bootstrap runtime."""
    global GLOBAL_WORKSPACE
    loop = asyncio.get_running_loop()
    # Execute non-blocking ingestion call over the executor threadpool
    GLOBAL_WORKSPACE = await loop.run_in_executor(None, IngestionEngine.get_data)
    yield
    GLOBAL_WORKSPACE = None


app = FastAPI(
    title="Agri-DSS Matrix Core Engine",
    description="High-performance vectorized overlay router for regional planning analytics.",
    version="0.4.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://tarimsalkoridor.online",
        "https://www.tarimsalkoridor.online",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.get("/api/health", status_code=status.HTTP_200_OK)
async def system_health_census():
    if GLOBAL_WORKSPACE is None:
        raise HTTPException(status_code=503, detail="Spatial matrix repository allocation uninitialized.")
    return {
        "status": "synchronized",
        "cached_cell_count": len(GLOBAL_WORKSPACE),
        "crs_signature": str(GLOBAL_WORKSPACE.crs),
        "spatial_bounding_box": GLOBAL_WORKSPACE.total_bounds.tolist(),
        "crop_registry": {token: profile["label"] for token, profile in CROP_MATRIX.items()},
    }


@app.post("/api/optimize", status_code=status.HTTP_200_OK)
async def resolve_spatial_suitability(payload: OptimizationRequest):
    """Executes the crop-modulated vectorized overlay S_c = f(X, crop_id) · Wᵀ in O(N)."""
    if GLOBAL_WORKSPACE is None:
        raise HTTPException(status_code=503, detail="Analytical core memory registry allocation offline.")

    if payload.crop_id not in CROP_MATRIX:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Unknown crop registry token '{payload.crop_id}'. "
                f"Valid tokens: {sorted(CROP_MATRIX.keys())}."
            ),
        )

    try:
        # Deep-copy the cached reference dataframe inside the localized process context
        local_gdf = GLOBAL_WORKSPACE.copy()

        w = np.array(
            [payload.weights.ph, payload.weights.slope, payload.weights.water],
            dtype=np.float64,
        )

        # Crop-modulated fused matrix overlay (single vectorized pass)
        local_gdf["score"] = np.round(apply_crop_modulation(local_gdf, payload.crop_id, w), 4)
        local_gdf["crop_id"] = payload.crop_id

        # Format dataset response contract output stream straight into raw standard GeoJSON
        geojson_payload = local_gdf.to_json()
        return json.loads(geojson_payload)

    except HTTPException:
        raise
    except Exception as spatial_error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Matrix layer computation exception encountered: {str(spatial_error)}",
        )
