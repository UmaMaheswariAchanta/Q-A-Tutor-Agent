import os
from pathlib import Path
import requests
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from pydantic import BaseModel

# ============================================================
# 1. SETUP & CONFIGURATION
# ============================================================

app = FastAPI(title="Network Security Tutor (LM Studio GPU + Qdrant)")

# Paths
script_dir = Path(__file__).parent
project_root = script_dir.parent
templates_dir = project_root / "templates"

# Template Engine
jinja_env = Environment(
    loader=FileSystemLoader(str(templates_dir)),
    autoescape=select_autoescape(['html', 'xml'])
)

SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY", "0296b30af4db54f0c40dfac526966c93ef22816317822c3935bfec0d614adfe4")

def render_template(name, **kwargs):
    return jinja_env.get_template(name).render(**kwargs)

# Configuration
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "network_security_docs"
RELEVANCE_THRESHOLD = 0.40

# LM Studio API endpoint (local)
LMSTUDIO_URL = "http://localhost:1234/v1/chat/completions"
LMSTUDIO_MODEL = "meta-llama-3.1-8b-instruct"

# ============================================================
# 2. LOAD MODELS
# ============================================================

print("--- SYSTEM STARTUP ---")

# 1. Embedding Model
print("1. Loading Embedding Model…")
embedder = SentenceTransformer("all-MiniLM-L6-v2")

# 2. Qdrant Client
print(f"2. Connecting to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}…")
try:
    qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    qdrant.get_collections()
    print("   ✔ Connected to Qdrant.\n")
except Exception as e:
    print("   ❌ Qdrant Connection Failed:", e)
    qdrant = None

print("--- STARTUP COMPLETE ---\n")


# ============================================================
# 3. FUNCTIONS: LM STUDIO GPU LLM
# ============================================================

def lm_studio_generate(system_prompt, user_prompt):
    """
    Sends prompt to LM Studio (GPU accelerated local API).
    """
    try:
        response = requests.post(
            LMSTUDIO_URL,
            json={
                "model": LMSTUDIO_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 400,
                "stream": False
            }
        )

        if response.status_code != 200:
            print("LM Studio API Error:", response.text)
            return "Error: LLM request failed."

        data = response.json()
        return data["choices"][0]["message"]["content"]

    except Exception as e:
        return f"LM Studio Connection Error: {str(e)}"


# ============================================================
# 4. QDRANT SEMANTIC SEARCH
# ============================================================

def find_relevant_documents(prompt: str):
    """Encodes prompt + searches Qdrant."""
    if not qdrant:
        return []

    embed = embedder.encode(prompt).tolist()


    try:
        results = qdrant.query_points(
            collection_name=COLLECTION_NAME,
            query=embed,
            with_payload=True,
            with_vectors=False
        )

        hits = results.points
        docs = []

        print(hits)

        for h in hits:
            payload = h.payload or {}
            docs.append({
                "document_name": payload.get("document", "Unknown"),
                "page_number": payload.get("page_number", 0),
                "reference": payload.get("text", ""),
                "similarity": h.score
            })

        # Apply threshold filter
        return [d for d in docs if d["similarity"] >= RELEVANCE_THRESHOLD]

    except Exception as e:
        print("Qdrant Error:", e)
        return []


# ============================================================
# 5. CORE LOGIC
# ============================================================

def generate_response_logic(prompt):
    docs = find_relevant_documents(prompt)

    if docs:
        context = "\n\n".join(
            f"[{d['document_name']} Pg {d['page_number']}]\n{d['reference']}"
            for d in docs
        )

        system_prompt = f"""
You are a Network Security Tutor. 
Use ONLY the CONTEXT to answer. Do NOT hallucinate. Do NOT duplicate content.
CONTEXT:
{context}
"""

        response = lm_studio_generate(system_prompt, prompt)

        sources = "\n".join(
            f"📄 {d['document_name']} (Pg {d['page_number']}) — Score: {d['similarity']:.2f}"
            for d in docs
        )

        return response, sources

    # No docs → Web search
    snippet, src = web_search(prompt)
    return snippet, src


def web_search(query):
    """Perform a web search using SerpAPI."""
    url = "https://serpapi.com/search"
    params = {
        "q": query,
        "api_key": SERPAPI_API_KEY,
        "engine": "google",
        "num": 1
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        search_results = response.json().get('organic_results', [])
        # Extract the title and snippet from the search results
        message = ""
        for result in search_results:
            message += f"{result['title']}-[URL:{result['link']}]\n"
            data = f"{result['snippet']}\n"
        return [data, message]
    else:
        print("Error with web search API:", response.status_code)
        return ["Internet Search Failure.", "Error"]


# ============================================================
# 6. FASTAPI ROUTES
# ============================================================

class QueryRequest(BaseModel):
    prompt: str

class QueryResponse(BaseModel):
    response: str
    source: str


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return HTMLResponse(render_template("index.html", prompt="", response="", source=""))


@app.post("/query", response_model=QueryResponse)
def api_query(req: QueryRequest):
    response, source = generate_response_logic(req.prompt)
    return QueryResponse(response=response, source=source)


@app.post("/query-form", response_class=HTMLResponse)
def form_query(request: Request, prompt: str = Form(...)):
    response, source = generate_response_logic(prompt)
    html = render_template("index.html", prompt=prompt, response=response, source=source)
    return HTMLResponse(html)


if __name__ == "__main__":
    import uvicorn
    print("🚀 Server running on http://127.0.0.1:7860")
    uvicorn.run(app, host="127.0.0.1", port=7860)
