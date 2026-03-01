from fastapi.testclient import TestClient
from app import app
import json

client = TestClient(app)

geojson = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[72.97, 19.04], [73.05, 19.04], [73.05, 19.10], [72.97, 19.10], [72.97, 19.04]]]
            }
        }
    ]
}

response = client.post("/run-analysis", json={"place_name": "Custom AOI Polygon", "geojson": geojson})
print(response.status_code)
print(response.text)
