import requests
import json

OPENROUTER_API_KEY = "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"

def generate_workflow_no_rag(user_query):

    prompt = f"""
You are a GIS workflow generator.

Generate a structured JSON workflow for the following task.

Rules:
- Output STRICT JSON.
- No explanation outside JSON.

Schema:

{{
  "workflow_name": "",
  "workflow_type": "",
  "steps": [
    {{
      "step_id": 1,
      "tool": "",
      "inputs": {{}},
      "parameters": {{}},
      "outputs": {{}}
    }}
  ]
}}

Task:
{user_query}
"""

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "mistralai/mistral-7b-instruct",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0
        }
    )

    data = response.json()

    if "choices" not in data:
        return json.dumps({"error": data})

    content = data["choices"][0]["message"]["content"]

    # Clean markdown
    content = content.replace("```json", "").replace("```", "").strip()

    return content