# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Local AI Packaged is a self-hosted AI infrastructure stack using Docker Compose. It bundles LLM inference (Ollama), chat UI (Open WebUI), workflow automation (n8n, Flowise), databases (PostgreSQL, Qdrant, Neo4j, Supabase), observability (Langfuse), web search (SearXNG), and reverse proxy (Caddy or SWAG) into a single deployable environment.

Fork of [coleam00/local-ai-packaged](https://github.com/coleam00/local-ai-packaged).

## Key Commands

```bash
# Interactive first-time setup wizard
python3 start_services.py --setup

# Generate .env with auto-detected GPU and secure secrets
python3 generate_env.py --yes --regen-sensitive

# Deploy all services
python3 start_services.py

# Deploy specific services only
python3 start_services.py --services n8n openwebui ollama qdrant

# Deploy with specific options
python3 start_services.py --profile gpu-nvidia --environment public --proxy swag
python3 start_services.py --no-supabase --no-caddy
python3 start_services.py --update --dry-run

# Update containers and restart
./update_services.sh [profile]  # e.g., ./update_services.sh gpu-nvidia

# Direct docker compose (project name is "localai")
docker compose -p localai -f docker-compose.yml --profile cpu up -d
docker compose -p localai -f docker-compose.yml --profile cpu down
```

## Architecture

### Deployment Flow

`generate_env.py` creates `.env` with secrets, GPU detection, and BASE_DOMAIN hostname expansion. `start_services.py` clones Supabase (sparse checkout), toggles Caddy/Supabase in docker-compose.yml, generates SearXNG secret, detects SWAG proxy, resolves service dependencies, starts Supabase stack first (10s wait), then starts main stack with selected profile and services.

### Selective Service Deployment

`--services` flag accepts any combination of: `n8n`, `openwebui`, `flowise`, `qdrant`, `neo4j`, `langfuse`, `searxng`, `ollama`. The `SERVICE_DEPS` map in start_services.py automatically includes required infrastructure (postgres, redis, etc.).

### Hardware Profiles

Three Docker Compose profiles select the Ollama variant: `cpu`, `gpu-nvidia`, `gpu-amd`. An additional `n8n-worker` profile enables Redis-backed queue mode workers.

### Network Modes

- **private** (`docker-compose.override.private.yml`): All ports bound to `127.0.0.1`
- **public** (`docker-compose.override.public.yml`): Ports on `0.0.0.0`, designed for reverse proxy routing

### Reverse Proxy Support

- **Caddy** (built-in): Configured via `Caddyfile`, auto Let's Encrypt
- **SWAG** (auto-detected): Proxy-conf templates in `swag/` directory, auto-installed to SWAG's proxy-confs dir
- **None**: Direct port access only

### Domain Configuration

Set `BASE_DOMAIN` in `.env` and all service hostnames auto-derive as `<service>.BASE_DOMAIN`. Individual overrides via `*_HOSTNAME` variables. Expansion happens in `generate_env.py`.

### Database Isolation

PostgreSQL init scripts in `postgres/init/` create separate databases for n8n, Langfuse, and Flowise to prevent schema collisions.

### N8N Queue Mode

Set `N8N_EXECUTIONS_MODE=queue` in `.env` to enable Redis-backed execution queue. Add `--profile n8n-worker` to start worker containers for horizontal scaling.

### Key Files

- `docker-compose.yml` — main orchestration; uses YAML anchors (`x-n8n`, `x-ollama`, `x-init-ollama`, `x-logging`)
- `start_services.py` — smart launcher with interactive wizard, service selection, proxy detection
- `generate_env.py` — .env generator with GPU detection and BASE_DOMAIN hostname expansion
- `n8n_pipe.py` — Open WebUI custom pipe that routes chat to n8n webhooks
- `Caddyfile` — Caddy reverse proxy routes using env var hostnames
- `swag/` — SWAG reverse proxy subdomain conf templates
- `postgres/init/` — PostgreSQL init scripts for database isolation
- `searxng/settings-base.yml` — SearXNG base config (runtime `settings.yml` is generated/gitignored)
- `n8n/backup/workflows/` — pre-built RAG agent workflows (V1/V2/V3)
- `flowise/` — exported chatflows and custom tool definitions

### Supabase Integration

Supabase is auto-cloned via git sparse-checkout (only `docker/` dir) into `supabase/`. Its docker-compose is included via the `include:` directive. `start_services.py` toggles this include on/off by commenting the relevant line.

## Environment

- `.env` is generated from `.env.example` — never commit `.env`
- `supabase/`, `volumes/`, `shared/`, `neo4j/` are gitignored (runtime data)
- Project language is French (commits, README)
- All images are pinned to specific versions (except Open WebUI `main` tag and SearXNG `latest`)
