import requests

data = {
    "query": "New Delhi",
    "place_name": "New Delhi, India"
}

print("Pinging /get-layers...")
try:
    response = requests.post("http://localhost:8000/get-layers", json=data)
    print("Status code:", response.status_code)
    import json
    # Truncate content for debug view
    print("Response text:", response.text[:500])
except Exception as e:
    print("Error:", e)
