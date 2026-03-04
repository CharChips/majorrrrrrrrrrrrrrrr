# streamlit_app.py — Premium GIS UI

import streamlit as st
import json
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

from engine_adapter import EngineAdapter
from main import generate_workflow_from_query


# ──────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────

st.set_page_config(
    page_title="GeoSpatial AI — EV Site Intelligence",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# GLOBAL CSS
# ──────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    background-color: #050d1a !important;
    color: #e0f0ff !important;
}

/* ── Streamlit chrome ── */
.stApp { background: #050d1a; }
header[data-testid="stHeader"] { background: #060f1f !important; border-bottom: 1px solid #1a3a5c; }
section[data-testid="stSidebar"] {
    background: #0a1628 !important;
    border-right: 1px solid #1a3a5c !important;
}
section[data-testid="stSidebar"] * { color: #e0f0ff !important; }

/* ── Sidebar ── */
.css-1d391kg { background: #0a1628 !important; }

/* ── Divider ── */
hr { border-color: #1a3a5c !important; margin: 12px 0; }

/* ── Buttons ── */
.stButton>button {
    background: linear-gradient(135deg, #0066cc, #00aaff) !important;
    border: none !important; color: #fff !important;
    font-weight: 600 !important; font-size: 13px !important;
    border-radius: 8px !important; letter-spacing: 0.04em !important;
    box-shadow: 0 0 18px #0088ff44 !important;
    transition: all 0.25s ease !important;
    padding: 8px 20px !important;
}
.stButton>button:hover {
    background: linear-gradient(135deg, #0088ff, #00d4ff) !important;
    box-shadow: 0 0 28px #00aaffaa !important;
    transform: translateY(-1px) !important;
}

/* ── Input / Textarea ── */
.stTextInput>div>div>input,
.stTextArea>div>div>textarea {
    background: #0f1e35 !important;
    border: 1px solid #1a3a5c !important;
    border-radius: 8px !important;
    color: #e0f0ff !important;
    font-family: 'Inter', sans-serif !important;
}
.stTextInput>div>div>input:focus,
.stTextArea>div>div>textarea:focus {
    border-color: #00d4ff !important;
    box-shadow: 0 0 0 2px #00d4ff22 !important;
}

/* ── Sliders ── */
.stSlider [data-baseweb="slider"] div[role="slider"] {
    background: #00d4ff !important;
    box-shadow: 0 0 8px #00d4ff !important;
}

/* ── Metrics ── */
[data-testid="metric-container"] {
    background: #0f1e35 !important;
    border: 1px solid #1a3a5c !important;
    border-radius: 10px !important;
    padding: 14px 16px !important;
}
[data-testid="metric-container"] label {
    color: #7da8cc !important; font-size: 11px !important;
    text-transform: uppercase; letter-spacing: 0.1em;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #00d4ff !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 22px !important; font-weight: 700 !important;
}

/* ── Expander ── */
.streamlit-expanderHeader {
    background: #0f1e35 !important;
    border: 1px solid #1a3a5c !important;
    border-radius: 8px !important;
    color: #e0f0ff !important;
    font-weight: 600 !important;
}
.streamlit-expanderContent {
    background: #0a1628 !important;
    border: 1px solid #1a3a5c !important;
    border-top: none !important;
}

/* ── Spinner ── */
.stSpinner > div > div { border-top-color: #00d4ff !important; }

/* ── Progress ── */
.stProgress > div > div { background: linear-gradient(90deg, #0066cc, #00d4ff) !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] { background: #0a1628 !important; gap: 4px; }
.stTabs [data-baseweb="tab"] {
    background: #0f1e35 !important; border: 1px solid #1a3a5c !important;
    border-radius: 8px 8px 0 0 !important; color: #7da8cc !important;
    font-weight: 500 !important;
}
.stTabs [aria-selected="true"] {
    background: #142340 !important; border-bottom-color: transparent !important;
    color: #00d4ff !important;
}

/* ── Code / JSON ── */
.stJson, pre {
    background: #060f1f !important;
    border: 1px solid #1a3a5c !important;
    border-radius: 8px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 12px !important;
}

/* ── Success/Error/Warning ── */
.stSuccess { background: #00ff9d11 !important; border-left: 3px solid #00ff9d !important; }
.stError   { background: #ff4d6d11 !important; border-left: 3px solid #ff4d6d !important; }
.stWarning { background: #ffb83011 !important; border-left: 3px solid #ffb830 !important; }

/* ── Custom label ── */
.gis-label {
    font-size: 10px; font-weight: 600; letter-spacing: 0.14em;
    text-transform: uppercase; color: #3a6080; margin-bottom: 8px;
    display: flex; align-items: center; gap: 8px;
}
.gis-label::after { content: ''; flex: 1; height: 1px; background: #1a3a5c; }

/* ── Criteria card ── */
.criteria-card {
    background: #0f1e35; border: 1px solid #1a3a5c;
    border-radius: 10px; padding: 12px 14px;
    margin-bottom: 8px; border-left: 3px solid;
    display: flex; gap: 12px; align-items: center;
}
.criteria-card.road { border-left-color: #00d4ff; }
.criteria-card.slope { border-left-color: #00ff9d; }

/* ── Workflow step ── */
.workflow-step {
    background: #0f1e35; border: 1px solid #1a3a5c;
    border-radius: 8px; padding: 10px 14px;
    margin-bottom: 6px; display: flex; align-items: center; gap: 10px;
    font-family: 'JetBrains Mono', monospace; font-size: 12px;
}
.step-badge {
    background: #00d4ff15; color: #00d4ff;
    border: 1px solid #00d4ff33; border-radius: 4px;
    padding: 2px 8px; font-size: 10px; font-weight: 700;
    min-width: 28px; text-align: center;
}
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────

st.markdown("""
<div style="display:flex;align-items:center;gap:14px;padding:8px 0 20px 0;border-bottom:1px solid #1a3a5c;margin-bottom:24px">
  <div style="width:44px;height:44px;background:linear-gradient(135deg,#0066cc,#00d4ff);border-radius:10px;
              display:flex;align-items:center;justify-content:center;box-shadow:0 0 18px #00d4ff44;flex-shrink:0">
    <span style="font-size:20px">🌐</span>
  </div>
  <div>
    <div style="font-size:20px;font-weight:700;letter-spacing:0.02em">
      Geo<span style="color:#00d4ff">Spatial</span> AI
      <span style="font-size:11px;background:#00d4ff15;color:#00d4ff;border:1px solid #00d4ff33;
                   border-radius:12px;padding:2px 10px;margin-left:10px;font-weight:500;vertical-align:middle">
        EV Site Intelligence
      </span>
    </div>
    <div style="font-size:11px;color:#3a6080;letter-spacing:0.06em;text-transform:uppercase;margin-top:2px">
      RAG-Powered GIS Workflow Engine · Navi Mumbai
    </div>
  </div>
  <div style="margin-left:auto;display:flex;gap:8px;align-items:center">
    <div style="display:flex;align-items:center;gap:6px;background:#0f1e35;border:1px solid #1a3a5c;
                border-radius:20px;padding:5px 12px">
      <div style="width:7px;height:7px;border-radius:50%;background:#00ff9d;box-shadow:0 0 6px #00ff9d"></div>
      <span style="font-size:11px;color:#7da8cc;font-weight:500">Engine Ready</span>
    </div>
    <div style="background:#00d4ff15;color:#00d4ff;border:1px solid #00d4ff33;border-radius:12px;
                padding:4px 12px;font-size:10px;font-weight:600;letter-spacing:0.08em">RAG ACTIVE</div>
  </div>
</div>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────

with st.sidebar:
    st.markdown('<div class="gis-label">Spatial Query</div>', unsafe_allow_html=True)

    query = st.text_area(
        label="query_input",
        value="Find suitable EV charging station locations in Navi Mumbai near major roads",
        height=80,
        label_visibility="collapsed",
    )

    run_button = st.button("⚡  Run GIS Analysis", use_container_width=True)

    st.markdown("---")
    st.markdown('<div class="gis-label">Suitability Criteria</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="criteria-card road">
      <div>
        <div style="font-size:12px;font-weight:600">🛣 Road Proximity</div>
        <div style="font-size:10px;color:#3a6080;margin-top:2px">Distance to major OSM roads</div>
      </div>
      <div style="margin-left:auto;font-family:'JetBrains Mono',monospace;color:#00d4ff;font-size:12px">60%</div>
    </div>
    <div class="criteria-card slope">
      <div>
        <div style="font-size:12px;font-weight:600">⛰ Terrain Slope</div>
        <div style="font-size:10px;color:#3a6080;margin-top:2px">SRTM DEM slope analysis</div>
      </div>
      <div style="margin-left:auto;font-family:'JetBrains Mono',monospace;color:#00ff9d;font-size:12px">40%</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="gis-label">Weight Tuning</div>', unsafe_allow_html=True)

    w_road = st.slider("Road Proximity Weight (%)", 0, 100, 60, step=5)
    w_slope = 100 - w_road
    st.caption(f"Slope weight auto-set to **{w_slope}%**")

    n_locs = st.slider("Top Locations", 1, 20, 10)

    st.markdown("---")
    st.markdown('<div class="gis-label">Data Sources</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:11px;color:#7da8cc;line-height:2">
      🛰 <b>Google Earth Engine</b> — SRTM DEM<br>
      🗺 <b>OpenStreetMap</b> — Road network<br>
      🤖 <b>OpenRouter LLM</b> — Workflow generation<br>
      📚 <b>FAISS RAG</b> — GIS knowledge base
    </div>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────
# MAIN CONTENT
# ──────────────────────────────────────────────

if run_button:

    # ── Workflow generation ────────────────────
    st.markdown('<div class="gis-label">Workflow Generation</div>', unsafe_allow_html=True)

    with st.spinner("🧠  Generating GIS workflow using LLM + RAG…"):
        workflow_json = generate_workflow_from_query(query)

    if "error" in workflow_json:
        st.error(f"Workflow generation failed: {workflow_json['error']}")
        st.stop()

    steps = workflow_json.get("steps", [])
    wf_name = workflow_json.get("workflow_name", "GIS Workflow")
    wf_type = workflow_json.get("workflow_type", "")

    # Workflow header
    st.markdown(f"""
    <div style="background:#0f1e35;border:1px solid #1a3a5c;border-radius:10px;padding:14px 18px;
                margin-bottom:16px;display:flex;align-items:center;gap:12px">
      <div style="font-size:14px;font-weight:700">{wf_name}</div>
      <div style="background:#00d4ff15;color:#00d4ff;border:1px solid #00d4ff33;border-radius:4px;
                  padding:2px 8px;font-size:10px;font-weight:600;text-transform:uppercase">{wf_type}</div>
      <div style="margin-left:auto;font-family:'JetBrains Mono',monospace;
                  font-size:11px;color:#7da8cc">{len(steps)} steps</div>
    </div>
    """, unsafe_allow_html=True)

    # Workflow steps
    steps_html = ""
    for s in steps:
        tool = s.get("tool", "")
        out  = list(s.get("outputs", {}).values())
        out_txt = ", ".join(out) if out else "—"
        steps_html += f"""
        <div class="workflow-step">
          <div class="step-badge">{s.get('step_id','?')}</div>
          <div style="flex:1">
            <span style="color:#00d4ff;font-weight:600">{tool}</span>
            <span style="color:#3a6080;font-size:10px;margin-left:8px">→ {out_txt}</span>
          </div>
        </div>"""

    with st.expander("📋  View Full Workflow Steps", expanded=False):
        st.markdown(steps_html, unsafe_allow_html=True)
        st.markdown("**Raw JSON**")
        st.json(workflow_json)

    st.markdown("---")

    # ── GIS Engine ────────────────────────────
    st.markdown('<div class="gis-label">GIS Engine Execution</div>', unsafe_allow_html=True)

    progress_bar = st.progress(0)

    with st.spinner("⚙️  Executing GIS workflow…"):
        adapter = EngineAdapter()
        result  = adapter.run_workflow(workflow_json)

    progress_bar.progress(100)

    # ── Metrics ───────────────────────────────
    st.markdown("---")
    st.markdown('<div class="gis-label">Analysis Results</div>', unsafe_allow_html=True)

    if result["status"] == "success":
        final_key    = list(result["results"].values())[-1]
        final_raster = adapter.engine.context.get(final_key)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Workflow Steps", len(steps))
        with col2:
            st.metric("Status", "✓ Success")
        with col3:
            if isinstance(final_raster, np.ndarray):
                st.metric("Raster Shape", f"{final_raster.shape[0]} × {final_raster.shape[1]}")
            else:
                st.metric("Raster Shape", "—")
        with col4:
            if isinstance(final_raster, np.ndarray):
                st.metric("Score Range", f"{final_raster.min():.2f} – {final_raster.max():.2f}")
            else:
                st.metric("Score Range", "—")

        # ── Logs ──────────────────────────────
        with st.expander("📜  Execution Logs", expanded=False):
            log_html = '<div style="font-family:\'JetBrains Mono\',monospace;font-size:11px;line-height:2">'
            for i, log in enumerate(result["logs"]):
                color = "#00d4ff" if i % 2 == 0 else "#7da8cc"
                log_html += f'<div style="color:{color}">› {log}</div>'
            log_html += '</div>'
            st.markdown(log_html, unsafe_allow_html=True)

        # ── Map ───────────────────────────────
        st.markdown("---")
        st.markdown('<div class="gis-label">Suitability Map</div>', unsafe_allow_html=True)

        if isinstance(final_raster, np.ndarray):
            # Custom dark-styled colormap
            colors_list = ["#0a0a1a", "#0d2044", "#0066cc", "#00aaff", "#00ff9d"]
            cmap = mcolors.LinearSegmentedColormap.from_list("gis_dark", colors_list)

            fig, ax = plt.subplots(figsize=(12, 6), facecolor="#050d1a")
            ax.set_facecolor("#050d1a")

            im = ax.imshow(final_raster, cmap=cmap, aspect='auto')

            cbar = plt.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
            cbar.ax.yaxis.set_tick_params(color='#7da8cc', labelsize=9)
            cbar.outline.set_edgecolor('#1a3a5c')
            plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='#7da8cc',
                     fontfamily='JetBrains Mono')
            cbar.set_label("Suitability Score", color='#7da8cc', fontsize=10,
                           fontfamily='JetBrains Mono')

            ax.set_title("EV Charging Site Suitability Score", color='#e0f0ff',
                         fontsize=14, fontweight='bold', fontfamily='Inter', pad=14)
            ax.tick_params(colors='#3a6080', labelsize=8)
            for spine in ax.spines.values():
                spine.set_edgecolor('#1a3a5c')

            st.pyplot(fig)
        else:
            st.warning("⚠️ No raster output found to display.")

    else:
        st.markdown(f"""
        <div style="background:#ff4d6d11;border:1px solid #ff4d6d33;border-left:3px solid #ff4d6d;
                    border-radius:8px;padding:14px 18px;color:#ff4d6d">
          <b>Workflow Execution Failed</b><br>
          <code style="font-size:11px">{result.get('error','Unknown error')}</code>
        </div>
        """, unsafe_allow_html=True)

else:
    # ── Empty state ───────────────────────────
    st.markdown("""
    <div style="text-align:center;padding:60px 20px">
      <div style="font-size:56px;margin-bottom:16px">🗺</div>
      <div style="font-size:20px;font-weight:700;color:#e0f0ff;margin-bottom:8px">
        GeoSpatial <span style="color:#00d4ff">Intelligence</span> Ready
      </div>
      <div style="font-size:13px;color:#3a6080;max-width:480px;margin:0 auto;line-height:1.7">
        Enter a spatial query in the sidebar and click <b>Run GIS Analysis</b> to generate
        an LLM-powered GIS workflow and identify optimal EV charging site locations.
      </div>

      <div style="display:flex;gap:16px;justify-content:center;margin-top:36px;flex-wrap:wrap">
        <div style="background:#0f1e35;border:1px solid #1a3a5c;border-radius:10px;padding:16px 24px;min-width:160px">
          <div style="font-size:24px;margin-bottom:6px">🛰</div>
          <div style="font-size:12px;font-weight:600">Google Earth Engine</div>
          <div style="font-size:10px;color:#3a6080;margin-top:4px">SRTM DEM terrain data</div>
        </div>
        <div style="background:#0f1e35;border:1px solid #1a3a5c;border-radius:10px;padding:16px 24px;min-width:160px">
          <div style="font-size:24px;margin-bottom:6px">🗺</div>
          <div style="font-size:12px;font-weight:600">OpenStreetMap</div>
          <div style="font-size:10px;color:#3a6080;margin-top:4px">Real-time road network</div>
        </div>
        <div style="background:#0f1e35;border:1px solid #1a3a5c;border-radius:10px;padding:16px 24px;min-width:160px">
          <div style="font-size:24px;margin-bottom:6px">🤖</div>
          <div style="font-size:12px;font-weight:600">RAG + LLM</div>
          <div style="font-size:10px;color:#3a6080;margin-top:4px">AI workflow generation</div>
        </div>
        <div style="background:#0f1e35;border:1px solid #1a3a5c;border-radius:10px;padding:16px 24px;min-width:160px">
          <div style="font-size:24px;margin-bottom:6px">📍</div>
          <div style="font-size:12px;font-weight:600">Site Suitability</div>
          <div style="font-size:10px;color:#3a6080;margin-top:4px">Multi-criteria analysis</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)