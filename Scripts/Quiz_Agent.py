from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
import requests
import random
import json
import re
from pathlib import Path

# ============================================================
# FASTAPI
# ============================================================
app = FastAPI(title="Quiz Agent (LMStudio + Qdrant + 4 Question Types)")

NUM_QUESTIONS = 5

# ============================================================
# PATH + TEMPLATE
# ============================================================
script_dir = Path(__file__).parent.parent
templates_dir = script_dir / "templates"

jinja_env = Environment(
    loader=FileSystemLoader(str(templates_dir)),
    autoescape=select_autoescape(['html', 'xml'])
)

def render_template(name, **kwargs):
    return jinja_env.get_template(name).render(**kwargs)

# ============================================================
# EMBEDDINGS + QDRANT
# ============================================================
embedder = SentenceTransformer("multi-qa-MiniLM-L6-cos-v1")
qdrant = QdrantClient(host="localhost", port=6333)
COLLECTION_NAME = "network_security_docs"

# ============================================================
# LM STUDIO CONFIG
# ============================================================
LMSTUDIO_URL = "http://localhost:1234/v1/chat/completions"
LMSTUDIO_MODEL = "meta-llama-3.1-8b-instruct"


# ============================================================
# HELPERS
# ============================================================

QUESTION_TYPES = [
    "true_false",
    "multiple_choice",
    "multiple_answer"
]

def lmstudio_generate(prompt):
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


# ============================================================
# QUESTION GENERATION
# ============================================================

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


# ============================================================
# GRADING
# ============================================================

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

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    html = render_template("quiz.html", quiz=[], results=None)
    return HTMLResponse(html)


@app.post("/generate", response_class=HTMLResponse)
async def generate_quiz(request: Request, topic: str = Form(None)):
    quiz = [generate_question(topic) for _ in range(NUM_QUESTIONS)]
    html = render_template("quiz.html", quiz=quiz, results=None)
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

    html = render_template("quiz.html", quiz=[], results=results)
    return HTMLResponse(html)


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=7860)
