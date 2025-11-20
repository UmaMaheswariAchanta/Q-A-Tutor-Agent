import os
from pathlib import Path
import requests
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from pydantic import BaseModel
import random
import json
import re

# ============================================================
# FASTAPI SETUP
# ============================================================
app = FastAPI(title="Network Security Tutor - Unified Application")

# Paths
script_dir = Path(__file__).parent
project_root = script_dir.parent
templates_dir = project_root / "templates"

# Template Engine
jinja_env = Environment(
    loader=FileSystemLoader(str(templates_dir)),
    autoescape=select_autoescape(['html', 'xml'])
)

def render_template(name, **kwargs):
    return jinja_env.get_template(name).render(**kwargs)

# Configuration
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "network_security_docs"
RELEVANCE_THRESHOLD = 0.40
NUM_QUESTIONS = 5

# LM Studio API endpoint (local)
LMSTUDIO_URL = "http://localhost:1234/v1/chat/completions"
LMSTUDIO_MODEL = "meta-llama-3.1-8b-instruct"

SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY", "0296b30af4db54f0c40dfac526966c93ef22816317822c3935bfec0d614adfe4")

# ============================================================
# LOAD MODELS
# ============================================================

print("--- SYSTEM STARTUP ---")

# 1. Embedding Model for Chatbot
print("1. Loading Embedding Model for Chatbot…")
embedder_chatbot = SentenceTransformer("all-MiniLM-L6-v2")

# 2. Embedding Model for Quiz
print("2. Loading Embedding Model for Quiz…")
embedder_quiz = SentenceTransformer("multi-qa-MiniLM-L6-cos-v1")

# 3. Qdrant Client
print(f"3. Connecting to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}…")
try:
    qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    qdrant.get_collections()
    print("   ✔ Connected to Qdrant.\n")
except Exception as e:
    print("   ❌ Qdrant Connection Failed:", e)
    qdrant = None

print("--- STARTUP COMPLETE ---\n")

# ============================================================
# LM STUDIO FUNCTIONS
# ============================================================

def lm_studio_generate(system_prompt, user_prompt, temperature=0.1, max_tokens=400):
    """Sends prompt to LM Studio (GPU accelerated local API)."""
    try:
        response = requests.post(
            LMSTUDIO_URL,
            json={
                "model": LMSTUDIO_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ] if system_prompt else [{"role": "user", "content": user_prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens,
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
# CHATBOT FUNCTIONS
# ============================================================

def find_relevant_documents(prompt: str):
    """Encodes prompt + searches Qdrant."""
    if not qdrant:
        return []

    embed = embedder_chatbot.encode(prompt).tolist()

    try:
        results = qdrant.query_points(
            collection_name=COLLECTION_NAME,
            query=embed,
            with_payload=True,
            with_vectors=False
        )

        hits = results.points
        docs = []

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
        message = ""
        for result in search_results:
            message += f"{result['title']}-[URL:{result['link']}]\n"
            data = f"{result['snippet']}\n"
        return [data, message]
    else:
        print("Error with web search API:", response.status_code)
        return ["Internet Search Failure.", "Error"]


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

# ============================================================
# QUIZ FUNCTIONS
# ============================================================

QUESTION_TYPES = [
    "true_false",
    "multiple_choice",
    "multiple_answer"
]

def lmstudio_generate(prompt):
    """Generate response using LM Studio for quiz."""
    try:
        resp = requests.post(
            LMSTUDIO_URL,
            json={
                "model": LMSTUDIO_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.55,
                "max_tokens": 350
            },
            timeout=30
        ).json()
        return resp["choices"][0]["message"]["content"]
    except Exception as e:
        print("LM Studio ERROR:", e)
        return None


def clean_json(text):
    """Extract clean JSON from LLM."""
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        try:
            return json.loads(m.group())
        except:
            return None
    return None


def get_random_topic():
    """Extract topics from Qdrant payloads."""
    try:
        items, _ = qdrant.scroll(
            collection_name=COLLECTION_NAME,
            with_payload=True,
            limit=200
        )
        topics = set()
        for p in items:
            md = p.payload
            if md and "topic" in md:
                topics.add(md["topic"])
        return random.choice(list(topics)) if topics else "network security"
    except:
        return "network security"


def generate_question(topic=None):
    if not topic:
        topic = get_random_topic()

    qtype = random.choice(QUESTION_TYPES)

    prompt = f"""
You are a cybersecurity exam expert.
Generate ONE question of type "{qtype}" on topic "{topic}".
Reply in VALID JSON ONLY.

RULES:
True/False JSON:
{{
  "question": "...",
  "type": "true_false",
  "options": ["True", "False"],
  "correct_answer": "True" or "False",
  "explanation": "..."
}}

Multiple Choice JSON:
{{
  "question": "...",
  "type": "multiple_choice",
  "options": ["A", "B", "C", "D"],
  "correct_answer": "<exact option text>",
  "explanation": "..."
}}

Multiple Answer JSON:
{{
  "question": "...",
  "type": "multiple_answer",
  "options": ["A", "B", "C", "D"],
  "correct_answers": ["...", "..."],
  "explanation": "..."
}}

IMPORTANT:
- OUTPUT JSON ONLY.
- No markdown.
- No text outside JSON.
"""

    raw = lmstudio_generate(prompt)
    if not raw:
        return fallback_question()

    data = clean_json(raw)
    if not data:
        return fallback_question()

    # FIX FORMATS
    if data["type"] == "true_false":
        data["options"] = ["True", "False"]

    if data["type"] in ["multiple_choice", "multiple_answer"]:
        if "options" not in data or len(data["options"]) != 4:
            data["options"] = ["A", "B", "C", "D"]

    data.setdefault("explanation", "")

    return data


def fallback_question():
    return {
        "question": "Error generating question.",
        "type": "true_false",
        "options": ["True", "False"],
        "correct_answer": "True",
        "explanation": ""
    }


def grade_answer(user_answer, correct, qtype, explanation):
    if qtype == "multiple_answer":
        if isinstance(user_answer, list):
            user_answers = [str(x).strip() for x in user_answer if isinstance(x, str) and x.strip()]
        elif isinstance(user_answer, str):
            user_answers = [x.strip() for x in user_answer.split(",") if x.strip()]
        else:
            user_answers = []

        correct_answers = [str(x).strip() for x in correct] if isinstance(correct, list) else []

        user_set = {x.lower() for x in user_answers}
        correct_set = {x.lower() for x in correct_answers}

        true_positive = len(user_set & correct_set)
        false_positive = len(user_set - correct_set)
        total_correct = len(correct_set) or 1

        partial_ratio = true_positive / total_correct
        penalty = false_positive / total_correct
        partial_score = max(0.0, round(partial_ratio - penalty, 2))

        correct_flag = user_set == correct_set and len(user_set) == len(correct_set)

        display_user = ", ".join(user_answers) if user_answers else "No answer provided"
        display_correct = ", ".join(correct_answers)

        return {
            "correct": correct_flag,
            "score": 1.0 if correct_flag else partial_score,
            "partial_score": 1.0 if correct_flag else partial_score,
            "correct_answer": display_correct,
            "user_answer": display_user,
            "explanation": explanation
        }

    answer_text = (user_answer or "").strip()
    correct_text = (correct or "").strip()
    correct_flag = answer_text.lower() == correct_text.lower()

    return {
        "correct": correct_flag,
        "score": 1.0 if correct_flag else 0.0,
        "correct_answer": correct_text,
        "user_answer": answer_text if answer_text else "No answer provided",
        "explanation": explanation
    }

# ============================================================
# ROUTES
# ============================================================

class QueryRequest(BaseModel):
    prompt: str

class QueryResponse(BaseModel):
    response: str
    source: str


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return HTMLResponse(render_template("unified.html", active_tab="home", prompt="", response="", source="", quiz=[], results=None))


@app.get("/chatbot", response_class=HTMLResponse)
def chatbot_page(request: Request):
    return HTMLResponse(render_template("unified.html", active_tab="chatbot", prompt="", response="", source="", quiz=[], results=None))


@app.get("/quiz", response_class=HTMLResponse)
def quiz_page(request: Request):
    return HTMLResponse(render_template("unified.html", active_tab="quiz", prompt="", response="", source="", quiz=[], results=None))


@app.post("/query", response_model=QueryResponse)
def api_query(req: QueryRequest):
    response, source = generate_response_logic(req.prompt)
    return QueryResponse(response=response, source=source)


@app.post("/query-form", response_class=HTMLResponse)
def form_query(request: Request, prompt: str = Form(...)):
    response, source = generate_response_logic(prompt)
    html = render_template("unified.html", active_tab="chatbot", prompt=prompt, response=response, source=source, quiz=[], results=None)
    return HTMLResponse(html)


@app.post("/generate", response_class=HTMLResponse)
async def generate_quiz(request: Request, topic: str = Form(None)):
    quiz = [generate_question(topic) for _ in range(NUM_QUESTIONS)]
    html = render_template("unified.html", active_tab="quiz", prompt="", response="", source="", quiz=quiz, results=None)
    return HTMLResponse(html)


@app.post("/submit-quiz", response_class=HTMLResponse)
async def submit_quiz(request: Request):
    form = await request.form()
    results = []

    for i in range(1, NUM_QUESTIONS + 1):
        qtype = form.get(f"type_{i}")
        if not qtype:
            continue

        question = form.get(f"question_{i}")
        explanation = form.get(f"explanation_{i}")

        if qtype == "multiple_answer":
            user_answer = form.getlist(f"answer_{i}")
            correct = json.loads(form.get(f"correct_{i}"))
        else:
            user_answer = form.get(f"answer_{i}", "")
            correct = form.get(f"correct_{i}")

        graded = grade_answer(user_answer, correct, qtype, explanation)
        graded["question"] = question
        results.append(graded)

    html = render_template("unified.html", active_tab="quiz", prompt="", response="", source="", quiz=[], results=results)
    return HTMLResponse(html)


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    import uvicorn
    print("🚀 Unified Server running on http://127.0.0.1:7860")
    uvicorn.run(app, host="127.0.0.1", port=7860)

