# scripts/initialise_chromadb.py

import chromadb
from pathlib import Path

def initialize_chromadb():
    # Initialize ChromaDB client (persistent storage in ./chroma_db_gpu directory)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    chroma_db_path = project_root / "chroma_db"
    
    client = chromadb.PersistentClient(path=str(chroma_db_path))

    # --- IMPORTANT NOTE ---
    # Using a new collection name avoids the HNSW metadata conflict error.
    collection_name = "network_security_knowledge"

    # Create a clean, optimized collection with cosine similarity
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={
            "hnsw:space": "cosine",                # Higher accuracy graph
        }
    )

    print(f"ChromaDB collection '{collection_name}' initialized successfully.")
    print(f"Collection contains {collection.count()} documents.")

if __name__ == "__main__":
    initialize_chromadb()
