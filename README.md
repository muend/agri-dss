# Agri-DSS: Spatial Decision Support System for Agricultural Suitability Analysis in the Western Antalya Corridor

**Production domain:** `tarimsalkoridor.online` · **Envelope:** 36.18N–37.12N / 29.30E–30.85E · **CRS:** EPSG:4326 (WGS-84)

---

## 1. Conceptual Abstract

Agri-DSS automates **vectorized multi-criteria overlay analysis** for regional agricultural planning inside the Western Antalya Corridor bounding envelope (36.18N–37.12N, 29.30E–30.85E). The core spatial engineering problem: given a fishnet partition of the corridor into N polygonal cells, each carrying standardized criterion scores for soil pH, topographic slope, and hydrographic proximity, compute a per-cell **Spatial Suitability Index** under an operator-controlled Analytical Hierarchy Process (AHP) weight vector — at interactive latency, for arbitrary weight configurations, differentiated per crop registry token.

The system rejects per-cell Python iteration categorically. All scoring executes as fused NumPy matrix arithmetic over C-level arrays, holding the evaluation path at **O(N)** with vectorized constant factors.

> **Demonstration mode notice.** The system currently ships with a **deterministic mock geospatial grid** (22 × 14 cells, seeded `np.random.default_rng(0xA6D5)`) for demonstration purposes. Production file ingestion (`.gpkg` / `.geojson`) is fully decoupled behind the Strategy pattern and activates via `AGRI_DSS_MODE=PRODUCTION` without any code modification.

---

## 2. System Architecture & Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│  CLIENT — React 19 + Vite (tarimsalkoridor.online, GitHub Pages)        │
│                                                                          │
│  ┌────────────────────────┐        ┌──────────────────────────────────┐ │
│  │ ControlPanel.jsx (30%) │        │ MapCanvas.jsx (70%)              │ │
│  │  crop registry buttons │        │  Leaflet / CARTO dark basemap    │ │
│  │  AHP sliders w1 w2 w3  │        │  GeoJSON suitability overlay     │ │
│  │  telemetry monitor     │        │  4-corner monospaced HUD         │ │
│  └───────────┬────────────┘        └────────────────▲─────────────────┘ │
│              │ dispatch(UPDATE_WEIGHTS)             │ geoData            │
│  ┌───────────▼─────────────────────────────────────┴─────────────────┐ │
│  │ DSSContext.jsx — reducer state core                                │ │
│  │  · RELATIVE SCALING NORMALIZATION: Σwᵢ = 1.0 enforced per tick     │ │
│  │  · composes POST payload {crop_id, weights}                        │ │
│  └───────────────────────────────┬────────────────────────────────────┘ │
└──────────────────────────────────┼──────────────────────────────────────┘
                                   │  HTTPS POST /api/optimize (JSON)
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  ENGINE — FastAPI / Uvicorn (backend/)                                   │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ schemas/contracts.py — Pydantic v2 gate                            │ │
│  │  · field bounds 0.0 ≤ wᵢ ≤ 1.0                                     │ │
│  │  · field_validator (ValidationInfo context): Σwᵢ = 1.0 or 422      │ │
│  └───────────────────────────────┬────────────────────────────────────┘ │
│                                  ▼                                       │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ main.py — crop-modulated vectorized overlay                        │ │
│  │  · CROP_MATRIX profile lookup (CRP-01 / CRP-02 / CRP-03)           │ │
│  │  · X' = f(X, crop_id)   (power-law reward, penalty, hard mask)     │ │
│  │  · S  = X' @ Wᵀ          (single fused N×3 · 3 dot product)        │ │
│  │  · thread-isolated copy of GLOBAL_WORKSPACE per request            │ │
│  └───────────────────────────────▲────────────────────────────────────┘ │
│                                  │ GeoDataFrame (cached at startup)      │
│  ┌───────────────────────────────┴────────────────────────────────────┐ │
│  │ core/ingestion.py — Strategy pattern                               │ │
│  │                                                                    │ │
│  │   IngestionStrategy (ABC)                                          │ │
│  │        ├── MockDataStrategy      AGRI_DSS_MODE=MOCK (default)      │ │
│  │        │     22×14 seeded fishnet, EPSG:4326                       │ │
│  │        └── FileIngestionStrategy AGRI_DSS_MODE=PRODUCTION          │ │
│  │              .gpkg/.geojson via AGRI_DSS_DATA_PATH, CRS-normalized │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  Response: GeoJSON FeatureCollection (N features, per-cell score)        │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
              Leaflet GeoJSON layer re-render + telemetry recompute
```

**Lifecycle.** At startup the FastAPI lifespan hook executes `IngestionEngine.get_data()` on the executor threadpool and pins the resulting GeoDataFrame in process memory (`GLOBAL_WORKSPACE`). Every `/api/optimize` call operates on a copy of this cached frame: the global workspace is never mutated, so concurrent requests with divergent weight vectors are isolated by construction.

---

## 3. Mathematical Formulations

### 3.1 AHP Constraint Layer

The operator supplies the priority vector **W** = (w₁, w₂, w₃) for the factors soil pH, slope, and water proximity. Two constraints are enforced at the Pydantic boundary:

```
0.0 ≤ wᵢ ≤ 1.0           ∀ i ∈ {1, 2, 3}        (field bounds)
w₁ + w₂ + w₃ = 1.0       (abs_tol = 1e-5)        (priority condition)
```

Violation returns HTTP 422 before any spatial computation is scheduled.

**Client-side synchronization.** The React reducer makes 422s structurally unreachable from slider motion. When slider A moves to value v_A, the residual mass is redistributed over the remaining pair proportionally to its current ratio:

```
r        = 1 − v_A
v_B      = r · w_B / (w_B + w_C)        (equal split if w_B + w_C = 0)
v_C      = 1 − v_A − v_B                 (exact residual closure)
```

The final member is assigned as an exact residual rather than a scaled product, so the vector closes to 1.0 without floating-point drift accumulation across interactions.

### 3.2 Crop-Modulated Vectorized Overlay

Let **X** be the N×3 criteria matrix `[x1_ph | x2_slope | x3_water]`. The engine computes:

```
S_c = f(X, crop_id) · Wᵀ
```

where `f` is the crop modulation profile applied column-wise before the fused dot product:

| Token | Crop | Modulation `f` | Ecological rationale |
|---|---|---|---|
| CRP-01 | Olive | `x1 ← x1^0.60`, `x2 ← x2^0.70` | Concave power-law reward: olives thrive on mild slopes and alkaline chemistry, so strong pH/slope cells are exponentially lifted. |
| CRP-02 | Citrus | `x3 ← 0.2·x3 if x3 < 0.4` | Severe hydrographic penalty: citrus is irrigation-dependent; cells far from water are crushed. |
| CRP-03 | Greenhouse | `S ← 0 where (1 − x2) > 0.35` | Absolute flatness constraint: terrain steepness above the ceiling hard-zeroes the fused score (binary mask). |

The complete evaluation is three NumPy column transforms, one `np.column_stack`, and one `(N×3) @ (3,)` dot product — no Python-level loop touches cell data at any point. Scores are clipped to [0, 1] and rounded to 4 decimals.

### 3.3 Telemetry Aggregates

Computed client-side from the returned FeatureCollection:

```
mean  = (Σ Sᵢ) / N
max   = max(Sᵢ)
prime = |{ i : Sᵢ ≥ 0.75 }| / N · 100%     (prime-land KPI, emerald threshold)
```

---

## 4. Installation Matrix

Prerequisites: Node.js ≥ 20, Python ≥ 3.11, npm ≥ 10.

### 4.1 Frontend — Node / Vite ecosystem

```bash
# [F1] Clone and enter the repository root
git clone <repository-url> agri-dss
cd agri-dss

# [F2] Install the pinned Node dependency graph
npm install

# [F3] Launch the Vite development server (http://localhost:5173)
npm run dev

# [F4] Produce the production bundle (dist/ — includes CNAME for
#      tarimsalkoridor.online custom-domain routing on GitHub Pages)
npm run build
```

### 4.2 Backend — sandboxed Python virtual environment

```bash
# [B1] Enter the analytical engine directory
cd backend

# [B2] Create the isolated virtual environment
python -m venv .venv

# [B3] Activate it
#      Windows (PowerShell):
.venv\Scripts\Activate.ps1
#      Linux / macOS:
source .venv/bin/activate

# [B4] Install the pinned deployment manifest
pip install -r requirements.txt

# [B5] Launch the engine (http://localhost:8000)
uvicorn app.main:app --host 0.0.0.0 --port 8000

# [B6] (Optional) Switch to production file ingestion
#      Windows (PowerShell):
$env:AGRI_DSS_MODE = "PRODUCTION"
$env:AGRI_DSS_DATA_PATH = "C:\data\antalya_corridor.gpkg"
#      Linux / macOS:
export AGRI_DSS_MODE=PRODUCTION
export AGRI_DSS_DATA_PATH=/data/antalya_corridor.gpkg
```

Interactive API documentation is served at `http://localhost:8000/docs` (OpenAPI / Swagger UI).

---

## 5. API Contract

### 5.1 `GET /api/health`

```json
{
  "status": "synchronized",
  "cached_cell_count": 308,
  "crs_signature": "EPSG:4326",
  "spatial_bounding_box": [29.3, 36.18, 30.85, 37.12],
  "crop_registry": {
    "CRP-01": "Olea Europaea (Olive Matrix)",
    "CRP-02": "Citrus Sinensis (Orchard Grid)",
    "CRP-03": "Solanum Lycopersicum (Greenhouse)"
  }
}
```

### 5.2 `POST /api/optimize` — request

```json
{
  "crop_id": "CRP-02",
  "weights": {
    "ph": 0.40,
    "slope": 0.35,
    "water": 0.25
  }
}
```

### 5.3 `POST /api/optimize` — response (abbreviated to one feature)

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "id": "0",
      "type": "Feature",
      "properties": {
        "cell_id": "WAC-RRCC-000",
        "x1_ph": 0.7204,
        "x2_slope": 0.5381,
        "x3_water": 0.2982,
        "score": 0.4914,
        "crop_id": "CRP-02"
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[29.3, 36.18], [29.3704, 36.18], [29.3704, 36.2471], [29.3, 36.2471], [29.3, 36.18]]]
      }
    }
  ]
}
```

### 5.4 Constraint rejection (HTTP 422)

Request with `{"ph": 0.5, "slope": 0.4, "water": 0.3}` (Σ = 1.2):

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "weights", "water"],
      "msg": "Value error, Analytical priority constraints must sum up to exactly 1.0. Got: 1.2"
    }
  ]
}
```

Unknown registry token (`"crop_id": "CRP-99"`):

```json
{
  "detail": "Unknown crop registry token 'CRP-99'. Valid tokens: ['CRP-01', 'CRP-02', 'CRP-03']."
}
```

---

## 6. Visual Assets Blueprint

Dashboard composition — strict high-modernist Swiss / brutalist GIS aesthetic. Monochrome ink-and-paper palette; **Emerald #00E676** is reserved exclusively for validated spatial bounds, prime suitability matrices (S ≥ 0.75), and the master processing trigger.

```
┌──────────────────────────────┬───────────────────────────────────────────┐
│ CONTROL HUD PANEL (30%)      │ MAP CANVAS (70%)                          │
│ paper #F9F9F9 / ink #0A0A0A  │ ink #0A0A0A                               │
│                              │                                           │
│ AGRI-DSS                     │ ┌SYS.LOC HUD┐            ┌EPSG:4326 HUD┐ │
│ SPATIAL SUITABILITY MATRIX   │                                           │
│ ──────────────────────────── │      CARTO Dark Matter basemap            │
│ ANALYSIS DOMAIN MODEL        │                                           │
│  [CRP-01] Olea Europaea      │      GeoJSON suitability fishnet:         │
│  [CRP-02] Citrus Sinensis    │       · S ≥ 0.75 → #00E676 fill 0.65,     │
│  [CRP-03] Solanum Lycop.     │         solid 1.5px emerald stroke        │
│                              │       · S < 0.75 → #262626 graduated      │
│ AHP INPUTS (Σ=1.0)           │         alpha ramp, 0.5px dashed #404040  │
│  w1 · SOIL PH      ▮──────   │                                           │
│  w2 · TOPO SLOPE   ───▮───   │                                           │
│  w3 · HYDRO PROX   ─────▮─   │                                           │
│  (rectangular ink thumbs,    │                                           │
│   emerald on hover)          │                                           │
│                              │                                           │
│ TELEMETRY MONITOR            │                                           │
│  MATRIX.MEAN   MATRIX.MAX    │                                           │
│  CELLS.CACHED  PRIME.ZONE    │                                           │
│  (mono font; PRIME.ZONE in   │                                           │
│   emerald-on-ink when > 0)   │                                           │
│                              │                                           │
│ ┌──────────────────────────┐ │ ┌Basemap HUD┐        ┌● ENGINE ONLINE┐   │
│ │ EXECUTE REGIONAL OPTIMIZ.│ │  (bottom-left)        (emerald, bottom-   │
│ │ (emerald master trigger; │ │                        right)             │
│ │  ink/emerald inversion   │ │                                           │
│ │  on hover)               │ │                                           │
│ └──────────────────────────┘ │                                           │
└──────────────────────────────┴───────────────────────────────────────────┘
```

Component inventory: `ControlPanel.jsx` renders the masthead, the three-token crop registry, the constraint-locked AHP slider stack with live monospaced numeric readouts, the four-cell telemetry monitor, and the master trigger. `MapCanvas.jsx` renders the dark-room Leaflet container with four corner-pinned monospaced HUD chips, the score-ramped GeoJSON overlay, and a `BoundsController` child that programmatically fits the camera to the returned FeatureCollection. Typography: Inter (display sans) and JetBrains Mono (telemetry/metadata) throughout; all borders 1px; zero decorative imagery.

---

## 7. Repository Layout

```
agri-dss/
├── README.md                      ← this document
├── package.json                   React 19 · react-leaflet 5 · Vite 8 · Tailwind 3
├── vite.config.js
├── tailwind.config.js             ink/paper monochrome + emeraldIgnition token
├── postcss.config.js
├── index.html                     Inter + JetBrains Mono stacks
├── public/
│   └── CNAME                      tarimsalkoridor.online
├── src/
│   ├── main.jsx
│   ├── App.jsx                    30/70 flex split shell
│   ├── index.css                  Tailwind layers + slider/Leaflet overrides
│   ├── context/
│   │   └── DSSContext.jsx         constraint-enforced reducer state core
│   └── components/
│       ├── ControlPanel.jsx       criteria console
│       └── MapCanvas.jsx          geospatial vector room
└── backend/
    ├── requirements.txt           pinned deployment manifest
    └── app/
        ├── __init__.py
        ├── main.py                crop-modulated vectorized overlay engine
        ├── core/
        │   ├── __init__.py
        │   └── ingestion.py       Strategy-pattern spatial ingestion
        └── schemas/
            ├── __init__.py
            └── contracts.py       Pydantic v2 AHP validation gate
```

---

## 8. License & Attribution

Basemap tiles © [CARTO](https://carto.com/attributions) / © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors. Spatial computation stack: NumPy, GeoPandas, Shapely, FastAPI, Pydantic. Client stack: React, react-leaflet, Leaflet, Tailwind CSS, Vite.
