import json
import numpy as np
import re
from build_index import build_index
from openrouter_client import generate_workflow

# ----------------------------------------
# Retrieve top-k documents
# ----------------------------------------

def retrieve_documents(query, index, metadata, k=8):
    from build_index import get_model
    model = get_model()

    query_embedding = model.encode([query], convert_to_numpy=True)
    query_embedding = query_embedding.astype("float32")

    distances, indices = index.search(query_embedding, k)

    retrieved = []
    for idx in indices[0]:
        retrieved.append(metadata[idx])

    return retrieved


# ----------------------------------------
# Structured context builder
# ----------------------------------------

def build_context(retrieved_docs):

    domain_rules = []
    workflow_patterns = []
    semantic_tools = []
    atomic_tools = []

    for doc in retrieved_docs:

        category = doc.get("category", "")
        workflow_type = doc.get("workflow_type", "")

        if doc.get("concept"):
            domain_rules.append(doc)

        elif workflow_type:
            workflow_patterns.append(doc)

        elif category in ["raster_analysis", "multi_criteria_analysis", "post_processing"]:
            semantic_tools.append(doc)

        else:
            atomic_tools.append(doc)

    context = ""

    # Priority order
    for group in [domain_rules, workflow_patterns, semantic_tools, atomic_tools]:
        for tool in group:
            context += f"""
Tool Name: {tool.get('tool_name')}
Description: {tool.get('description')}
Category: {tool.get('category')}
Workflow Type: {tool.get('workflow_type')}
Constraints: {tool.get('constraints')}
"""

    return context


# ----------------------------------------
# JSON validator
# ----------------------------------------
import json_repair
import re

def validate_json(output):
    try:
        # Remove code fences
        cleaned = re.sub(r"```json", "", output)
        cleaned = re.sub(r"```", "", cleaned)

        # Extract first JSON object using regex
        json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)

        if not json_match:
            raise ValueError("No JSON object found in response")

        json_string = json_match.group(0)

        parsed = json_repair.loads(json_string)

        if not isinstance(parsed, dict):
            raise ValueError('Parsed output is not a dictionary')

        if "steps" not in parsed:
            raise ValueError("Missing 'steps' key")

        return parsed

    except Exception as e:
        with open("raw_output.txt", "w") as f:
            f.write(output)
        with open('raw_output.txt', 'w', encoding='utf-8') as f:
            f.write(output)
        return {'error': f'Invalid JSON: {str(e)}', 'raw': output}
# ----------------------------------------
# Main pipeline
# ----------------------------------------

def run_pipeline(user_query, location="", previous_workflow=None, feedback=None):

    index, metadata = build_index()

    # retrieved = retrieve_documents(user_query, index, metadata, k=8)
    retrieved = retrieve_documents(user_query, index, metadata, k=5)

    context = build_context(retrieved)

    # Strong constraints for LLM
    system_instructions = """
You are an expert GIS analyst and spatial data scientist planner.
The user is currently focused on the geographic region: {LOCATION}.

We have the following strict datasets available for analysis:
1. "population_raster": Population density. Use for Malls, Hospitals, Commercial hubs, Schools, etc.
2. "dem_raster": Elevation/Slope. Use for Solar farms, Wind farms, Flood risks, Construction costs.
3. "vegetation_raster": NDVI or Land Cover. Use to avoid forests, or find green spaces/parks.
4. "road_network": Distance to driving roads. Use for warehouses, EV stations, emergency services.
5. "land_use_raster": Zoning classifications. Use to evaluate commercial vs residential zones or avoid water bodies.

If workflow_type is site_suitability:
- You MUST select the most logical datasets from the 5 available options above based on the specific end-goal.
- IMPORTANT: Site suitability is about finding OPTIMAL NEW BUILD SITES, not just identifying existing ones.
- For commercial/mall requests: prioritize "population_raster" (near consumers), "road_network" (easy access), and "vegetation_raster" (specifically look for LOW vegetation/barren land to minimize environmental impact).
- You MUST include WeightedOverlay for those criteria.
- You MUST normalize all criteria before combining.
- ExtractTopLocations must be final step.
- Do not repeat gdalwarp unnecessarily.

Rules:
- Maximum 10 steps.
- Do not make up datasets. Use ONLY the names listed above as inputs.
- Use raster-based approach for site suitability.
- All steps must be logically ordered.
- Output ONLY valid JSON.
- Follow this schema:

{
  "workflow_name": "",
  "workflow_type": "",
  "reasoning": "Write a short paragraph explaining the spatial analysis strategy for this workflow. Act as an expert GIS consultant detailing explicitly WHICH of the 5 datasets you chose and WHY they are suitable for this specific location and use-case.",
  "steps": [
    {
      "step_id": 1,
      "tool": "",
      "inputs": {},
      "parameters": {},
      "outputs": {}
    }
  ]
}
""".replace("{LOCATION}", location)

    if previous_workflow and feedback:
        user_query_override = f"Original Query: {user_query}\n\nPrevious Plan:\n{json.dumps(previous_workflow)}\n\nUser Feedback for Modification:\n{feedback}\n\nPlease generate a completely revised workflow JSON that addresses the user feedback."
    else:
        user_query_override = user_query

    llm_output = generate_workflow(user_query_override, context, system_instructions)

    workflow = validate_json(llm_output)
    
    from workflow_validator import validate_semantics

    is_valid, message = validate_semantics(workflow)

    if not is_valid:
        print("Workflow failed semantic validation:", message)
        # Regenerate once
        llm_output = generate_workflow(user_query, context, system_instructions)
        workflow = validate_json(llm_output)

    return workflow


