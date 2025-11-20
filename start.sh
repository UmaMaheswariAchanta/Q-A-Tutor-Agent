#!/bin/bash
set -e

echo "======================================"
echo "  Starting Q&A Tutor Agent Deployment"
echo "======================================"

# Step 1: Download models
echo ""
echo "Step 1: Downloading GGUF models..."
bash download_models.sh

# Step 2: Start Qdrant (if not already running)
echo ""
echo "Step 2: Checking Qdrant..."
if ! curl -s http://localhost:6333 > /dev/null 2>&1; then
    echo "  ⚠ Qdrant not detected at localhost:6333"
    echo "  Please ensure Qdrant is running or use cloud Qdrant:"
    echo "  - Docker: docker run -p 6333:6333 qdrant/qdrant"
    echo "  - Cloud: https://cloud.qdrant.io/"
else
    echo "  ✓ Qdrant is running"
fi

# Step 3: Start the application
echo ""
echo "Step 3: Starting FastAPI application..."
PORT=${PORT:-8000}
echo "  → Server will run on http://0.0.0.0:$PORT"
uvicorn Scripts.unified_app:app --host 0.0.0.0 --port $PORT
