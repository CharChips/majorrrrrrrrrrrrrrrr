import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd

sns.set(style="whitegrid")
plt.rcParams["figure.figsize"] = (8, 5)


# --------------------------------------------------
# Plot 1: Planning Score Comparison
# --------------------------------------------------

def plot_planning_score(rag_metrics, no_rag_metrics):

    scores = [rag_metrics["planning_score"], no_rag_metrics["planning_score"]]
    labels = ["GeoToolRAG", "Non-RAG LLM"]

    plt.figure()
    sns.barplot(x=labels, y=scores)
    plt.ylabel("Planning Score")
    plt.title("Overall Planning Quality Comparison")
    plt.ylim(0, 1)

    for i, v in enumerate(scores):
        plt.text(i, v + 0.02, f"{v:.2f}", ha='center')

    plt.savefig("plot1_planning_score.png", dpi=300)
    plt.show()


# --------------------------------------------------
# Plot 2: Radar Chart (Completeness vs Robustness)
# --------------------------------------------------

def plot_radar(rag_metrics, no_rag_metrics):

    categories = ["Completeness", "Robustness"]
    rag_values = [rag_metrics["completeness"], rag_metrics["robustness"]]
    no_rag_values = [no_rag_metrics["completeness"], no_rag_metrics["robustness"]]

    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    rag_values += rag_values[:1]
    no_rag_values += no_rag_values[:1]
    angles += angles[:1]

    plt.figure()
    ax = plt.subplot(111, polar=True)

    ax.plot(angles, rag_values, label="GeoToolRAG")
    ax.fill(angles, rag_values, alpha=0.25)

    ax.plot(angles, no_rag_values, label="Non-RAG LLM")
    ax.fill(angles, no_rag_values, alpha=0.25)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)

    plt.title("Completeness vs Robustness")
    plt.legend(loc="upper right")

    plt.savefig("plot2_radar.png", dpi=300)
    plt.show()


# --------------------------------------------------
# Plot 3: Tool Diversity Comparison
# --------------------------------------------------

def plot_tool_diversity(rag_metrics, no_rag_metrics):

    diversity = [rag_metrics["tool_diversity"], no_rag_metrics["tool_diversity"]]
    labels = ["GeoToolRAG", "Non-RAG LLM"]

    plt.figure()
    sns.barplot(x=labels, y=diversity)
    plt.ylabel("Tool Diversity Ratio")
    plt.title("Tool Usage Diversity Comparison")
    plt.ylim(0, 1)

    for i, v in enumerate(diversity):
        plt.text(i, v + 0.02, f"{v:.2f}", ha='center')

    plt.savefig("plot3_tool_diversity.png", dpi=300)
    plt.show()


# --------------------------------------------------
# Plot 4: Workflow Complexity (Step Count)
# --------------------------------------------------

def plot_workflow_complexity(rag_metrics, no_rag_metrics):

    steps = [rag_metrics["steps"], no_rag_metrics["steps"]]
    labels = ["GeoToolRAG", "Non-RAG LLM"]

    plt.figure()
    sns.barplot(x=labels, y=steps)
    plt.ylabel("Number of Steps")
    plt.title("Workflow Structural Complexity")
    
    for i, v in enumerate(steps):
        plt.text(i, v + 0.1, f"{v}", ha='center')

    plt.savefig("plot4_complexity.png", dpi=300)
    plt.show()


# --------------------------------------------------
# Plot 5: Multi-Metric Comparison
# --------------------------------------------------

def plot_multi_metric(rag_metrics, no_rag_metrics):

    metrics = ["completeness", "robustness", "planning_score"]
    rag_vals = [rag_metrics[m] for m in metrics]
    no_rag_vals = [no_rag_metrics[m] for m in metrics]

    x = np.arange(len(metrics))
    width = 0.35

    plt.figure()
    plt.bar(x - width/2, rag_vals, width, label="GeoToolRAG")
    plt.bar(x + width/2, no_rag_vals, width, label="Non-RAG LLM")

    plt.xticks(x, metrics)
    plt.ylim(0, 1)
    plt.title("Multi-Metric Performance Comparison")
    plt.legend()

    plt.savefig("plot5_multi_metric.png", dpi=300)
    plt.show()