# scripts/init_qdrant.py

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

def initialize_qdrant():
    # Connect to Qdrant
    qdrant_client = QdrantClient(host="localhost", port=6333)

    # Define and create a collection with vector configuration
    qdrant_client.recreate_collection(
        collection_name="network_security_docs",
        vectors_config=VectorParams(size=384, distance=Distance.COSINE)
    )

    print("Qdrant collection 'network_security_knowledge' initialized successfully.")

if __name__ == "__main__":
    initialize_qdrant()
