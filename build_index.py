import os
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# -----------------------------
# Lazy model loader (safer)
# -----------------------------
_model = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("sentence-transformers/paraphrase-MiniLM-L3-v2")
    return _model


# -----------------------------
# Load JSON knowledge base
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_tool_cards(base_path=os.path.join(BASE_DIR, "gis_knowledge_base")):
    documents = []
    metadata = []

    if not os.path.exists(base_path):
        raise ValueError(f"Knowledge base path not found: {base_path}")

    for root, _, files in os.walk(base_path):
        for file in files:
            if file.endswith(".json"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    try:
                        data = json.load(f)
                    except Exception as e:
                        print(f"Skipping invalid JSON: {path}")
                        continue

                text = f"""
                Tool Name: {data.get('tool_name', '')}
                Description: {data.get('description', '')}
                Category: {data.get('category', '')}
                Workflow Type: {data.get('workflow_type', '')}
                Concept: {data.get('concept', '')}
                """

                documents.append(text.strip())
                metadata.append(data)

    if len(documents) == 0:
        raise ValueError("No JSON files found in knowledge base.")

    return documents, metadata


# -----------------------------
# Build FAISS index safely
# -----------------------------
def build_index():
    docs, metadata = load_tool_cards()

    model = get_model()

    embeddings = model.encode(
        docs,
        convert_to_numpy=True,
        show_progress_bar=False
    )

    # Ensure embeddings are 2D
    if embeddings.ndim == 1:
        embeddings = embeddings[np.newaxis, :]

    embeddings = embeddings.astype("float32")

    dim = embeddings.shape[1]

    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    print(f"FAISS index built with {len(docs)} documents. Dimension: {dim}")

    return index, metadata