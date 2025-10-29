# 🧠 Local AI Packaged

> ⚠️ **Note:** This project is a maintained and extended **fork** of [coleam00/local-ai-packaged](https://github.com/coleam00/local-ai-packaged), which no longer appears to be actively maintained.  
> This version includes up‑to‑date dependencies, bug fixes, and full automation scripts for setup and management.

---

## 🌍 Overview

**Local AI Packaged** provides a full self‑hosted AI environment using **Docker Compose**.  
It bundles everything you need for local LLM workflows, including:

- 🧠 **Ollama** for local LLM inference  
- 💬 **Open WebUI** for chatting with your models or n8n agents  
- ⚙️ **n8n** for building automation workflows  
- 🧱 **Supabase** as database, vector store, and auth system  
- 🧩 **Flowise**, **Langfuse**, **Qdrant**, **Neo4j**, **SearXNG**, and optional **Caddy**

This version is designed for **technical self‑hosters** running the stack on a home server, NAS (e.g. Synology), or any Linux host.

---

## ⚙️ Prerequisites

Make sure you have:

- 🐳 **Docker** and **Docker Compose** installed  
- 🐍 **Python 3.8+**  
- 💾 **Git**  
- 💡 At least **16 GB RAM** recommended

### GPU (optional)

- **NVIDIA:** [Install NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)  
- **AMD:** ROCm runtime configured  
- **CPU only:** Works fine, just slower

---

## 🚀 Quick Installation

### ① Clone the repository

```bash
git clone https://github.com/gamersalpha/local-ai-packaged.git
cd local-ai-packaged
```

### ② Generate the `.env` automatically

The `generate_env.py` script creates a full environment configuration automatically:  
- Generates secure random secrets  
- Detects GPU type (NVIDIA / AMD / CPU)  
- Sets correct local paths for volumes  

Run:

```bash
python3 generate_env.py --yes --regen-sensitive --docker
```

Once complete, it will start the stack and show the service URLs:

```
🌐 Available services:
  🧠 Ollama      : http://192.168.1.42:11434
  ⚙️ n8n          : http://192.168.1.42:5678
  💬 Open WebUI  : http://192.168.1.42:8080
  🧱 Supabase    : http://192.168.1.42:54323
```

---

## 🧩 Managing the stack

### ▶️ Start automatically

Use the provided Python launcher for easy orchestration:

```bash
python3 start_services.py [options]
```

#### Options

| Option | Description |
|--------|--------------|
| `--profile [cpu|gpu-nvidia|gpu-amd]` | Select hardware profile |
| `--environment [private|public]` | Deployment environment |
| `--no-supabase` | Skip Supabase include |
| `--no-caddy` | Skip Caddy reverse proxy |
| `--update` | Pull latest Docker images before start |
| `--dry-run` | Preview configuration only |

#### Examples

```bash
# CPU-only deployment
python3 start_services.py --profile cpu

# NVIDIA GPU
python3 start_services.py --profile gpu-nvidia

# Skip Supabase and Caddy
python3 start_services.py --no-supabase --no-caddy

# Pull new images before starting
python3 start_services.py --update
```

💡 **What it does:**
- Validates or creates your `.env`
- Clones Supabase’s official Docker stack if missing
- (De)comments Caddy and Supabase dynamically
- Generates a new secret key for SearXNG
- Stops existing containers before redeploy
- Starts Supabase → then the Local AI stack

---

### ♻️ Update all services

Use the helper script `update_services.sh`:

```bash
./update_services.sh
```

This will:
1. Stop all containers  
2. Pull the latest images  
3. Restart the stack via `start_services.py`

For GPU users, you can adjust:
```bash
docker compose -p localai -f docker-compose.yml --profile gpu-nvidia down
docker compose -p localai -f docker-compose.yml --profile gpu-nvidia pull
python3 start_services.py --profile gpu-nvidia --no-caddy
```

---

## 🌐 Access your local services

| Service | Description | Default URL |
|----------|--------------|-------------|
| **n8n** | Workflow automation | http://192.168.1.42:5678 |
| **Open WebUI** | Chat interface for LLMs | http://192.168.1.42:8080 |
| **Ollama** | Local LLM API | http://192.168.1.42:11434 |
| **Flowise** | Low‑code AI builder | http://192.168.1.42:3001 |
| **Supabase** | DB, Auth & Vector store | http://192.168.1.42:54323 |
| **Langfuse** | LLM tracing dashboard | http://192.168.1.42:3000 |
| **SearXNG** | Web search engine for RAG | http://192.168.1.42:8080 |
| **Neo4j** | Graph database | http://192.168.1.42:7474 |

*(Adjust IPs for your own LAN setup.)*

---

## 🛠️ Troubleshooting

### Supabase fails to start
- Check that the folder `supabase/` was created automatically.  
- Delete it and rerun:  
  ```bash
  python3 start_services.py --no-caddy
  ```
- Ensure `.env` contains:  
  ```bash
  POOLER_DB_POOL_SIZE=5
  ```

### GPU not detected
- Ensure the **NVIDIA Container Toolkit** or **ROCm** is installed correctly.  
- Fallback to CPU mode if needed:  
  ```bash
  python3 start_services.py --profile cpu
  ```

### Ports already in use
Edit `docker-compose.yml` to change exposed ports, then restart.

---

## 🧾 Project structure

```
.
├── docker-compose.yml
├── start_services.py
├── update_services.sh
├── generate_env.py
├── supabase/           # auto-cloned (ignored by Git)
├── n8n/
│   └── backup/
├── searxng/
├── shared/
└── neo4j/
```

> 📝 **Note:** The `supabase/` folder is automatically cloned by `start_services.py` from [github.com/supabase/supabase](https://github.com/supabase/supabase).  
> It should **not** be committed to Git and is already included in `.gitignore`.

---

## 📜 License

Licensed under the **Apache 2.0 License**.  
See [LICENSE](LICENSE) for details.

---

**Built and maintained with ❤️ for the self‑hosting community.**
