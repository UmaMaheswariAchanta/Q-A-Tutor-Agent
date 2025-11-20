# 🚀 Deploy on RunPod (GPU Deployment Guide)

RunPod is the best platform for deploying the Q&A Tutor Agent with local LLMs (GGUF models).
You get a full GPU, persistent storage, and a public URL for your application.

Follow the steps below to deploy your model:

---

## 1️⃣ Create a GPU Pod

1. Go to: https://www.runpod.io/console/pods
2. Click **+ Deploy**
3. Choose a GPU template:
   - **RTX 4090** (best performance)
   - **RTX 3090 / A4000 / 3080** (budget)
4. Select **runpod/pytorch:latest** or **runpod/ubuntu:latest** template
5. Set container disk to **30–50 GB**
6. Click **Deploy Pod**

Wait until the pod is in **Running** state.

---

## 2️⃣ Open Terminal

1. Click **Connect**
2. Choose **Open Web Terminal**

This opens a full Ubuntu terminal inside your GPU container.

---

## 3️⃣ Clone Your Repository

Inside the terminal, run:

```bash
git clone https://github.com/UmaMaheswariAchanta/Q-A-Tutor-Agent.git
cd Q-A-Tutor-Agent
```

---

## 4️⃣ Install Dependencies

```bash
# Update system
apt-get update && apt-get install -y wget curl

# Install Python dependencies
pip install -r requirements.txt
```

---

## 5️⃣ Download Models

Run the automated model download script:

```bash
bash download_models.sh
```

This will download:
- Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf (4.7GB)
- Phi-3-mini-4k-instruct-q3.gguf (1.9GB)
- Phi-3-mini-4k-instruct-q4.gguf (2.3GB)

**Time:** ~10-15 minutes depending on connection

---

## 6️⃣ Start Qdrant Vector Database

```bash
# Install Docker (if not present)
apt-get install -y docker.io

# Start Qdrant
docker run -d -p 6333:6333 -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  --name qdrant \
  qdrant/qdrant
```

---

## 7️⃣ Initialize Qdrant with Data

```bash
# Create collection
python Scripts/initialise_qdrant.py

# Insert documents
python Scripts/Data_insertion_qdrant.py
```

---

## 8️⃣ Start LM Studio (GPU Inference)

```bash
# Install LM Studio CLI (or use llama.cpp directly)
# For this guide, we'll use llama.cpp for GPU inference

# Clone llama.cpp
cd ~
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# Build with CUDA support
make LLAMA_CUBLAS=1

# Start server with your model
./server \
  -m /workspace/Q-A-Tutor-Agent/models/lmstudio-community/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf \
  -c 4096 \
  --host 0.0.0.0 \
  --port 1234 \
  -ngl 33
```

Keep this terminal running.

---

## 9️⃣ Start the FastAPI Application

Open a **new terminal** and run:

```bash
cd Q-A-Tutor-Agent

# Start the app
uvicorn Scripts.unified_app:app --host 0.0.0.0 --port 8000
```

---

## 🔟 Expose Public URL

### Option A: Using RunPod's Built-in Port Forwarding

1. In RunPod Console, click your pod
2. Go to **HTTP Service [Port 8000]**
3. Copy the public URL (e.g., `https://xxxxx-8000.proxy.runpod.net`)

### Option B: Using ngrok

```bash
# Install ngrok
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar -xvzf ngrok-v3-stable-linux-amd64.tgz

# Start tunnel
./ngrok http 8000
```

Copy the `https://` URL from ngrok output.

---

## ✅ Test Your Deployment

Visit your public URL:
```
https://xxxxx-8000.proxy.runpod.net
```

You should see the Q&A Tutor Agent interface!

---

## 🔧 Troubleshooting

### Models not loading
```bash
# Check if models exist
ls -lh models/lmstudio-community/

# Re-run download script
bash download_models.sh
```

### Qdrant connection failed
```bash
# Check if Qdrant is running
curl http://localhost:6333/health

# Restart Qdrant
docker restart qdrant
```

### LLM server not responding
```bash
# Check if llama.cpp server is running
curl http://localhost:1234/v1/models

# Restart with more verbose logging
./server -m /path/to/model.gguf --host 0.0.0.0 --port 1234 -ngl 33 --verbose
```

### GPU not being used
```bash
# Check GPU availability
nvidia-smi

# Ensure llama.cpp was built with CUDA
cd ~/llama.cpp
make clean
make LLAMA_CUBLAS=1
```

---

## 📊 Performance Tips

1. **Use RTX 4090** for best performance (40-60 tokens/sec)
2. **Increase context size** if needed: `-c 8192`
3. **Adjust GPU layers**: `-ngl 35` (all layers on GPU)
4. **Monitor GPU usage**: `watch -n 1 nvidia-smi`

---

## 💰 Cost Estimation

| GPU | Cost/hour | Recommended For |
|-----|-----------|-----------------|
| RTX 4090 | $0.69/hr | Production, best performance |
| RTX 3090 | $0.49/hr | Development, good performance |
| RTX 3080 | $0.29/hr | Testing, budget option |

**Monthly cost for 24/7 uptime:**
- RTX 4090: ~$500/month
- RTX 3090: ~$350/month
- RTX 3080: ~$210/month

---

## 🔄 Auto-Start on Pod Restart

Create a startup script:

```bash
# Create startup script
cat > /workspace/start.sh << 'EOF'
#!/bin/bash
cd /workspace/Q-A-Tutor-Agent

# Start Qdrant
docker start qdrant || docker run -d -p 6333:6333 -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  --name qdrant qdrant/qdrant

# Start LLM server
cd ~/llama.cpp
./server \
  -m /workspace/Q-A-Tutor-Agent/models/lmstudio-community/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf \
  -c 4096 --host 0.0.0.0 --port 1234 -ngl 33 &

# Wait for LLM server to start
sleep 10

# Start FastAPI app
cd /workspace/Q-A-Tutor-Agent
uvicorn Scripts.unified_app:app --host 0.0.0.0 --port 8000
EOF

chmod +x /workspace/start.sh
```

Run on pod start:
```bash
/workspace/start.sh
```

---

## 📚 Additional Resources

- [RunPod Documentation](https://docs.runpod.io/)
- [llama.cpp GitHub](https://github.com/ggerganov/llama.cpp)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Main Deployment Guide](./DEPLOYMENT.md)

---

## 🆘 Support

If you encounter issues:
1. Check [Troubleshooting](#-troubleshooting) section above
2. Review [Main Deployment Guide](./DEPLOYMENT.md)
3. Open an issue: https://github.com/UmaMaheswariAchanta/Q-A-Tutor-Agent/issues

---

**Happy GPU-powered LLM deployment! 🚀**
