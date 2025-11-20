# 🚀 Deployment Guide - Q&A Tutor Agent

This guide covers deploying your Q&A Tutor Agent to various cloud platforms. The models are automatically downloaded during deployment, bypassing GitHub's file size limits.

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Railway Deployment](#railway-deployment)
3. [Render Deployment](#render-deployment)
4. [Azure Deployment](#azure-deployment)
5. [Docker Deployment](#docker-deployment)
6. [Manual Deployment](#manual-deployment)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 Quick Start

### Prerequisites
- Git repository with your code pushed to GitHub
- Models excluded via `.gitignore` (already configured)
- Cloud platform account (Railway/Render/Azure)

### What Happens During Deployment
1. Cloud server pulls code from GitHub (without models)
2. `download_models.sh` runs automatically
3. Models are downloaded to `models/lmstudio-community/`
4. Application starts with all models ready

---

## 🚂 Railway Deployment

Railway offers the simplest deployment with automatic configuration.

### Steps:

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit - deployment ready"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   git push -u origin main
   ```

2. **Deploy to Railway**
   - Go to [railway.app](https://railway.app)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Railway auto-detects `railway.json` and `Procfile`

3. **Configure Environment Variables** (Optional)
   ```
   PORT=8000
   QDRANT_HOST=localhost
   QDRANT_PORT=6333
   ```

4. **Add Qdrant Service** (Required)
   - In Railway dashboard: "New" → "Database" → "Qdrant"
   - Update `QDRANT_HOST` to the internal URL Railway provides

5. **Deploy**
   - Railway automatically builds and deploys
   - Models download on first startup (~10-15 minutes)
   - Access your app at the Railway-provided URL

### Railway Configuration Files
- ✅ `railway.json` - Build & deploy config
- ✅ `Procfile` - Start command

---

## 🎨 Render Deployment

Render provides persistent disk storage, ideal for large models.

### Steps:

1. **Push to GitHub** (same as Railway)

2. **Create Web Service**
   - Go to [render.com](https://render.com)
   - "New" → "Web Service"
   - Connect your GitHub repository

3. **Configure Build Settings**
   ```
   Name: qa-tutor-agent
   Environment: Python 3
   Build Command: pip install -r requirements.txt && bash download_models.sh
   Start Command: uvicorn Scripts.unified_app:app --host 0.0.0.0 --port $PORT
   ```

4. **Add Persistent Disk**
   - Scroll to "Disk"
   - Click "Add Disk"
   - Mount Path: `/opt/render/project/src/models`
   - Size: 20 GB (for all models)

5. **Environment Variables**
   ```
   PYTHON_VERSION=3.11.0
   QDRANT_HOST=localhost
   QDRANT_PORT=6333
   ```

6. **Deploy Qdrant** (Separate Service)
   - "New" → "Web Service"
   - Deploy Qdrant: `docker.io/qdrant/qdrant`
   - Update main app's `QDRANT_HOST` to Qdrant's internal URL

7. **Deploy**
   - Click "Create Web Service"
   - First build downloads models (~15-20 minutes)
   - Subsequent deploys use cached models

### Render Configuration Files
- ✅ `render.yaml` - Complete service definition
- ✅ Can use instead of manual configuration

---

## ☁️ Azure Deployment

Deploy to Azure App Service or Container Instances.

### Option A: Azure App Service

1. **Install Azure CLI**
   ```bash
   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
   az login
   ```

2. **Create Resources**
   ```bash
   # Create resource group
   az group create --name qa-tutor-rg --location eastus

   # Create App Service plan (Linux)
   az appservice plan create \
     --name qa-tutor-plan \
     --resource-group qa-tutor-rg \
     --is-linux \
     --sku B2

   # Create web app
   az webapp create \
     --resource-group qa-tutor-rg \
     --plan qa-tutor-plan \
     --name qa-tutor-app \
     --runtime "PYTHON:3.11"
   ```

3. **Configure Startup**
   ```bash
   az webapp config set \
     --resource-group qa-tutor-rg \
     --name qa-tutor-app \
     --startup-file "bash start.sh"
   ```

4. **Deploy Code**
   ```bash
   # Using local Git
   az webapp deployment source config-local-git \
     --name qa-tutor-app \
     --resource-group qa-tutor-rg

   git remote add azure <GIT_URL_FROM_ABOVE>
   git push azure main
   ```

5. **Add Qdrant**
   - Deploy Qdrant as Azure Container Instance
   - Or use [Qdrant Cloud](https://cloud.qdrant.io/)
   - Update environment variables

### Option B: Azure Container Instances

1. **Build and Push Docker Image**
   ```bash
   # Build image
   docker build -t qa-tutor-agent .

   # Tag for Azure Container Registry
   docker tag qa-tutor-agent <registry>.azurecr.io/qa-tutor-agent

   # Push to ACR
   docker push <registry>.azurecr.io/qa-tutor-agent
   ```

2. **Deploy Container**
   ```bash
   az container create \
     --resource-group qa-tutor-rg \
     --name qa-tutor-container \
     --image <registry>.azurecr.io/qa-tutor-agent \
     --cpu 2 \
     --memory 8 \
     --ports 8000
   ```

---

## 🐳 Docker Deployment

Use Docker Compose for local or self-hosted deployment.

### Local Development

1. **Start All Services**
   ```bash
   docker-compose up --build
   ```

   This starts:
   - Qdrant (port 6333)
   - Your FastAPI app (port 8000)

2. **Initialize Qdrant Data** (First time only)
   ```bash
   # In a new terminal
   docker-compose exec app python Scripts/initialise_qdrant.py
   docker-compose exec app python Scripts/Data_insertion_qdrant.py
   ```

3. **Access Application**
   - App: http://localhost:8000
   - Qdrant: http://localhost:6333

### Production Docker

1. **Build Image**
   ```bash
   docker build -t qa-tutor-agent .
   ```

2. **Run Container**
   ```bash
   docker run -d \
     -p 8000:8000 \
     -e QDRANT_HOST=<qdrant-host> \
     -e QDRANT_PORT=6333 \
     --name qa-tutor \
     qa-tutor-agent
   ```

---

## 🔧 Manual Deployment (VPS/Ubuntu)

For self-hosted VPS (DigitalOcean, Linode, etc.)

### Steps:

1. **SSH into Server**
   ```bash
   ssh user@your-server-ip
   ```

2. **Install Dependencies**
   ```bash
   sudo apt update
   sudo apt install -y python3.11 python3-pip git curl
   ```

3. **Clone Repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
   cd YOUR_REPO
   ```

4. **Install Python Packages**
   ```bash
   pip3 install -r requirements.txt
   ```

5. **Download Models**
   ```bash
   bash download_models.sh
   ```

6. **Install & Start Qdrant**
   ```bash
   docker run -d -p 6333:6333 -p 6334:6334 \
     -v $(pwd)/qdrant_storage:/qdrant/storage \
     qdrant/qdrant
   ```

7. **Start Application**
   ```bash
   # Using start.sh (recommended)
   bash start.sh

   # Or directly
   uvicorn Scripts.unified_app:app --host 0.0.0.0 --port 8000
   ```

8. **Setup as Service** (Optional - keeps app running)
   ```bash
   sudo nano /etc/systemd/system/qa-tutor.service
   ```

   Add:
   ```ini
   [Unit]
   Description=Q&A Tutor Agent
   After=network.target

   [Service]
   Type=simple
   User=youruser
   WorkingDirectory=/path/to/your/repo
   ExecStart=/usr/bin/bash /path/to/your/repo/start.sh
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

   Enable:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable qa-tutor
   sudo systemctl start qa-tutor
   ```

---

## 🐛 Troubleshooting

### Models Not Downloading

**Problem:** Script fails to download models

**Solutions:**
```bash
# Check if huggingface_hub is installed
pip install huggingface_hub

# Verify HuggingFace access
python3 -c "from huggingface_hub import hf_hub_download; print('OK')"

# Manual download
python3 << EOF
from huggingface_hub import hf_hub_download
hf_hub_download(
    repo_id="lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF",
    filename="Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
    local_dir="models/lmstudio-community"
)
EOF
```

### Qdrant Connection Failed

**Problem:** `❌ Qdrant Connection Failed`

**Solutions:**
1. Ensure Qdrant is running:
   ```bash
   # Local
   docker run -d -p 6333:6333 qdrant/qdrant

   # Check status
   curl http://localhost:6333/health
   ```

2. Update environment variables:
   ```bash
   export QDRANT_HOST=localhost
   export QDRANT_PORT=6333
   ```

3. Use Qdrant Cloud:
   - Sign up at https://cloud.qdrant.io/
   - Get cluster URL
   - Update `QDRANT_HOST` in code

### Port Already in Use

**Problem:** `Address already in use`

**Solutions:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
uvicorn Scripts.unified_app:app --port 8080
```

### Out of Memory

**Problem:** Server crashes during model download

**Solutions:**
1. Increase server RAM (minimum 8GB recommended)
2. Download models one at a time:
   ```bash
   # Edit download_models.sh to download sequentially
   # Comment out models you don't need immediately
   ```

### LM Studio Connection Error

**Problem:** Cannot connect to LM Studio

**Solutions:**
1. **Local Development:**
   ```bash
   # Start LM Studio GUI
   # Load model: Meta-Llama-3.1-8B-Instruct
   # Enable local server (port 1234)
   ```

2. **Production:**
   ```python
   # Use cloud LLM API instead
   # Update Scripts/unified_app.py:
   LMSTUDIO_URL = "https://your-cloud-llm-api.com/v1/chat/completions"
   ```

---

## 📊 Deployment Checklist

Before deploying, ensure:

- [ ] Code pushed to GitHub
- [ ] `.gitignore` excludes `models/` directory
- [ ] `requirements.txt` is complete
- [ ] `download_models.sh` has execute permissions
- [ ] Environment variables configured
- [ ] Qdrant service available
- [ ] Sufficient disk space (20GB+ recommended)
- [ ] Sufficient RAM (8GB+ recommended)

---

## 🔗 Useful Links

- [Railway Docs](https://docs.railway.app/)
- [Render Docs](https://render.com/docs)
- [Azure App Service](https://docs.microsoft.com/azure/app-service/)
- [Qdrant Cloud](https://cloud.qdrant.io/)
- [HuggingFace Models](https://huggingface.co/models)

---

## 📞 Need Help?

If you encounter issues:
1. Check logs: `docker-compose logs` or platform-specific logs
2. Verify all environment variables are set
3. Ensure models downloaded successfully: `ls -lh models/lmstudio-community/`
4. Test Qdrant connectivity: `curl http://<qdrant-host>:6333/health`

---

**Happy Deploying! 🎉**
