import os
import numpy as np
import geopandas as gpd
from shapely.geometry import box
from abc import ABC, abstractmethod
class IngestionStrategy(ABC):
    """Abstract baseline class establishing data ingestion standards."""
    @abstractmethod
    def load_workspace(self) -> gpd.GeoDataFrame:
        pass
class MockDataStrategy(IngestionStrategy):
    """Generates an explicit, deterministic vector matrix replicating the Western Antalya Corridor."""
    def load_workspace(self) -> gpd.GeoDataFrame:
        # Geographic bounds matching envelope bounds exactly
        min_lon, max_lon = 29.30, 30.85
        min_lat, max_lat = 36.18, 37.12

        cols, rows = 22, 14
        lon_bins = np.linspace(min_lon, max_lon, cols + 1)
        lat_bins = np.linspace(min_lat, max_lat, rows + 1)

        polygons = []
        cell_ids = []
        counter = 0

        for i in range(cols):
            for j in range(rows):
                polygons.append(box(lon_bins[i], lat_bins[j], lon_bins[i+1], lat_bins[j+1]))
                cell_ids.append(f"WAC-RRCC-{counter:03d}")
                counter += 1

        # Instantiating clean seeded generation matching hexadecimal stream signature
        rng = np.random.default_rng(0xA6D5)
        data = {
            "cell_id": cell_ids,
            "x1_ph": rng.uniform(0.1, 1.0, len(polygons)),
            "x2_slope": rng.uniform(0.1, 1.0, len(polygons)),
            "x3_water": rng.uniform(0.1, 1.0, len(polygons)),
            "geometry": polygons
        }
        return gpd.GeoDataFrame(data, crs="EPSG:4326")
class FileIngestionStrategy(IngestionStrategy):
    """Ingests enterprise geospatial vector files under EPSG:4326 standard projection."""
    def __init__(self, file_path: str):
        self.file_path = file_path
    def load_workspace(self) -> gpd.GeoDataFrame:
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Target GIS workspace resource missing at: {self.file_path}")
        gdf = gpd.read_file(self.file_path)
        return gdf.to_crs("EPSG:4326")
class IngestionEngine:
    """Orchestrates ingestion mode context loading routines dynamically."""
    @staticmethod
    def get_data() -> gpd.GeoDataFrame:
        mode = os.getenv("AGRI_DSS_MODE", "MOCK")
        if mode == "PRODUCTION":
            path = os.getenv("AGRI_DSS_DATA_PATH", "backend/data/antalya_corridor.gpkg")
            return FileIngestionStrategy(path).load_workspace()
        return MockDataStrategy().load_workspace()
