from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sentence_transformers import SentenceTransformer
import chromadb
from gpt4all import GPT4All
import requests
from pydantic import BaseModel
import os
from pathlib import Path

# Initialize FastAPI app
app = FastAPI(title="Q & A Tutor Agent")

# Setup templates directory - handle both running from Scripts/ and root directory
script_dir = Path(__file__).parent
project_root = script_dir.parent
templates_dir = project_root / "templates"

# Initialize Jinja2 environment
jinja_env = Environment(
    loader=FileSystemLoader(str(templates_dir)),
    autoescape=select_autoescape(['html', 'xml'])
)

def render_template(template_name: str, **kwargs):
    """Render a Jinja2 template."""
    template = jinja_env.get_template(template_name)
    return template.render(**kwargs)

# Load the embedding model
embedder = SentenceTransformer("all-MiniLM-L12-v2")

# Connect to ChromaDB (persistent storage)
# Store database in project root, not Scripts directory
chroma_db_path = project_root / "chroma_db"
client = chromadb.PersistentClient(path=str(chroma_db_path))
collection = client.get_or_create_collection(
    name="network_security_knowledge",
    metadata={"hnsw:space": "cosine"}
)

# Load the GPT4All model
model_path = "Meta-Llama-3-8B-Instruct.Q4_0.gguf"  # Update this path if needed
gpt4all_model = GPT4All(model_path)

# Get SERPAPI_API_KEY from environment variable or use default
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY", "7fa7214ef761e09c624ba83150a6881f0238327672d3fe4023bc65610c566cc8")

relevance_threshold = 0.4  # choose relevance threshold to improve the output


class QueryRequest(BaseModel):
    prompt: str


class QueryResponse(BaseModel):
    response: str
    source: str


def find_relevant_document(prompt):
    question_embedding = embedder.encode([prompt])[0].tolist()

    # Perform a search in the ChromaDB database
    # Query returns results sorted by similarity (distance)
    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=10,  # Get top 10 results
    )

    # Prepare the output
    relevant_pages = []
    
    # ChromaDB returns results in a different format
    # results contains: ids, distances, metadatas, documents
    if results['ids'] and len(results['ids'][0]) > 0:
        for i in range(len(results['ids'][0])):
            # ChromaDB uses distance (lower is better), we can convert to similarity score
            # For cosine distance: similarity = 1 - distance
            distance = results['distances'][0][i]
            similarity_score = 1 - distance  # Convert distance to similarity
            
            if similarity_score >= relevance_threshold:
                metadata = results['metadatas'][0][i]
                document_text = results['documents'][0][i]
                
                relevant_pages.append({
                    "document_name": metadata.get("document", "Unknown"),
                    "page_number": metadata.get("page_number", 0),
                    "reference": metadata.get("text", document_text[:500])  # Use stored reference or first 500 chars
                })

    return relevant_pages


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


def generate_response(prompt):
    # Find the relevant-documents
    relevant_pages = find_relevant_document(prompt)

    if relevant_pages:
        context_prompt = f"Answer the following question '{prompt}'\n\n from the below Context:\n"
        for i in relevant_pages:
            context_prompt += f"{i['reference']}\n\n"
        response = gpt4all_model.generate(context_prompt)
        source = "\n".join([f"Document: {page['document_name']}, Page: {page['page_number']}\nReference: {page['reference']}\n" for page in relevant_pages])
    else:
        source = "No relevant information found in the documents, Searching from Internet\n"
        resp1 = web_search(prompt)
        response = resp1[0]
        source += resp1[1]

    return response, source


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serve the main chat interface."""
    html_content = render_template("index.html", prompt="", response="", source="")
    return HTMLResponse(content=html_content)


@app.post("/query", response_model=QueryResponse)
async def query_chatbot(request: QueryRequest):
    """API endpoint for querying the chatbot."""
    response, source = generate_response(request.prompt)
    return QueryResponse(response=response, source=source)


@app.post("/query-form", response_class=HTMLResponse)
async def query_chatbot_form(request: Request, prompt: str = Form(...)):
    """Handle form submission from the web interface."""
    response, source = generate_response(prompt)
    html_content = render_template("index.html", prompt=prompt, response=response, source=source)
    return HTMLResponse(content=html_content)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=7860)
