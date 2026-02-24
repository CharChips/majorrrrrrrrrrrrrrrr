from rag_pipeline import run_pipeline
import json


def generate_workflow_from_query(query: str):
    """
    This function is used by Streamlit.
    It returns structured workflow JSON.
    """
    workflow = run_pipeline(query)
    return workflow


if __name__ == "__main__":

    query = "Find suitable locations for EV charging stations in Navi Mumbai"

    # 1️⃣ Generate workflow
    workflow = generate_workflow_from_query(query)

    # 2️⃣ Print workflow
    print(json.dumps(workflow, indent=4))

    # 3️⃣ Save workflow to file
    with open("generated_workflow.json", "w") as f:
        json.dump(workflow, f, indent=4)

    print("\nWorkflow saved to generated_workflow.json")