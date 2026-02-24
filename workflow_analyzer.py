import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
from collections import Counter


# ----------------------------
# Load Workflow
# ----------------------------

def load_workflow(workflow_path):
    with open(workflow_path, "r") as f:
        return json.load(f)


# ----------------------------
# Structural Metrics
# ----------------------------

def analyze_structure(workflow):
    steps = workflow.get("steps", [])
    tools = [step["tool"] for step in steps]

    metrics = {}

    metrics["num_steps"] = len(steps)
    metrics["unique_tools"] = len(set(tools))
    metrics["tool_diversity_ratio"] = metrics["unique_tools"] / max(len(steps), 1)

    tool_counts = Counter(tools)
    metrics["most_used_tool"] = tool_counts.most_common(1)[0][0] if tool_counts else None

    return metrics


# ----------------------------
# Completeness Check (EV Task)
# ----------------------------

def check_ev_completeness(workflow):
    required_keywords = ["slope", "buffer", "overlay"]

    steps = workflow.get("steps", [])
    tools = [step["tool"].lower() for step in steps]

    score = 0
    for keyword in required_keywords:
        if any(keyword in tool for tool in tools):
            score += 1

    completeness_score = score / len(required_keywords)

    return completeness_score


# ----------------------------
# Robustness Checks
# ----------------------------

def robustness_check(workflow):
    steps = workflow.get("steps", [])

    valid = 1
    missing_parameters = 0

    for step in steps:
        if "parameters" not in step:
            valid = 0

        if not step.get("parameters"):
            missing_parameters += 1

    robustness_score = 1 - (missing_parameters / max(len(steps), 1))

    return robustness_score


# ----------------------------
# Planning Score
# ----------------------------

def compute_planning_score(structure_metrics, completeness_score, robustness_score):

    validity = 1 if structure_metrics["num_steps"] > 0 else 0

    planning_score = (
        0.4 * validity +
        0.3 * completeness_score +
        0.3 * robustness_score
    )

    return planning_score


# ----------------------------
# DAG Visualization
# ----------------------------

def visualize_workflow_graph(workflow):

    G = nx.DiGraph()

    steps = workflow.get("steps", [])

    for step in steps:
        G.add_node(step["step_id"], label=step["tool"])

    for i in range(len(steps) - 1):
        G.add_edge(steps[i]["step_id"], steps[i+1]["step_id"])

    pos = nx.spring_layout(G)

    labels = {node: G.nodes[node]["label"] for node in G.nodes}

    plt.figure(figsize=(8, 6))
    nx.draw(G, pos, with_labels=True)
    nx.draw_networkx_labels(G, pos, labels)

    plt.title("Workflow DAG Structure")
    plt.show()


# ----------------------------
# Main Analysis Function
# ----------------------------

def analyze_workflow(workflow_path):

    workflow = load_workflow(workflow_path)

    structure = analyze_structure(workflow)
    completeness = check_ev_completeness(workflow)
    robustness = robustness_check(workflow)
    planning_score = compute_planning_score(structure, completeness, robustness)

    results = {
        "Structure": structure,
        "Completeness Score": completeness,
        "Robustness Score": robustness,
        "Planning Score": planning_score
    }

    print("\n===== WORKFLOW ANALYSIS =====\n")
    for key, value in results.items():
        print(key, ":", value)

    visualize_workflow_graph(workflow)

    return results