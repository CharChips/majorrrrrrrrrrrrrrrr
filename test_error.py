import sys
import traceback

try:
    from app import run_ev_analysis
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Point",
                    "coordinates": [73.02, 19.03]
                }
            }
        ]
    }
    locations = run_ev_analysis("Custom AOI Polygon", geojson=geojson)
    print("Success! Found", len(locations), "locations.")
except Exception as e:
    traceback.print_exc()
