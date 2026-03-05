# streamlit_app.py

import streamlit as st
import json
import matplotlib.pyplot as plt
import numpy as np

from engine_adapter import EngineAdapter
from main import generate_workflow_from_query
import requests

# --------------------------------------------------
# Streamlit Page Config
# --------------------------------------------------

st.set_page_config(
    page_title="GIS AI Expert",
    layout="wide"
)

st.title("GIS Site Suitability Expert")

st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
        color: #f0f2f6;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        background-color: #2e7bcf;
        color: white;
        font-weight: bold;
    }
    .stExpander {
        border: 1px solid #2e7bcf;
        border-radius: 10px;
    }
    p, li, h1, h2, h3, h4, h5, h6 {
        color: #f0f2f6;
    }
    </style>
    """, unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am your GIS AI Expert. Tell me what kind of site you are looking to build. For example, 'Find the best place to build a new mall in Navi Mumbai'"}
    ]

# Display chat messages from history on app rerun
for msg_idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        if message["role"] == "assistant" and "workflow_json" in message:
            with st.expander("🧠 View Workflow Strategy & JSON"):
                wf = message["workflow_json"]
                if "reasoning" in wf:
                    st.info(wf["reasoning"])
                st.json(wf)
                
        if message["role"] == "assistant" and "result" in message:
            result = message["result"]
            locations = []
            if result["status"] == "success":
                for step_res in result.get("results", {}).values():
                    if isinstance(step_res, dict) and "final_locations" in step_res:
                        locations = step_res["final_locations"]
                        break
            
            if locations:
                st.subheader("📍 Recommended Build Sites")
                cols = st.columns(min(len(locations), 3))
                for i, loc in enumerate(locations[:6]): # Limit to 6 to save space
                    with cols[i % 3]:
                        with st.container(border=True):
                            st.write(f"### Site #{i+1}")
                            st.write(f"**Score**: {loc['score']:.2f}")
                            st.write(f"**Lat**: {loc['latitude']:.4f}")
                            st.write(f"**Lon**: {loc['longitude']:.4f}")
                            
                            if st.button(f"🔍 Deep Analysis", key=f"deep_{msg_idx}_{i}"):
                                with st.sidebar:
                                    st.subheader(f"Detailed Analysis: Site #{i+1}")
                                    with st.spinner("Analyzing site trends..."):
                                        try:
                                            res = requests.post("http://localhost:8000/deep-analysis", json={
                                                "query": message.get("query", "site analysis"),
                                                "lat": loc['latitude'],
                                                "lon": loc['longitude'],
                                                "location_name": f"Predicted Site {i+1}"
                                            })
                                            analysis_data = res.json()
                                            if analysis_data.get("status") == "success":
                                                st.markdown(analysis_data["report"])
                                                st.divider()
                                                st.write("#### Raw Spatial Stats")
                                                st.json(analysis_data["spatial_stats"])
                                            else:
                                                st.error("Deep analysis failed.")
                                        except Exception as e:
                                            st.error(f"Error connecting to backend: {e}")

# React to user input
if prompt := st.chat_input("Enter your spatial query..."):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        st.markdown("Analyzing your request and determining spatial suitability...")
        
        with st.spinner("Generating workflow using LLM..."):
            workflow_json = generate_workflow_from_query(prompt)

        with st.spinner("Executing GIS workflow..."):
            adapter = EngineAdapter()
            result = adapter.run_workflow(workflow_json)

        assistant_msg = {
            "role": "assistant",
            "content": "I have completed the analysis based on your criteria. You can review the top recommended sites below and perform a deep analysis on any of them.",
            "workflow_json": workflow_json,
            "result": result,
            "query": prompt
        }
        st.session_state.messages.append(assistant_msg)
        st.rerun()
