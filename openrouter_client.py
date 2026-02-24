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
                "model": "llama-3.1-8b-instant",
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