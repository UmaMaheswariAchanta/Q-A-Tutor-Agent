from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance, PointStruct
import os
import uuid
from pathlib import Path

# =============================================
# 1. Load Embedding Model
# =============================================
MODEL_NAME = "all-MiniLM-L6-v2"
print(f"Loading SentenceTransformer model: {MODEL_NAME} ...")
embedder = SentenceTransformer(MODEL_NAME)
EMBED_DIM = embedder.get_sentence_embedding_dimension()
print(f"✔ Model loaded (Embedding dimension = {EMBED_DIM}).\n")

# =============================================
# 2. Connect to Qdrant
# =============================================
print("Connecting to Qdrant (localhost:6333) ...")
qdrant_client = QdrantClient(host="localhost", port=6333)
print("✔ Connected to Qdrant.\n")

collection_name = "network_security_docs"


# =============================================
# Create Qdrant collection if missing
# =============================================
def create_collection():
    collections = qdrant_client.get_collections().collections
    existing = [c.name for c in collections]

    print(f"Existing collections: {existing}")

    if collection_name not in existing:
        print(f"➡ Creating new collection '{collection_name}' ...")
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=EMBED_DIM,
                distance=Distance.COSINE
            )
        )
        print(f"✔ Collection '{collection_name}' created.\n")
    else:
        print(f"✔ Using existing collection '{collection_name}'.\n")


# =============================================
# Extract text from PDF using pypdf
# =============================================
def extract_text_pypdf(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        print(f"   → Total pages: {len(reader.pages)}")

        for page_num, page in enumerate(reader.pages, start=1):
            print(f"   → Extracting Page {page_num}/{len(reader.pages)} ...")

            text = page.extract_text()

            if not text or not text.strip():
                print("     ⚠ Empty page — skipped.\n")
                continue

            yield page_num, text

    except Exception as e:
        print(f"❌ ERROR reading PDF with pypdf: {pdf_path.name} — {e}")
        return


# =============================================
# Process PDFs and insert into Qdrant
# =============================================
def process_pdfs(directory):
    print(f"📁 Searching for PDFs in: {directory}")

    directory = Path(directory)
    if not directory.exists():
        print(f"❌ ERROR: Directory does not exist: {directory}")
        return

    create_collection()

    pdf_files = list(directory.glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF file(s): {[f.name for f in pdf_files]}\n")

    total_pages = 0
    batch_points = []

    for pdf_file in pdf_files:
        print(f"📄 Opening PDF: {pdf_file.name}")

        for page_num, text in extract_text_pypdf(pdf_file):
            total_pages += 1
            print("     ✔ Extracted text. Generating embedding...")

            embedding = embedder.encode(text).tolist()
            point_id = str(uuid.uuid4())

            batch_points.append(
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "document": pdf_file.name,
                        "page_number": page_num,
                        "text": text,
                    }
                )
            )

            print(f"     ✔ Added Page {page_num} to batch.\n")

        print(f"Finished processing PDF: {pdf_file.name}\n")

    # =============================================
    # Batch upload for high speed
    # =============================================
    if batch_points:
        print(f"🚀 Uploading {len(batch_points)} pages in batch...")
        qdrant_client.upsert(collection_name=collection_name, points=batch_points)
        print("✔ Batch upload completed.\n")
    else:
        print("⚠ No valid pages found — nothing to upload.\n")

    print("🎉 COMPLETED")
    print(f"📌 Total pages inserted: {total_pages}")
    print(f"📌 Total documents processed: {len(pdf_files)}\n")


# =============================================
# MAIN
# =============================================
if __name__ == "__main__":
    parent_path = Path(__file__).parent.parent
    pdf_directory = parent_path / "References"

    print("============================================")
    print("🚀 STARTING QDRANT PDF INGESTION PIPELINE 🚀")
    print("============================================\n")

    process_pdfs(pdf_directory)

    print("============================================")
    print("✨ DONE — Qdrant is updated with embeddings ✨")
    print("============================================")
