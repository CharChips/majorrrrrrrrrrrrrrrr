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
import json
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

        parsed = json.loads(json_string)

        if "steps" not in parsed:
            raise ValueError("Missing 'steps' key")

        return parsed

    except Exception as e:
        return {"error": f"Invalid JSON: {str(e)}"}
# ----------------------------------------
# Main pipeline
# ----------------------------------------

def run_pipeline(user_query):

    index, metadata = build_index()

    # retrieved = retrieve_documents(user_query, index, metadata, k=8)
    retrieved = retrieve_documents(user_query, index, metadata, k=5)

    context = build_context(retrieved)

    # Strong constraints for LLM
    system_instructions = """
You are a GIS workflow planner.

If workflow_type is site_suitability:
- You MUST include WeightedOverlay.
- You MUST normalize all criteria before combining.
- ExtractTopLocations must be final step.
- Do not repeat gdalwarp unnecessarily.

Rules:
- Maximum 10 steps.
- Do not repeat tools unnecessarily.
- Use raster-based approach for site suitability.
- All steps must be logically ordered.
- Output ONLY valid JSON.
- Follow this schema:

{
  "workflow_name": "",
  "workflow_type": "",
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
"""

    llm_output = generate_workflow(user_query, context, system_instructions)

    workflow = validate_json(llm_output)
    
    from workflow_validator import validate_semantics

    is_valid, message = validate_semantics(workflow)

    if not is_valid:
        print("Workflow failed semantic validation:", message)
        # Regenerate once
        llm_output = generate_workflow(user_query, context, system_instructions)
        workflow = validate_json(llm_output)

    return workflow