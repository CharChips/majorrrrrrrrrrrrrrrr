import ee
import os
from dotenv import load_dotenv

print("Loading .env...")
load_dotenv()
project_id = os.getenv("GEE_PROJECT_ID", "llm-gis-project")
print(f"Project ID: {project_id}")

print("Initializing Earth Engine (Auto-detect project)...")
try:
    ee.Initialize()
    print("Initialization successful!")
    # Try a simple call
    print("Testing call: Get info for SRTM...")
    img = ee.Image("USGS/SRTMGL1_003")
    print(img.getInfo())
except Exception as e:
    print(f"Initialization FAILED: {e}")
