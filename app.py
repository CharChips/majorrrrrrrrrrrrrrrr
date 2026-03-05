import ee
import geemap
import os
import requests
import osmnx as ox
import rasterio
from rasterio import features
import numpy as np
from scipy.ndimage import distance_transform_edt
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import json
import re
import logging

# Configure logging to file
logging.basicConfig(
    filename='server_debug.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("server")

from openrouter_client import generate_workflow, generate_osm_tags, generate_feature_reasoning
from rag_pipeline import run_pipeline

# --------------------------------------------------
# INITIALIZE
# --------------------------------------------------

# Load from .env if possible
from dotenv import load_dotenv
load_dotenv()
GEE_PROJECT = os.getenv("GEE_PROJECT_ID", "llm-gis-project")
logger.info(f"Initializing Earth Engine with project: {GEE_PROJECT}")
try:
    ee.Initialize(project=GEE_PROJECT)
    logger.info("EE Initialize successful")
except Exception as e:
    logger.error(f"EE Initialize FAILED: {e}")

app = FastAPI()

os.makedirs("data", exist_ok=True)
os.makedirs("static", exist_ok=True)

def get_safe_filename(name):
    return re.sub(r'[^a-zA-Z0-9]', '_', name.lower()).strip('_')

class WorkflowRequest(BaseModel):
    query: str
    location: str = ""
    previous_workflow: dict = None
    feedback: str = None

class AnalysisRequest(BaseModel):
    query: str = ""
    place_name: str
    geojson: dict = None
    top_n: int = 10
    weights: dict = None

class DeepAnalysisRequest(BaseModel):
    query: str
    lat: float
    lon: float
    location_name: str = "Unknown Location"

@app.post("/generate-workflow")
def generate_workflow_api(request: WorkflowRequest):
    workflow = run_pipeline(
        user_query=request.query, 
        location=request.location,
        previous_workflow=request.previous_workflow,
        feedback=request.feedback
    )
    with open("generated_workflow.json", "w") as f:
        json.dump(workflow, f, indent=4)
    return JSONResponse(content={"status": "success", "message": "Workflow generated.", "workflow": workflow})

@app.post("/run-analysis")
def analysis(request: AnalysisRequest):
    # Determine boundary
    if request.geojson and 'features' in request.geojson and len(request.geojson['features']) > 0:
        import geopandas as gpd
        from shapely.geometry import shape
        geom = shape(request.geojson['features'][0]['geometry'])
        if geom.geom_type in ['Point', 'LineString']:
            geom = geom.buffer(0.05).envelope
        boundary = gpd.GeoDataFrame({'geometry': [geom]}, crs="EPSG:4326")
    else:
        try:
            boundary = ox.geocode_to_gdf(request.place_name)
            boundary = boundary.to_crs(epsg=4326)
        except Exception as e:
            try:
                import geopandas as gpd
                from shapely.geometry import Point
                lat, lng = ox.geocode(request.place_name)
                geom = Point(lng, lat).buffer(0.05).envelope
                boundary = gpd.GeoDataFrame({'geometry': [geom]}, crs="EPSG:4326")
            except Exception as inner_e:
                print(f"Geocoding failed for {request.place_name}: {inner_e}")
                return JSONResponse(status_code=404, content={"error": "Location not found."})

    roi_geom = boundary.geometry.iloc[0]
    bounds = roi_geom.bounds
    roi = ee.Geometry.Rectangle(bounds)

    place_slug = get_safe_filename(request.place_name)

    # 1. Fetch Elevation and Export Slope TIFF (User wants this file)
    slope_path = f"data/{place_slug}_slope.tif"
    if not os.path.exists(slope_path):
        print(f"Generating new slope TIFF for {request.place_name}...")
        dem = ee.Image("USGS/SRTMGL1_003").clip(roi)
        slope = ee.Terrain.slope(dem)
        geemap.ee_export_image(slope, filename=slope_path, scale=30, region=roi)
    else:
        print(f"Using existing slope TIFF for {request.place_name}.")

    # 2. Raster Suitability Math
    # Weights from request
    w_road = request.weights.get("road_dist", 0.6) if request.weights else 0.6
    w_slope = request.weights.get("slope", 0.4) if request.weights else 0.4

    # Fetch roads
    try:
        G = ox.graph_from_polygon(roi_geom, network_type='drive')
        roads = ox.graph_to_gdfs(G, nodes=False)
    except:
        return JSONResponse(content={"type": "FeatureCollection", "features": []})

    with rasterio.open(slope_path) as src:
        transform = src.transform
        shape = src.shape
        slope_data = src.read(1)

    road_raster = features.rasterize(
        [(geom, 1) for geom in roads.geometry],
        out_shape=shape, transform=transform, fill=0, dtype='uint8'
    )

    road_distance = distance_transform_edt(1 - road_raster)
    road_score = 1 - (road_distance / (road_distance.max() + 1e-6))
    slope_score = 1 - (slope_data / (slope_data.max() + 1e-6))

    final_score = (w_road * road_score) + (w_slope * slope_score)

    # 3. Extract Top Locations
    top_n = request.top_n or 10
    flat = final_score.flatten()
    top_indices = np.argpartition(flat, -top_n)[-top_n:]
    rows, cols = np.unravel_index(top_indices, final_score.shape)

    geojson_features = []
    for r, c in zip(rows, cols):
        lon, lat = transform * (c, r)
        score = final_score[r, c]
        
        # Simple reasoning for suitability
        reason = f"Suitability score: {score:.2f}. "
        reason += "Good road access. " if road_score[r,c] > 0.7 else ""
        reason += "Optimal slope." if slope_score[r,c] > 0.7 else ""

        feature = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [float(lon), float(lat)]},
            "properties": {
                "name": f"Optimal Site ({score:.2f})",
                "reason": reason,
                "score": float(score),
                "centroid": [float(lat), float(lon)]
            }
        }
        geojson_features.append(feature)

    return JSONResponse(content={"type": "FeatureCollection", "features": geojson_features})

@app.post("/get-layers")
def get_layers(request: AnalysisRequest, background_tasks: BackgroundTasks):
    logger.info(f"Received request for /get-layers: {request.place_name}")
    # Determine boundary
    if request.geojson and 'features' in request.geojson and len(request.geojson['features']) > 0:
        logger.info("Using provided GeoJSON for boundary")
        import geopandas as gpd
        from shapely.geometry import shape
        geom = shape(request.geojson['features'][0]['geometry'])
        if geom.geom_type in ['Point', 'LineString']:
            geom = geom.buffer(0.05).envelope
        boundary = gpd.GeoDataFrame({'geometry': [geom]}, crs="EPSG:4326")
    else:
        logger.info(f"Geocoding location: {request.place_name}")
        try:
            boundary = ox.geocode_to_gdf(request.place_name)
            boundary = boundary.to_crs(epsg=4326)
            logger.info("Geocoding to GDF successful")
        except Exception as e:
            logger.warning(f"Geocoding to GDF failed, trying fallback: {e}")
            try:
                import geopandas as gpd
                from shapely.geometry import Point
                lat, lng = ox.geocode(request.place_name)
                geom = Point(lng, lat).buffer(0.05).envelope
                boundary = gpd.GeoDataFrame({'geometry': [geom]}, crs="EPSG:4326")
                logger.info("Fallback geocoding successful")
            except Exception as inner_e:
                logger.error(f"All geocoding failed for {request.place_name}: {inner_e}")
                return JSONResponse(status_code=404, content={"error": "Location not found."})

    roi_geom = boundary.geometry.iloc[0]
    bounds = roi_geom.bounds
    roi = ee.Geometry.Rectangle(bounds)
    
    place_slug = get_safe_filename(request.place_name)
    logger.info(f"Place slug: {place_slug}")
    
    requested_layers = request.weights.get("layers", ["population", "dem", "vegetation", "land_use"]) if request.weights else ["population", "dem", "vegetation", "land_use"]
    logger.info(f"Requested layers: {requested_layers}")
    
    response = {}

    # 1. Population (WorldPop)
    if "population" in requested_layers:
        logger.info("Fetching Population layer MapID")
        try:
            pop = ee.ImageCollection("WorldPop/GP/100m/pop") \
                    .filterBounds(roi) \
                    .map(lambda img: img.clip(roi)) \
                    .mean()
            pop_id = pop.getMapId({"min": 0, "max": 50, "palette": ['24126c', '1fff4f', 'd4ff50']})
            response["population"] = pop_id['tile_fetcher'].url_format
            logger.info("Population MapID success")
            
            pop_path = f"data/{place_slug}_population.tif"
            if not os.path.exists(pop_path):
                logger.info(f"Adding background task: Export Population to {pop_path}")
                background_tasks.add_task(geemap.ee_export_image, pop, filename=pop_path, scale=100, region=roi)
        except Exception as e:
            logger.error(f"Population layer error: {e}")

    # 2. DEM / Elevation / Slope
    if "dem" in requested_layers:
        logger.info("Fetching DEM layer MapID")
        try:
            dem = ee.Image("USGS/SRTMGL1_003").clip(roi)
            dem_id = dem.getMapId({"min": 0, "max": 3000, "palette": ['006600', '002200', 'fff700', 'ab7634', 'c4d0ff', 'ffffff']})
            response["dem"] = dem_id['tile_fetcher'].url_format
            logger.info("DEM MapID success")
            
            dem_path = f"data/{place_slug}_dem.tif"
            if not os.path.exists(dem_path):
                logger.info(f"Adding background task: Export DEM to {dem_path}")
                background_tasks.add_task(geemap.ee_export_image, dem, filename=dem_path, scale=30, region=roi)
                
            slope_path = f"data/{place_slug}_slope.tif"
            if not os.path.exists(slope_path):
                logger.info(f"Adding background task: Export Slope to {slope_path}")
                slope = ee.Terrain.slope(dem)
                background_tasks.add_task(geemap.ee_export_image, slope, filename=slope_path, scale=30, region=roi)
        except Exception as e:
            logger.error(f"DEM/Slope layer error: {e}")

    # 3. Vegetation (NDVI)
    if "vegetation" in requested_layers:
        ndvi = ee.ImageCollection("MODIS/061/MOD13Q1") \
                 .filterBounds(roi) \
                 .map(lambda img: img.clip(roi)) \
                 .mean().select('NDVI')
        ndvi_id = ndvi.getMapId({"min": 0, "max": 8000, "palette": ['FFFFFF', 'CE7E45', 'DF923D', 'F1B555', 'FCD163', '99B718', '74A901', '66A000', '529400', '3E8601', '207401', '056201', '004C00', '023B01', '012E01', '011D01', '011301']})
        response["vegetation"] = ndvi_id['tile_fetcher'].url_format
        # Export in background if missing
        ndvi_path = f"data/{place_slug}_vegetation.tif"
        if not os.path.exists(ndvi_path):
            background_tasks.add_task(geemap.ee_export_image, ndvi, filename=ndvi_path, scale=250, region=roi)

    # 4. Land Use (ESA WorldCover)
    if "land_use" in requested_layers:
        land_use = ee.ImageCollection("ESA/WorldCover/v100").first().clip(roi)
        lu_id = land_use.getMapId({"bands": ['Map']})
        response["land_use"] = lu_id['tile_fetcher'].url_format
        # Export in background if missing
        lu_path = f"data/{place_slug}_land_use.tif"
        if not os.path.exists(lu_path):
            background_tasks.add_task(geemap.ee_export_image, land_use, filename=lu_path, scale=10, region=roi)

    return JSONResponse(content=response)


def fetch_news_articles(query: str, location_name: str, max_results: int = 8):
    """Fetch real news articles using DuckDuckGo News — no API key required."""
    try:
        from duckduckgo_search import DDGS
        search_query = f"{query} {location_name} real estate development site"
        results = []
        with DDGS() as ddgs:
            news_items = list(ddgs.news(search_query, region="in-en", max_results=max_results))
        
        for item in news_items:
            results.append({
                "title": item.get("title", ""),
                "snippet": item.get("body", ""),
                "source": item.get("source", "Unknown"),
                "url": item.get("url", ""),
                "date": item.get("date", ""),
                "tag": "news"
            })

        # Also try a social/sentiment search
        social_query = f"{location_name} {query} opinion OR residents OR protest OR trending"
        with DDGS() as ddgs:
            social_items = list(ddgs.news(social_query, region="in-en", max_results=4))
        
        for item in social_items:
            results.append({
                "title": item.get("title", ""),
                "snippet": item.get("body", ""),
                "source": item.get("source", "Unknown"),
                "url": item.get("url", ""),
                "date": item.get("date", ""),
                "tag": "social"
            })

        return results
    except Exception as e:
        print(f"News fetch error: {e}")
        return []


@app.post("/deep-analysis")
def deep_analysis(request: DeepAnalysisRequest):
    # 1. Resolve location name from coordinates if not provided
    location_name = request.location_name
    if location_name == "Unknown Location":
        try:
            rev_url = f"https://nominatim.openstreetmap.org/reverse?lat={request.lat}&lon={request.lon}&format=json"
            rev = requests.get(rev_url, headers={"User-Agent": "GISSiteExpert/1.0"}, timeout=5).json()
            addr = rev.get("address", {})
            location_name = (
                addr.get("suburb") or addr.get("neighbourhood") or
                addr.get("city_district") or addr.get("city") or
                addr.get("town") or addr.get("village") or location_name
            )
        except:
            pass

    # 2. Get Spatial Stats for the Point using Earth Engine
    point = ee.Geometry.Point([request.lon, request.lat])
    
    pop = ee.ImageCollection("WorldPop/GP/100m/pop").mean()
    pop_val = pop.reduceRegion(reducer=ee.Reducer.mean(), geometry=point, scale=100).get('population').getInfo()
    
    dem = ee.Image("USGS/SRTMGL1_003")
    slope = ee.Terrain.slope(dem)
    slope_val = slope.reduceRegion(reducer=ee.Reducer.mean(), geometry=point, scale=30).get('slope').getInfo()
    
    ndvi = ee.ImageCollection("MODIS/061/MOD13Q1").mean().select('NDVI')
    ndvi_val = ndvi.reduceRegion(reducer=ee.Reducer.mean(), geometry=point, scale=250).get('NDVI').getInfo()
    
    spatial_stats = {
        "population_density": pop_val,
        "slope_degrees": slope_val,
        "vegetation_index": ndvi_val,
        "latitude": request.lat,
        "longitude": request.lon
    }

    # 3. Fetch Real News
    articles = fetch_news_articles(request.query, location_name)
    
    # Build a text summary of news for the LLM
    if articles:
        news_lines = [f"- {a['title']} ({a['source']})" for a in articles[:6]]
        market_context = f"Recent news about {location_name}:\n" + "\n".join(news_lines)
    else:
        market_context = f"No recent news found specifically for {location_name}."

    # 4. Generate LLM Report
    from openrouter_client import generate_deep_analysis
    report = generate_deep_analysis(request.query, spatial_stats, market_context)

    return JSONResponse(content={
        "status": "success",
        "spatial_stats": spatial_stats,
        "location_name": location_name,
        "report": report,
        "news_articles": articles
    })



app.mount("/", StaticFiles(directory="static", html=True), name="static")