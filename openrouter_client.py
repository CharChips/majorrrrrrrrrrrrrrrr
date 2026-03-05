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
Convert the user's natural language request into a valid JSON dictionary of OSM tags that can be passed to osmnx.features_from_polygon(tags=...).

Rules:
1. Return ONLY a single JSON dictionary. No markdown fences or explanations.
2. Use standard OSM keys like "amenity", "building", "leisure", "landuse", "highway", "shop", "natural".
3. **CRITICAL**: If the user wants to *build*, *make*, or *find a site for* something new (e.g. "make a new school"), DO NOT just return the tags for the final building (e.g. {"amenity": "school"}). 
   Instead, return tags for suitable development land or zones:
   - Use "landuse" (e.g., ["greenfield", "brownfield", "grass", "meadow", "farmland", "residential"]).
   - Combine with relevant infrastructure if mentioned (e.g., {"highway": ["primary", "secondary"]} if they mention "near roads").
4. If they are looking for *existing* places (e.g. "find hospitals"), use the direct tags.

Examples:
- "jogging path" -> {"highway": ["path", "track", "footway"], "leisure": "park"}
- "national highway" -> {"highway": ["motorway", "trunk", "primary"]}
- "best hospitals" -> {"amenity": ["hospital", "clinic"]}
- "locations to build a new school near major roads" -> {"landuse": ["greenfield", "brownfield", "grass", "residential"], "highway": ["primary", "secondary", "trunk"]}
- "suitable site for a mall" -> {"landuse": ["retail", "commercial", "industrial", "brownfield"]}
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

def generate_deep_analysis(query, spatial_data, web_context):
    system_prompt = """
You are a Senior Spatial Strategy Consultant. 
The user is interested in a specific geographic site for a development project (e.g. building a mall).
We have extracted spatial statistics (Population, Slope, Vegetation, Road Access) and recent web news about the area.

Your task is to write a "Deep Site Analysis Report" in Markdown. 
Include:
1. **Site Suitability Summary**: How well it fits the query based on spatial data.
2. **Environmental & Structural Insights**: Mention vegetation (is it barren or forested?) and slope.
3. **Market & Logistics Context**: Mention road access and population density.
4. **Recent Local Developments**: Incorporate relevant news from the provided web context.
5. **Final Recommendation**: Should the user proceed with deeper due diligence?

Rules:
- Professional, detailed, but concise.
- Use Markdown headers, bold text, and bullet points.
- If web context is provided, cite it naturally.
- Output ONLY the Markdown report.
"""

    user_prompt = f"""
User Query: {query}
Spatial Data for this point: {json.dumps(spatial_data)}
Web Research Context: {web_context}
"""

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.5,
                "max_tokens": 800
            },
            timeout=40
        )
        data = response.json()
        if "error" in data:
            return f"API Error: {data['error']}"
        if "choices" not in data:
            return f"Unexpected response: {data}"
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Error generating report: {str(e)}"