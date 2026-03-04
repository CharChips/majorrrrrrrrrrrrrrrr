import ee
import geemap
import os
import osmnx as ox
import rasterio
from rasterio import features as rio_features
import numpy as np
import json
from scipy.ndimage import distance_transform_edt
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

# --------------------------------------------------
# INITIALIZE
# --------------------------------------------------

ee.Initialize(project='geospatialproject-488418')

app = FastAPI()

os.makedirs("data", exist_ok=True)
os.makedirs("static", exist_ok=True)

# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def safe_norm(arr):
    """Normalize array to [0,1]. Returns zeros if max is 0."""
    mx = arr.max()
    if mx == 0 or np.isnan(mx):
        return np.zeros_like(arr, dtype=float)
    return arr.astype(float) / mx

# --------------------------------------------------
# CORE EV ENGINE FUNCTION
# --------------------------------------------------

def run_ev_analysis(place_name: str, geojson: dict = None):

    # ── Build Region of Interest ─────────────────────────────
    if geojson and geojson.get('features'):
        import geopandas as gpd
        from shapely.geometry import shape, MultiPoint
        from shapely.ops import unary_union

        # Use ALL pins to compute a bounding AOI
        geoms = [shape(f['geometry']) for f in geojson['features']]
        combined = unary_union(geoms)

        if combined.geom_type == 'Point':
            aoi_geom = combined.buffer(0.045).envelope   # ~5 km
        else:
            aoi_geom = combined.convex_hull.buffer(0.03).envelope

        boundary = gpd.GeoDataFrame({'geometry': [aoi_geom]}, crs="EPSG:4326")

    elif place_name and place_name.strip():
        try:
            boundary = ox.geocode_to_gdf(place_name)
            boundary = boundary.to_crs(epsg=4326)
        except Exception:
            # Fallback: point + buffer
            import geopandas as gpd
            from shapely.geometry import Point
            try:
                lat, lng = ox.geocode(place_name)
            except Exception as e:
                raise ValueError(f"Could not geocode '{place_name}': {e}")
            aoi_geom = Point(lng, lat).buffer(0.045).envelope
            boundary = gpd.GeoDataFrame({'geometry': [aoi_geom]}, crs="EPSG:4326")
    else:
        raise ValueError("place_name is required when no geojson is provided")

    roi_geom = boundary.geometry.iloc[0]
    bounds   = roi_geom.bounds                          # (minx, miny, maxx, maxy)
    roi      = ee.Geometry.Rectangle(list(bounds))

    # ── DEM + Slope via Google Earth Engine ──────────────────
    slope_path = "data/slope.tif"
    dem   = ee.Image("USGS/SRTMGL1_003").clip(roi)
    slope = ee.Terrain.slope(dem)

    geemap.ee_export_image(
        slope,
        filename=slope_path,
        scale=30,
        region=roi,
        file_per_band=False,
    )

    if not os.path.exists(slope_path):
        raise RuntimeError("Slope raster export failed — check GEE auth and region size")

    # ── Road Distance Raster ──────────────────────────────────
    G     = ox.graph_from_polygon(roi_geom, network_type='drive')
    roads = ox.graph_to_gdfs(G, nodes=False)

    with rasterio.open(slope_path) as src:
        raster_transform = src.transform
        raster_shape     = src.shape          # (height, width) — NOTE: not shadowing 'shape' import

    road_raster = rio_features.rasterize(
        [(geom, 1) for geom in roads.geometry],
        out_shape=raster_shape,
        transform=raster_transform,
        fill=0,
        dtype='uint8'
    )

    road_distance = distance_transform_edt(1 - road_raster)
    road_score    = 1.0 - safe_norm(road_distance)      # closer to road = higher score

    # ── Slope Score ───────────────────────────────────────────
    with rasterio.open(slope_path) as src:
        slope_data = src.read(1).astype(float)

    slope_data = np.clip(slope_data, 0, 90)             # clamp sensor noise
    slope_score = 1.0 - safe_norm(slope_data)           # flatter = higher score

    # ── Weighted Overlay ──────────────────────────────────────
    final_score = (0.6 * road_score) + (0.4 * slope_score)

    # ── Extract Top 10 Candidate Locations ───────────────────
    flat        = final_score.flatten()
    top_indices = np.argpartition(flat, -10)[-10:]
    rows, cols  = np.unravel_index(top_indices, final_score.shape)

    locations = []
    with rasterio.open(slope_path) as src:
        for r, c in zip(rows, cols):
            lon, lat_ = src.transform * (c, r)
            score     = final_score[r, c]
            locations.append({
                "latitude":  float(lat_),
                "longitude": float(lon),
                "score":     float(score)
            })

    # Sort by score descending
    locations.sort(key=lambda x: x["score"], reverse=True)
    return locations

# --------------------------------------------------
# API ROUTES
# --------------------------------------------------

from pydantic import BaseModel
from typing import Optional
from rag_pipeline import run_pipeline

_last_locations: list = []
_last_workflow:  dict = {}

class WorkflowRequest(BaseModel):
    query: str
    location: str = ""

class AnalysisRequest(BaseModel):
    place_name: str = ""
    geojson: Optional[dict] = None

# ── POST: full workflow generation ───────────────────────
@app.post("/generate-workflow")
def generate_workflow_post(request: WorkflowRequest):
    global _last_workflow
    try:
        workflow = run_pipeline(request.query, request.location)
        _last_workflow = workflow
        with open("generated_workflow.json", "w") as f:
            json.dump(workflow, f, indent=4)
        return JSONResponse(content={"status": "success", "workflow": workflow})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── GET: workflow ─────────────────────────────────────────
@app.get("/workflow")
def get_workflow():
    global _last_workflow
    if _last_workflow:
        return JSONResponse(content=_last_workflow)
    try:
        with open("generated_workflow.json", "r") as f:
            return JSONResponse(content=json.load(f))
    except FileNotFoundError:
        return JSONResponse(content={"error": "No workflow yet"}, status_code=404)

# ── POST: run analysis ────────────────────────────────────
@app.post("/run-analysis")
def analysis_post(request: AnalysisRequest):
    global _last_locations
    if not request.place_name and not request.geojson:
        raise HTTPException(status_code=422, detail="Provide place_name or geojson")
    try:
        locations = run_ev_analysis(request.place_name, request.geojson)
        _last_locations = locations
        return JSONResponse(content=locations)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── GET: last cached results ──────────────────────────────
@app.get("/locations")
def get_locations():
    return JSONResponse(content=_last_locations)

@app.get("/dem")
def get_dem():
    return FileResponse("data/slope.tif")

app.mount("/", StaticFiles(directory="static", html=True), name="static")
