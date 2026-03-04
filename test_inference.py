import requests
import json

base_url = "http://127.0.0.1:8000/generate-workflow"

print("--- Hospital Test ---")
res1 = requests.post(base_url, json={"query": "Where can I build a hospital?", "location": "Navi Mumbai"}).json()
print("Status:", res1.get("status", "error"))
print("Workflow keys:", res1.get("workflow", {}).keys())
print("Reasoning snippet:", str(res1.get("workflow", {}).get("reasoning", ""))[:200])
if "steps" in res1.get("workflow", {}):
    datasets = [s["inputs"] for s in res1["workflow"]["steps"] if "inputs" in s]
    print("Hospital Datasets Chosen:", datasets)

print("\n--- Solar Test ---")
res2 = requests.post(base_url, json={"query": "Identify suitable locations for a large solar farm", "location": "Pune"}).json()
print("Reasoning snippet:", str(res2.get("workflow", {}).get("reasoning", ""))[:200])
if "steps" in res2.get("workflow", {}):
    datasets = [s["inputs"] for s in res2["workflow"]["steps"] if "inputs" in s]
    print("Solar Datasets Chosen:", datasets)
