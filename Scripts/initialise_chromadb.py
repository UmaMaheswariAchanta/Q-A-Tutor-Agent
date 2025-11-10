# scripts/initialise_chromadb.py

import chromadb
from pathlib import Path

def initialize_chromadb():
    # Initialize ChromaDB client (persistent storage in ./chroma_db directory)
    # Get the project root directory (parent of Scripts directory)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    chroma_db_path = project_root / "chroma_db"
    
    client = chromadb.PersistentClient(path=str(chroma_db_path))
    
    # Get or create the collection
    # The collection will use cosine distance by default for similarity search
    collection = client.get_or_create_collection(
        name="network_security_knowledge",
        metadata={"hnsw:space": "cosine"}  # Use cosine similarity
    )
    
    print("ChromaDB collection 'network_security_knowledge' initialized successfully.")
    print(f"Collection contains {collection.count()} documents.")

if __name__ == "__main__":
    initialize_chromadb()

