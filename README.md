# Self-hosted AI Package

**Self-hosted AI Package** is an open, Docker Compose–based template that bootstraps a fully featured Local AI and Low Code development environment — including Ollama for local LLMs, Open WebUI for an interface to chat with your n8n agents, and Supabase for database, vector store, and authentication.

This version extends Cole’s setup with major improvements and **automation scripts** for a cleaner deployment workflow — including Supabase, Open WebUI, Flowise, Neo4j, Langfuse, SearXNG, and optional Caddy integration.

If you use this version, all local RAG AI Agent workflows from the demo video will be automatically included in your n8n instance.

> ⚠️ **Note:** Supabase updated some environment variables.  
> If you had this project running before June 14th, add the following to your `.env`:
> ```bash
> POOLER_DB_POOL_SIZE=5
> ```

---

## 🧩 Installation (Simplified & Automated)

The installation process is now fully automated via the included Python setup scripts.

### 1️⃣ Clone the repository
```bash
git clone https://github.com/gamersalpha/local-ai-packaged.git
cd local-ai-packaged
```

### 2️⃣ Generate your environment file automatically

You no longer need to manually edit `.env` — the `generate_env.py` script will:

- Generate all required environment variables  
- Create secure random passwords and API keys  
- Detect your GPU (NVIDIA / AMD / CPU)  
- Configure correct local paths  

Run this for a full setup:

```bash
python3 generate_env.py --yes --regen-sensitive --docker
```

This will:
- Create `.env`
- Detect your GPU profile
- Build and start all Docker services automatically
- Display access URLs like:
  ```
  🌐 Services:
    🧠 Ollama      : http://192.168.1.42:11434
    ⚙️  n8n         : http://192.168.1.42:5678
    💬 OpenWebUI   : http://192.168.1.42:8080
    🧱 Supabase    : http://192.168.1.42:54323
  ```

---

### 3️⃣ Manual `.env` generation (optional)
If you prefer to create the `.env` without launching Docker yet:
```bash
python3 generate_env.py --yes --regen-sensitive
```

---

## 🚀 Start, Update, and Manage the Stack

### ▶️ Start services automatically
Use the new **`start_services.py`** to launch the full stack interactively:

```bash
python3 start_services.py [options]
```

#### Available options

| Option | Description |
|--------|--------------|
| `--profile [cpu|gpu-nvidia|gpu-amd|none]` | Hardware profile to use (default: `cpu`). |
| `--environment [private|public]` | Deployment mode (default: `private`). |
| `--no-supabase` | Skip Supabase (comments include line). |
| `--no-caddy` | Skip Caddy (comments service block). |
| `--update` | Pull the latest Docker images before launch. |
| `--dry-run` | Preview configuration without starting containers. |

#### Examples

```bash
# CPU-only stack
python3 start_services.py --profile cpu

# GPU (NVIDIA)
python3 start_services.py --profile gpu-nvidia

# Skip Supabase and Caddy
python3 start_services.py --no-supabase --no-caddy

# Dry-run (no Docker actions)
python3 start_services.py --dry-run

# Update images before starting
python3 start_services.py --update
```

💡 **Features**
- Auto-generates `.env` if missing  
- Clones Supabase Docker stack automatically  
- Toggles Supabase and Caddy in `docker-compose.yml`  
- Generates secure SearXNG secret key  
- Stops existing containers cleanly before redeploy  
- Launches Supabase → then Local AI stack in the correct order  

---

### ♻️ Update all services easily

Use the **`update_services.sh`** script to refresh every container and restart cleanly:

```bash
./update_services.sh
```

This script:
1. Stops all containers  
2. Pulls the latest images  
3. Relaunches the stack with your profile (default: CPU)  

To adapt for GPU:
```bash
docker compose -p localai -f docker-compose.yml --profile gpu-nvidia down
docker compose -p localai -f docker-compose.yml --profile gpu-nvidia pull
python3 start_services.py --profile gpu-nvidia --no-caddy
```

---

## 🧠 What’s included

✅ [**n8n**](https://n8n.io/) – workflow automation  
✅ [**Supabase**](https://supabase.com/) – database, auth & storage  
✅ [**Ollama**](https://ollama.com/) – local LLM runtime  
✅ [**Open WebUI**](https://openwebui.com/) – chat interface  
✅ [**Flowise**](https://flowiseai.com/) – low-code AI pipeline builder  
✅ [**Qdrant**](https://qdrant.tech/) – vector store  
✅ [**Neo4j**](https://neo4j.com/) – graph database  
✅ [**SearXNG**](https://searxng.org/) – web search for RAG  
✅ [**Langfuse**](https://langfuse.com/) – LLM tracing & analytics  
✅ [**Caddy**](https://caddyserver.com/) – reverse proxy (optional)  

---

## 🧾 Project Structure

```
.
├── docker-compose.yml
├── start_services.py
├── update_services.sh
├── generate_env.py
├── supabase/           # auto-cloned stack (ignored by Git)
├── n8n/
│   └── backup/
├── searxng/
├── shared/
└── neo4j/
```

> 📝 **Note:** The `supabase/` folder is automatically cloned by `start_services.py` from the official [Supabase repo](https://github.com/supabase/supabase) and should **not** be versioned.  
> Ensure it’s listed in `.gitignore`.

---

## 🧠 Quick Access

- n8n → http://localhost:5678  
- Open WebUI → http://localhost:8080  
- Ollama API → http://localhost:11434  
- Supabase → http://localhost:54323  
- Flowise → http://localhost:3001  
- Langfuse → http://localhost:3000  

---

## 📜 License

Licensed under the Apache License 2.0.  
See [LICENSE](LICENSE) for details.
