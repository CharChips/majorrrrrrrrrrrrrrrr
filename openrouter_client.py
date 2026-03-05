import requests
import json
import os

GROQ_API_KEY = ""

def generate_workflow(user_query, context, system_instructions):

    user_prompt = f"""
User Query:
{user_query}

Available Knowledge:
{context}

Generate a workflow JSON strictly following the schema.
Do not exceed 10 steps.
Do not repeat tools unnecessarily.
Return ONLY valid JSON.
"""

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "groq/compound-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": system_instructions
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                "temperature": 0.2,
                # "max_tokens": 700
                "max_tokens": 900
                
            },
            timeout=60
        )

        data = response.json()

        print("\nFULL GROQ RESPONSE:\n", data)

        if "error" in data:
            return json.dumps({"error": data["error"]})

        if "choices" not in data:
            return json.dumps({"error": "Invalid response format"})

        return data["choices"][0]["message"]["content"]

    except Exception as e:
        return json.dumps({"error": str(e)})

def generate_osm_tags(user_query):
    system_prompt = """
You are an OpenStreetMap (OSM) tagging expert.
Convert the user's natural language request into a valid JSON dictionary of OSM tags that can be passed to osmnx.geometries_from_polygon(tags=...).

Rules:
1. Return ONLY a single JSON dictionary. No markdown fences or explanations.
2. Use standard OSM keys like "amenity", "building", "leisure", "landuse", "highway", "shop".
3. Extract the primary intent of the user's query.

Examples:
- "jogging path" -> {"highway": ["path", "track", "footway"], "leisure": "park"}
- "national highway" -> {"highway": ["motorway", "trunk", "primary"]}
- "best hospitals" -> {"amenity": ["hospital", "clinic"]}
- "solar farms" -> {"power": "plant", "plant:source": "solar"}
"""

    user_prompt = f"Convert this query to OSM tags: '{user_query}'"

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 150
            },
            timeout=30
        )
        data = response.json()
        raw_output = data["choices"][0]["message"]["content"]
        
        # Clean potential markdown
        import re
        cleaned = re.sub(r"```json", "", raw_output)
        cleaned = re.sub(r"```", "", cleaned)
        return json.loads(cleaned)

    except Exception as e:
        print("OSM Tag Generation Error:", e)
        # Fallback to generic building/amenity if LLM fails
        return {"amenity": True}

def generate_feature_reasoning(user_query, feature_properties):
    system_prompt = """
You are an expert GIS Spatial Analyst.
The user asked for a specific type of location (e.g. "a place to jog", "a suitable hospital site").
We successfully extracted a real-world geographic feature from OpenStreetMap that matches their criteria.
Given the user's query and the feature's raw properties (name, tags, area, etc.), write a compelling, 1-sentence justification explaining WHY this specific feature is an excellent choice.

Rules:
1. Max 1 sentence.
2. Be specific. If the feature has a "name", use it.
3. Pretend you analyzed it spatially.
4. Output raw text ONLY. No quotes.
"""

    user_prompt = f"User Query: {user_query}\nFeature Properties: {json.dumps(feature_properties)}"

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.4,
                "max_tokens": 100
            },
            timeout=20
        )
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()

    except Exception as e:
        print("Reasoning Generation Error:", e)
        return "This location meets spatial criteria for your query."