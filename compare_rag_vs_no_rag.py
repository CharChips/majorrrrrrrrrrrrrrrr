import json
from rag_pipeline import run_pipeline
from no_rag_client import generate_workflow_no_rag
from workflow_analyzer import analyze_structure, check_ev_completeness, robustness_check, compute_planning_score

QUERY = "Find suitable locations for EV charging stations in Navi Mumbai"

def evaluate(workflow_dict):
    structure = analyze_structure(workflow_dict)
    completeness = check_ev_completeness(workflow_dict)
    robustness = robustness_check(workflow_dict)
    score = compute_planning_score(structure, completeness, robustness)

    return {
        "steps": structure["num_steps"],
        "tool_diversity": structure["tool_diversity_ratio"],
        "completeness": completeness,
        "robustness": robustness,
        "planning_score": score
    }


if __name__ == "__main__":

    print("\n=== Generating RAG Workflow ===")
    rag_workflow = run_pipeline(QUERY)

    print("\n=== Generating NON-RAG Workflow ===")
    no_rag_raw = generate_workflow_no_rag(QUERY)
    try:
        no_rag_workflow = json.loads(no_rag_raw)
    except Exception:
        print("Non-RAG produced invalid JSON.")
    no_rag_workflow = {
        "steps": []
    }
    print("\n=== Evaluating RAG ===")
    rag_metrics = evaluate(rag_workflow)

    print("\n=== Evaluating NON-RAG ===")
    no_rag_metrics = evaluate(no_rag_workflow)

    print("\n========== COMPARISON ==========")
    print("RAG Metrics:", rag_metrics)
    print("NO-RAG Metrics:", no_rag_metrics)
    
    from research_plots import (
    plot_planning_score,
    plot_radar,
    plot_tool_diversity,
    plot_workflow_complexity,
    plot_multi_metric
)

plot_planning_score(rag_metrics, no_rag_metrics)
plot_radar(rag_metrics, no_rag_metrics)
plot_tool_diversity(rag_metrics, no_rag_metrics)
plot_workflow_complexity(rag_metrics, no_rag_metrics)
plot_multi_metric(rag_metrics, no_rag_metrics)