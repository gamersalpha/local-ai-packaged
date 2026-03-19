# 🧠 Local AI Packaged

> ⚠️ **Note:** This project is a maintained and extended **fork** of [coleam00/local-ai-packaged](https://github.com/coleam00/local-ai-packaged), which no longer appears to be actively maintained.
> This version includes up‑to‑date dependencies, bug fixes, and full automation scripts for setup and management.

---

## 🌍 Overview

**Local AI Packaged** provides a full self‑hosted AI environment using **Docker Compose**.
It bundles everything you need for local LLM workflows, including:

- 🧠 **Ollama** — Local LLM inference (CPU / NVIDIA / AMD)
- 💬 **Open WebUI** — Chat interface for your models and n8n agents
- ⚙️ **n8n** — Workflow automation with Redis queue mode support
- 🌊 **Flowise** — Low-code AI chain builder
- 🧱 **Supabase** — Database, vector store, and auth system (optional)
- 📊 **Langfuse** — LLM tracing and observability
- 📦 **Qdrant** — Vector database for RAG
- 🕸️ **Neo4j** — Graph database
- 🔍 **SearXNG** — Web search engine for RAG pipelines
- 🔧 **Unsloth** — LLM fine-tuning studio (NVIDIA GPU required, ~20 GB image)
- 🔒 **Caddy** or **SWAG** — Reverse proxy with auto HTTPS (optional)

This version is designed for **technical self‑hosters** running the stack on a home server, NAS (e.g. Synology), or any Linux/Windows host.

---

## ⚙️ Prerequisites

- 🐳 **Docker** and **Docker Compose** v2+
- 🐍 **Python 3.8+**
- 💾 **Git**
- 💡 At least **16 GB RAM** recommended

### GPU (optional)

- **NVIDIA:** [Install NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
- **AMD:** ROCm runtime configured
- **CPU only:** Works fine, just slower

---

## 🚀 Quick Start

### ① Clone the repository

```bash
git clone https://github.com/gamersalpha/local-ai-packaged.git
cd local-ai-packaged
```

### ② Generate the `.env` automatically

```bash
python3 generate_env.py --yes --regen-sensitive
```

Features:
- Generates secure random secrets
- Detects GPU type (NVIDIA / AMD / CPU)
- Sets correct local paths for volumes
- Expands `BASE_DOMAIN` into per-service hostnames if configured

### ③ Deploy the stack

**Interactive setup wizard (recommended for first time):**
```bash
python3 start_services.py --setup
```

**Or direct launch:**
```bash
python3 start_services.py --profile cpu --no-supabase --no-caddy
```

---

## 🧩 Managing the Stack

### ▶️ start_services.py

The main orchestrator with service selection, proxy detection, and interactive wizard.

```bash
python3 start_services.py [options]
```

#### Options

| Option | Description |
|--------|-------------|
| `--setup` | Interactive setup wizard with service picker |
| `--profile [cpu\|gpu-nvidia\|gpu-amd]` | Select hardware profile |
| `--environment [private\|public]` | Network mode (localhost-only or LAN) |
| `--services [names...]` | Select specific services to deploy |
| `--proxy [caddy\|swag\|none\|auto]` | Reverse proxy type (auto-detects SWAG) |
| `--no-supabase` | Skip Supabase |
| `--no-caddy` | Skip Caddy reverse proxy |
| `--update` | Pull latest Docker images before start |
| `--dry-run` | Preview configuration only |

#### Selectable Services

Use `--services` to deploy only what you need. Dependencies are resolved automatically (e.g. `n8n` will also start `postgres` and `redis`).

```bash
# Deploy only n8n, Open WebUI, and Ollama
python3 start_services.py --services n8n openwebui ollama

# Deploy everything (default)
python3 start_services.py --services all
```

Available: `n8n`, `openwebui`, `flowise`, `qdrant`, `neo4j`, `langfuse`, `searxng`, `ollama`, `unsloth`

#### Examples

```bash
# Interactive wizard
python3 start_services.py --setup

# CPU, all services, no reverse proxy
python3 start_services.py --profile cpu --no-supabase --no-caddy

# NVIDIA GPU, public network with SWAG proxy
python3 start_services.py --profile gpu-nvidia --environment public --proxy swag

# Dry-run to preview what would be deployed
python3 start_services.py --services n8n openwebui ollama --dry-run

# Pull latest images and restart
python3 start_services.py --update
```

💡 **What it does:**
- Validates or creates your `.env`
- Clones Supabase's official Docker stack if missing
- Toggles Caddy and Supabase dynamically in `docker-compose.yml`
- Generates a new secret key for SearXNG
- Auto-detects SWAG reverse proxy and installs nginx configs
- Resolves service dependencies automatically
- Stops existing containers before redeploy
- Starts Supabase first (if enabled), then the Local AI stack

---

### ♻️ Update all services

```bash
./update_services.sh [profile]
```

Examples:
```bash
./update_services.sh cpu
./update_services.sh gpu-nvidia
```

This will stop all containers, pull latest images, and restart the stack.

---

## 🌐 Access Your Services

| Service | Description | Default URL (private) |
|---------|-------------|----------------------|
| **n8n** | Workflow automation | http://localhost:5678 |
| **Open WebUI** | Chat interface for LLMs | http://localhost:8080 |
| **Ollama** | Local LLM API | http://localhost:11434 |
| **Flowise** | Low-code AI builder | http://localhost:3001 |
| **Langfuse** | LLM tracing dashboard | http://localhost:3000 |
| **SearXNG** | Web search for RAG | http://localhost:8081 |
| **Neo4j** | Graph database browser | http://localhost:7474 |
| **Qdrant** | Vector database API | http://localhost:6333 |
| **PostgreSQL** | Shared database | localhost:5433 |
| **Unsloth** | LLM fine-tuning studio (~20 GB image, long pull) | http://localhost:8888 |
| **Supabase** | DB, Auth & API (optional) | http://localhost:54323 |

> In private mode, all ports are bound to `127.0.0.1`. In public mode, they are accessible on all interfaces.

---

## 🌐 Domain Configuration

Set `BASE_DOMAIN` in your `.env` to auto-derive all service hostnames:

```bash
BASE_DOMAIN=home.example.com
```

This generates:
- `n8n.home.example.com`
- `openwebui.home.example.com`
- `flowise.home.example.com`
- etc.

Override individual services:
```bash
N8N_HOSTNAME=custom-n8n.mydomain.com
```

---

## 🔒 Reverse Proxy

### Caddy (built-in)

Enabled by default in public mode. Auto-generates Let's Encrypt certificates.

### SWAG (auto-detected)

If you already run [SWAG](https://github.com/linuxserver/docker-swag) on your server (Synology, Unraid, etc.), `start_services.py` detects it automatically and installs nginx proxy configs from the `swag/` directory.

```bash
python3 start_services.py --proxy swag
# or let it auto-detect:
python3 start_services.py --proxy auto
```

---

## ⚡ n8n Queue Mode

For heavy workflows, enable Redis-backed queue mode with separate worker containers:

```bash
# In .env:
N8N_EXECUTIONS_MODE=queue
```

Then start with the worker profile:
```bash
python3 start_services.py --profile cpu
docker compose -p localai --profile n8n-worker up -d
```

---

## 🗄️ Database Isolation

Each service uses its own PostgreSQL database to prevent schema collisions:

| Service | Database |
|---------|----------|
| n8n | `n8n` |
| Langfuse | `langfuse` |
| Flowise | `flowise` |
| Supabase | `postgres` |

Databases are auto-created on first start via `postgres/init/01-create-databases.sql`.

---

## 🛠️ Troubleshooting

### Supabase fails to start
- Check that the folder `supabase/` was created automatically
- Delete it and rerun: `python3 start_services.py`
- Ensure `.env` contains `POOLER_DB_POOL_SIZE=5`

### GPU not detected
- Ensure the **NVIDIA Container Toolkit** or **ROCm** is installed correctly
- Fallback to CPU: `python3 start_services.py --profile cpu`

### Ports already in use
- Check what's using the port: `netstat -tlnp | grep <port>`
- Edit `docker-compose.override.private.yml` to change exposed ports

### Unsloth image takes forever to pull
- The `unsloth/unsloth:latest` image is ~20 GB (CUDA + PyTorch). First pull can take 10-30 minutes depending on your connection.
- You can pull it in the background: `docker pull unsloth/unsloth:latest`
- Deploy all other services first without Unsloth, then add it later with: `docker compose -p localai --profile gpu-nvidia -f docker-compose.yml -f docker-compose.override.private.yml up -d unsloth`

### Container healthcheck failing
- All healthchecks use `127.0.0.1` (not `localhost`) to avoid IPv6 issues
- Check logs: `docker logs <container_name>`

---

## 🧾 Project Structure

```
.
├── docker-compose.yml                 # Main orchestration file
├── docker-compose.override.private.yml # Localhost-only port bindings
├── docker-compose.override.public.yml  # LAN-accessible port bindings
├── start_services.py                  # Smart deployment launcher
├── generate_env.py                    # .env generator with GPU detection
├── update_services.sh                 # Container update helper
├── Caddyfile                          # Caddy reverse proxy config
├── .env.example                       # Environment template
├── n8n_pipe.py                        # Open WebUI → n8n integration pipe
├── postgres/
│   └── init/                          # Database init scripts
├── swag/                              # SWAG proxy-conf templates
├── n8n/
│   └── backup/                        # Pre-built n8n workflows
├── flowise/                           # Flowise chatflows & custom tools
├── searxng/                           # SearXNG configuration
├── supabase/                          # Auto-cloned (gitignored)
├── shared/                            # Shared data volume (gitignored)
└── neo4j/                             # Neo4j data (gitignored)
```

---

## 📋 Roadmap / TODO

### 🔜 Planned Features

- [ ] **Landing page dashboard** — Page d'accueil Cyberpunk 2077 avec icônes, descriptions et liens dynamiques vers chaque service installé (localhost ou domaine)
- [ ] **Environment-based versioning** — Mode `prod` (versions pinnées) vs `recette` (latest) avec granularité par service. Permettre `--env prod` / `--env recette` dans `start_services.py`
- [ ] **Supabase rework** — Refaire l'intégration Supabase pour plus de fiabilité et de modularité (clone, .env partagé, sélection de services)
- [ ] **Monitoring & alerting** — Intégration Prometheus/Grafana pour surveiller l'état des services
- [ ] **Backup automation** — Script de backup automatique des volumes Docker et bases de données
- [ ] **Multi-node support** — Support Docker Swarm ou Kubernetes pour déploiement multi-serveur

### ✅ Recently Completed

- [x] Selective service deployment (`--services`)
- [x] Interactive setup wizard (`--setup`)
- [x] SWAG reverse proxy auto-detection and config generation
- [x] Global `BASE_DOMAIN` with per-service hostname derivation
- [x] n8n v2 + Redis queue mode + worker profile
- [x] Database isolation (separate PostgreSQL databases per service)
- [x] Healthchecks on all services (IPv4-safe)
- [x] Unified logging with rotation on all containers
- [x] Dynamic `update_services.sh` with profile argument
- [x] Redis authentication (`--requirepass`)

---

## 📜 License

Licensed under the **Apache 2.0 License**.
See [LICENSE](LICENSE) for details.

---

**Built and maintained with ❤️ for the self‑hosting community.**
