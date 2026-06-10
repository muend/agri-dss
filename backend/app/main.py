import json
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
from app.schemas.contracts import OptimizationRequest
from app.core.ingestion import IngestionEngine
# Global in-memory cache registry container
GLOBAL_WORKSPACE = None
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-caches spatial geometry registries inside system memory at bootstrap runtime."""
    global GLOBAL_WORKSPACE
    loop = asyncio.get_running_loop()
    # Execute non-blocking ingestion call over the executor threadpool pool
    GLOBAL_WORKSPACE = await loop.run_in_executor(None, IngestionEngine.get_data)
    yield
    GLOBAL_WORKSPACE = None
app = FastAPI(
    title="Agri-DSS Matrix Core Engine",
    description="High-performance vectorized overlay router for regional planning analytics.",
    version="0.3.5",
    lifespan=lifespan
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Expand bounding parameters safely inside production routing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/api/health", status_code=status.HTTP_200_OK)
async def system_health_census():
    if GLOBAL_WORKSPACE is None:
        raise HTTPException(status_code=503, detail="Spatial matrix repository allocation uninitialized.")
    return {
        "status": "synchronized",
        "cached_cell_count": len(GLOBAL_WORKSPACE),
        "crs_signature": str(GLOBAL_WORKSPACE.crs),
        "spatial_bounding_box": GLOBAL_WORKSPACE.total_bounds.tolist()
    }
@app.post("/api/optimize", status_code=status.HTTP_200_OK)
async def resolve_spatial_suitability(payload: OptimizationRequest):
    """Executes high-speed matrix overlay computation in O(N) using vector dot product operations."""
    if GLOBAL_WORKSPACE is None:
        raise HTTPException(status_code=503, detail="Analytical core memory registry allocation offline.")

    try:
        # Deep-copy the cached reference dataframe inside the localized process context
        local_gdf = GLOBAL_WORKSPACE.copy()

        w_ph = payload.weights.ph
        w_slope = payload.weights.slope
        w_water = payload.weights.water

        # Execute vectorized matrix math directly inside C-level arrays via NumPy array slicing
        local_gdf["score"] = (local_gdf["x1_ph"] * w_ph) + (local_gdf["x2_slope"] * w_slope) + (local_gdf["x3_water"] * w_water)
        local_gdf["score"] = local_gdf["score"].round(4)

        # Format dataset response contract output stream straight into raw standard GeoJSON
        geojson_payload = local_gdf.to_json()
        return json.loads(geojson_payload)

    except Exception as spatial_error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Matrix layer computation exception encountered: {str(spatial_error)}"
        )
