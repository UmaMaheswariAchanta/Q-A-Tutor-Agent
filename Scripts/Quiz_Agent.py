from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sentence_transformers import SentenceTransformer
import chromadb
from gpt4all import GPT4All
import os
import random
import json
import re
from difflib import SequenceMatcher
from pathlib import Path

# -------------------------
# INITIAL SETUP
# -------------------------
app = FastAPI(title="Network Security Quiz Agent")

NUM_QUESTIONS = 5  # number of questions per quiz

# Paths
script_dir = Path(__file__).parent.parent
templates_dir = script_dir / "templates"
chroma_db_path = script_dir / "chroma_db"

# Jinja2 templates
jinja_env = Environment(
    loader=FileSystemLoader(str(templates_dir)),
    autoescape=select_autoescape(['html', 'xml'])
)

def render_template(template_name, **kwargs):
    template = jinja_env.get_template(template_name)
    return template.render(**kwargs)

# Embedding model
embedder = SentenceTransformer("all-MiniLM-L12-v2")

# ChromaDB connection (optional)
client = chromadb.PersistentClient(path=str(chroma_db_path))
collection = client.get_or_create_collection(name="network_security_knowledge")

# GPT4All model
model_path = r"C:\Users\Prudhvi\Desktop\NS_GP1_ondemand_Q-A-main\models\phi-2.Q4_0.gguf"  # update path if needed
gpt4all_model = GPT4All(model_path)

# -------------------------
# HELPER FUNCTIONS
# -------------------------

def get_random_topic():
    """Pick a random topic from ChromaDB metadata"""
    results = collection.get(include=["metadatas"])
    if results and results["metadatas"]:
        topics = [meta.get("topic", "network security") for meta in results["metadatas"]]
        return random.choice(topics)
    return "network security"

def generate_question(topic=None):
    """Generate only MCQ or True/False questions in JSON"""
    if not topic:
        topic = get_random_topic()

    question_type = random.choice(["multiple_choice", "true_false"])

    prompt = f"""
    You are a cybersecurity quiz generator.
    Create one {question_type} question about "{topic}".

    Follow this JSON format exactly:
    {{
      "question": "<Question text>",
      "type": "{question_type}",
      "options": ["<A>", "<B>", "<C>", "<D>"],  # Only for multiple_choice
      "correct_answer": "<Correct answer text>",
      "explanation": "<Brief explanation why this is correct>"
    }}

    - If the question_type is "true_false", give only 'True' and 'False' as options.
    """

    raw_output = gpt4all_model.generate(prompt)

    # Extract JSON from model response
    match = re.search(r"\{.*\}", raw_output, re.DOTALL)
    if match:
        try:
            q_data = json.loads(match.group())
        except json.JSONDecodeError:
            q_data = {"question": "Error generating question", "type": question_type,
                      "options": ["N/A"], "correct_answer": "", "explanation": ""}
    else:
        q_data = {"question": "Error generating question", "type": question_type,
                  "options": ["N/A"], "correct_answer": "", "explanation": ""}

    # Ensure options exist for MCQ, True/False otherwise
    if q_data["type"] == "multiple_choice":
        q_data.setdefault("options", ["A", "B", "C", "D"])
    elif q_data["type"] == "true_false":
        q_data["options"] = ["True", "False"]

    q_data.setdefault("correct_answer", "")
    q_data.setdefault("explanation", "")
    return q_data

def grade_answer(user_answer, correct_answer, question_type, explanation, citation=None):
    """Grade MCQ or True/False by exact match"""
    user_answer_clean = user_answer.strip().lower()
    correct_answer_clean = correct_answer.strip().lower()

    correct = user_answer_clean == correct_answer_clean
    score = 1.0 if correct else 0.0

    feedback = {
        "correct": correct,
        "score": score,
        "correct_answer": correct_answer,
        "explanation": explanation,
    }
    if citation:
        feedback["citation"] = citation
    return feedback

# -------------------------
# ROUTES
# -------------------------

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    html = render_template("quiz.html", quiz=[], results=None)
    return HTMLResponse(html)

@app.post("/generate", response_class=HTMLResponse)
async def generate_quiz(request: Request, topic: str = Form(None)):
    quiz = []
    for _ in range(NUM_QUESTIONS):
        q = generate_question(topic)
        quiz.append(q)
    html = render_template("quiz.html", quiz=quiz, results=None)
    return HTMLResponse(html)

@app.post("/submit-quiz", response_class=HTMLResponse)
async def submit_quiz(request: Request):
    form = await request.form()
    results = []

    for i in range(1, NUM_QUESTIONS + 1):
        user_answer = form.get(f"answer_{i}", "")
        correct_answer = form.get(f"correct_{i}", "")
        question_type = form.get(f"type_{i}", "")
        explanation = form.get(f"explanation_{i}", "")
        citation = form.get(f"citation_{i}", None)
        question_text = form.get(f"question_{i}", "")

        feedback = grade_answer(user_answer, correct_answer, question_type, explanation, citation)
        feedback["user_answer"] = user_answer
        feedback["question"] = question_text
        results.append(feedback)

    html = render_template("quiz.html", quiz=[], results=results)
    return HTMLResponse(html)

# -------------------------
# RUN APP
# -------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=7860)
