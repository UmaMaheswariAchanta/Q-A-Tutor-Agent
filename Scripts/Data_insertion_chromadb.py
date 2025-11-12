import pdfplumber
from sentence_transformers import SentenceTransformer
import chromadb
import os
import uuid  # Import UUID module
from pathlib import Path

print("Starting the data insertion process...")

# Initialize the sentence transformer model for embeddings
embedder = SentenceTransformer('all-MiniLM-L12-v2')

print("Sentence transformer model initialized successfully.")

# Connect to ChromaDB (persistent storage)
# Get the project root directory (parent of Scripts directory)
script_dir = Path(__file__).parent
project_root = script_dir.parent
chroma_db_path = project_root / "chroma_db"

client = chromadb.PersistentClient(path=str(chroma_db_path))
collection = client.get_or_create_collection(
    name="network_security_knowledge",
    metadata={"hnsw:space": "cosine"}
)

# Function to extract text from PDF and store it in ChromaDB
def process_pdfs(directory):
    page_texts = []
    embeddings = []
    ids = []
    metadatas = []
    
    # List PDF files in the given directory
    pdf_files = [f for f in os.listdir(directory) if f.lower().endswith('.pdf')]
    
    # Process each PDF
    for pdf_file in pdf_files:
        pdf_path = os.path.join(directory, pdf_file)  # Get full path for the PDF
        
        # Open the PDF using pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            # Iterate over the pages and extract text
            for page_num, page in enumerate(pdf.pages, start=1):
                # Extract text from the page
                text = page.extract_text()
                
                # Skip empty pages
                if not text or text.strip() == "":
                    continue
                
                page_texts.append(text)
                
                # Generate embedding for the text of the page
                embedding = embedder.encode([text])[0].tolist()  # Text embedding as list
                embeddings.append(embedding)
                
                # Generate a unique UUID for each page
                point_id = str(uuid.uuid4())  # Generate a unique UUID
                ids.append(point_id)
                
                # Store metadata
                metadatas.append({
                    "document": pdf_file,
                    "page_number": page_num,
                    "text": text[:500]  # Store the first 500 characters for reference
                })
    
    # Insert all pages into ChromaDB in batches for better performance
    if page_texts:
        # ChromaDB can handle batch inserts efficiently
        collection.add(
            embeddings=embeddings,
            documents=page_texts,  # Full text stored as documents
            metadatas=metadatas,
            ids=ids
        )
        print(f"Processed {len(page_texts)} pages from {len(pdf_files)} documents")
        print(f"Total documents in collection: {collection.count()}")
    else:
        print("No PDF files found to process.")

if __name__ == "__main__":
    # Provide the directory containing the PDFs
    pdf_path = r"C:\Users\Prudhvi\Desktop\NS_GP1_ondemand_Q-A-main\References"
    process_pdfs(pdf_path)

