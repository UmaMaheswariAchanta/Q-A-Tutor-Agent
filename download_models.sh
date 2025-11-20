#!/bin/bash
set -e

echo "======================================"
echo "  Downloading GGUF Models for LMStudio"
echo "======================================"

# Install huggingface_hub if not present
echo ""
echo "[1/4] Installing dependencies..."
pip install -q huggingface_hub

# Create directory structure
echo ""
echo "[2/4] Creating models directory structure..."
mkdir -p models/lmstudio-community

# Download Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf (4.7GB)
echo ""
echo "[3/4] Downloading Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf (4.7GB)..."
echo "This may take several minutes depending on your connection..."
python3 << EOF
from huggingface_hub import hf_hub_download
import os

try:
    print("  → Downloading from lmstudio-community...")
    hf_hub_download(
        repo_id="lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF",
        filename="Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
        local_dir="models/lmstudio-community",
        local_dir_use_symlinks=False
    )
    print("  ✓ Meta-Llama model downloaded successfully!")
except Exception as e:
    print(f"  ✗ Error downloading Meta-Llama model: {e}")
    exit(1)
EOF

# Download Phi-3 models
echo ""
echo "[4/4] Downloading Phi-3 models..."
python3 << EOF
from huggingface_hub import hf_hub_download
import shutil
import os

# Download Phi-3 Q3 model (1.9GB)
try:
    print("  → Downloading Phi-3-mini Q3 (1.9GB)...")
    q3_path = hf_hub_download(
        repo_id="bartowski/Phi-3-mini-4k-instruct-GGUF",
        filename="Phi-3-mini-4k-instruct-Q3_K_M.gguf",
        local_dir="models/temp"
    )
    # Move to correct location with correct name
    shutil.move(
        "models/temp/Phi-3-mini-4k-instruct-Q3_K_M.gguf",
        "models/lmstudio-community/Phi-3-mini-4k-instruct-q3.gguf"
    )
    print("  ✓ Phi-3 Q3 model downloaded successfully!")
except Exception as e:
    print(f"  ✗ Error downloading Phi-3 Q3: {e}")
    exit(1)

# Download Phi-3 Q4 model (2.3GB)
try:
    print("  → Downloading Phi-3-mini Q4 (2.3GB)...")
    q4_path = hf_hub_download(
        repo_id="microsoft/Phi-3-mini-4k-instruct-gguf",
        filename="Phi-3-mini-4k-instruct-q4.gguf",
        local_dir="models/temp"
    )
    # Move to correct location
    shutil.move(
        "models/temp/Phi-3-mini-4k-instruct-q4.gguf",
        "models/lmstudio-community/Phi-3-mini-4k-instruct-q4.gguf"
    )
    print("  ✓ Phi-3 Q4 model downloaded successfully!")
except Exception as e:
    print(f"  ✗ Error downloading Phi-3 Q4: {e}")
    exit(1)

# Cleanup temp directory
import shutil
if os.path.exists("models/temp"):
    shutil.rmtree("models/temp")
    print("  ✓ Cleaned up temporary files")
EOF

echo ""
echo "======================================"
echo "  ✓ All models downloaded successfully!"
echo "======================================"
echo ""
echo "Models location:"
echo "  models/lmstudio-community/"
echo "    ├── Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
echo "    ├── Phi-3-mini-4k-instruct-q3.gguf"
echo "    └── Phi-3-mini-4k-instruct-q4.gguf"
echo ""
