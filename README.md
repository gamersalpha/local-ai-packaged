# Self-hosted AI Package

**Self-hosted AI Package** is an open, docker compose template that
quickly bootstraps a fully featured Local AI and Low Code development
environment including Ollama for your local LLMs, Open WebUI for an interface to chat with your N8N agents, and Supabase for your database, vector store, and authentication. 

This is Cole's version with a couple of improvements and the addition of Supabase, Open WebUI, Flowise, Neo4j, Langfuse, SearXNG, and Caddy!
Also, the local RAG AI Agent workflows from the video will be automatically in your 
n8n instance if you use this setup instead of the base one provided by n8n!

**IMPORANT**: Supabase has updated a couple environment variables so you may have to add some new default values in your .env that I have in my .env.example if you have had this project up and running already and are just pulling new changes. Specifically, you need to add "POOLER_DB_POOL_SIZE=5" to your .env. This is required if you have had the package running before June 14th.

---

## 🧩 Installation (Simplified & Automated)

The new installation process is fully automated thanks to the included Python setup script.

### 1️⃣ Clone the repository
```bash
git clone -b stable https://https://github.com/gamersalpha/local-ai-packaged/
cd local-ai-packaged
```

### 2️⃣ Generate the environment file automatically

You no longer need to manually edit `.env` — the new `generate_env.py` script will:

- Generate all required environment variables  
- Create secure random passwords and API keys  
- Automatically detect your GPU (NVIDIA / AMD / CPU)  
- Add correct local paths:  
  ```
  LOCAL_AI_BASE_PATH=/volume1/docker/local-ai-packaged-infra
  LOCAL_AI_INFRA_PATH=/volume1/docker/local-ai-packaged-infra/DATAS
  ```

Run the following command for a **fully automated setup**:

```bash
python3 generate_env.py --yes --regen-sensitive --docker
```

This will:
- Create `.env`
- Detect your GPU profile
- Build and start all Docker services automatically
- Display your service access URLs, like:
  ```
  🌐 Services disponibles :
    🧠 Ollama      : http://192.168.1.42:11434
    ⚙️  N8n         : http://192.168.1.42:5678
    📦 Qdrant URL  : http://192.168.1.42:6333
    💬 OpenWebUI   : http://192.168.1.42:3000/
  ```

---

### 3️⃣ Manual setup (optional)
If you prefer to generate the `.env` file without starting Docker right away:
```bash
python3 generate_env.py --yes --regen-sensitive
```

This creates your `.env` only, without running any containers.

---

### 4️⃣ Start services manually (if `.env` is already created)
If you didn’t use `--docker`, you can still launch later using:
```bash
python3 start_services.py --profile gpu-nvidia
```
or
```bash
python3 start_services.py --profile cpu
```

---

### 💡 Notes
- The script generates all secrets using only **letters, numbers, “!” and “?”** (safe for Docker Compose).
- It automatically populates:
  ```bash
  FLOWISE_USERNAME=FLOWISEUSER
  FLOWISE_PASSWORD=<random>
  PG_META_CRYPTO_KEY=<random>
  LOCAL_AI_BASE_PATH=/absolute/path/to/local-ai-packaged-infra
  LOCAL_AI_INFRA_PATH=/absolute/path/to/local-ai-packaged-infra/DATAS
  ```
- If you re-run it, a backup of your previous `.env` will be saved as `.env.bak`.

---

✅ **In short:**
> 💬 One command does everything:
> ```bash
> python3 generate_env.py --yes --regen-sensitive --docker
> ```

---

## Important Links

- [Local AI community](https://thinktank.ottomator.ai/c/local-ai/18)
- [GitHub Kanban board](https://github.com/users/coleam00/projects/2/views/1)
- [Original Local AI Starter Kit](https://github.com/n8n-io/self-hosted-ai-starter-kit)
- [N8N + OpenWebUI Integration](https://openwebui.com/f/coleam/n8n_pipe/)

![n8n.io - Screenshot](https://raw.githubusercontent.com/n8n-io/self-hosted-ai-starter-kit/main/assets/n8n-demo.gif)

Curated by <https://github.com/n8n-io> and <https://github.com/coleam00>

---

## 🧠 What’s included

✅ [**Self-hosted n8n**](https://n8n.io/)  
✅ [**Supabase**](https://supabase.com/)  
✅ [**Ollama**](https://ollama.com/)  
✅ [**Open WebUI**](https://openwebui.com/)  
✅ [**Flowise**](https://flowiseai.com/)  
✅ [**Qdrant**](https://qdrant.tech/)  
✅ [**Neo4j**](https://neo4j.com/)  
✅ [**SearXNG**](https://searxng.org/)  
✅ [**Caddy**](https://caddyserver.com/)  
✅ [**Langfuse**](https://langfuse.com/)

---

## Prerequisites

- [Python](https://www.python.org/downloads/)
- [Git](https://desktop.github.com/)
- [Docker / Docker Desktop](https://www.docker.com/products/docker-desktop/)

---

## ⚡️ Quick Start and Usage

1. Open <http://localhost:5678/> in your browser to set up n8n  
2. Import the included workflow:
   <http://localhost:5678/workflow/vTN9y2dLXqTiDfPT>
3. Configure credentials:
   - **Ollama URL:** `http://ollama:11434`
   - **Postgres:** `Host=db` + credentials from `.env`
   - **Qdrant:** `http://qdrant:6333`
4. Activate the workflow and copy the “Production” webhook URL.
5. Visit <http://localhost:3000/> to configure Open WebUI.

Once up and running:
- n8n is available at **http://localhost:5678/**
- Open WebUI at **http://localhost:3000/**
- Supabase Admin at **http://localhost:54323/** (if enabled)

---

## 🚀 Upgrading

To update everything:
```bash
docker compose -p localai -f docker-compose.yml --profile <profile> down
docker compose -p localai -f docker-compose.yml --profile <profile> pull
python3 start_services.py --profile <profile>
```

---

## 🔧 Troubleshooting

### Supabase
- Remove “@” or special characters in `POSTGRES_PASSWORD`
- Ensure Docker volumes have correct permissions
- If missing Supabase files, delete the `/supabase` folder and restart

### GPU
- NVIDIA: Install [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
- AMD: Use ROCm or CPU mode
- macOS: Use `--profile cpu`

---

## 👓 Recommended reading

- [AI agents for developers](https://blog.n8n.io/ai-agents/)
- [Build AI workflow in n8n](https://docs.n8n.io/advanced-ai/intro-tutorial/)
- [Langchain Concepts in n8n](https://docs.n8n.io/advanced-ai/langchain/langchain-n8n/)

---

## 📜 License

Licensed under the Apache License 2.0.  
See [LICENSE](LICENSE) for details.
