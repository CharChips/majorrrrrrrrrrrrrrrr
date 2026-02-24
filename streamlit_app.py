# streamlit_app.py

import streamlit as st
import json
import matplotlib.pyplot as plt
import numpy as np

from engine_adapter import EngineAdapter
from main import generate_workflow_from_query


# --------------------------------------------------
# Streamlit Page Config
# --------------------------------------------------

st.set_page_config(
    page_title="EV Site Suitability - GIS AI Engine",
    layout="wide"
)

st.title("🚗⚡ EV Charging Site Suitability - Navi Mumbai")

st.markdown(
"""
This demo uses:
- LLM + RAG to generate GIS workflow
- Automated GIS Engine execution
- Multi-criteria suitability analysis
"""
)

# --------------------------------------------------
# User Query Section
# --------------------------------------------------

query = st.text_input(
    "Enter spatial query:",
    value="ev in navi mumbai"
)

run_button = st.button("Run Analysis")

# --------------------------------------------------
# Execution
# --------------------------------------------------

if run_button:

    with st.spinner("Generating workflow using LLM..."):

        workflow_json = generate_workflow_from_query(query)

    st.subheader("🧠 Generated Workflow (LLM Output)")
    st.json(workflow_json)

    # --------------------------------------------------
    # Run GIS Engine
    # --------------------------------------------------

    with st.spinner("Executing GIS workflow..."):

        adapter = EngineAdapter()
        result = adapter.run_workflow(workflow_json)

    # --------------------------------------------------
    # Logs
    # --------------------------------------------------

    st.subheader("📜 Execution Logs")

    if result["status"] == "success":
        for log in result["logs"]:
            st.text(log)
    else:
        st.error("Workflow failed")
        st.text(result["error"])

    # --------------------------------------------------
    # Display Output
    # --------------------------------------------------

    st.subheader("🗺 Final Suitability Map")

    # We assume final output key is stored
    final_key = list(result["results"].values())[-1]

    # Get raster array from context
    final_raster = adapter.engine.context.get(final_key)

    if isinstance(final_raster, np.ndarray):

        fig, ax = plt.subplots(figsize=(8, 6))
        im = ax.imshow(final_raster, cmap="viridis")
        plt.colorbar(im, ax=ax)
        ax.set_title("EV Suitability Score (0-100)")

        st.pyplot(fig)

    else:
        st.warning("No raster output found to display.")