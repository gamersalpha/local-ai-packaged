# 🧠 Ollama — Moteur d'inférence LLM local

## C'est quoi ?

Ollama permet d'exécuter des modèles de langage (LLM) directement sur votre serveur, sans dépendance cloud. Il gère le téléchargement, le chargement en mémoire et l'API de chat compatible OpenAI.

## Ce qu'on peut faire

- Exécuter des modèles open-source (Llama 3, Mistral, Phi, Gemma, Qwen, DeepSeek...)
- Exposer une API REST compatible OpenAI (`/v1/chat/completions`)
- Créer des modèles personnalisés avec un `Modelfile` (system prompt, paramètres)
- Servir de backend pour Open WebUI, n8n, Flowise et tout outil compatible OpenAI

## Modèles recommandés

| Modèle | Taille | Usage |
|--------|--------|-------|
| `llama3.2:3b` | ~2 GB | Chat rapide, tests |
| `llama3.1:8b` | ~4.7 GB | Usage général |
| `mistral:7b` | ~4.1 GB | Bon en français |
| `qwen2.5:14b` | ~9 GB | Performant, multilingue |
| `deepseek-r1:8b` | ~4.9 GB | Raisonnement avancé |
| `nomic-embed-text` | ~274 MB | Embeddings pour RAG |

## Exemple concret : Installer un modèle et discuter

### 1. Télécharger un modèle

```bash
# Depuis le serveur
docker exec -it ollama ollama pull llama3.1:8b

# Ou via l'API
curl http://localhost:11434/api/pull -d '{"name": "llama3.1:8b"}'
```

### 2. Lister les modèles installés

```bash
curl http://localhost:11434/api/tags | python3 -m json.tool
```

### 3. Discuter via l'API

```bash
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1:8b",
    "messages": [
      {"role": "system", "content": "Tu es un assistant technique expert en DevOps."},
      {"role": "user", "content": "Explique-moi Docker Compose en 3 phrases."}
    ]
  }'
```

### 4. Créer un modèle personnalisé

```bash
# Créer un Modelfile
cat << 'EOF' > /tmp/Modelfile
FROM llama3.1:8b
SYSTEM "Tu es un assistant spécialisé en cybersécurité. Tu réponds toujours en français avec des exemples concrets."
PARAMETER temperature 0.7
PARAMETER top_p 0.9
EOF

# Créer le modèle
docker exec -i ollama ollama create cyber-assistant -f - < /tmp/Modelfile

# Tester
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "cyber-assistant",
    "messages": [{"role": "user", "content": "Comment sécuriser un serveur SSH ?"}]
  }'
```

### 5. Télécharger un modèle d'embeddings pour le RAG

```bash
docker exec -it ollama ollama pull nomic-embed-text
```

Ce modèle sera utilisé par n8n, Flowise et Open WebUI pour le RAG (Retrieval Augmented Generation).

## Endpoints utiles

| Endpoint | Description |
|----------|-------------|
| `GET /api/tags` | Liste des modèles |
| `POST /api/pull` | Télécharger un modèle |
| `POST /api/generate` | Génération de texte (streaming) |
| `POST /v1/chat/completions` | API compatible OpenAI |
| `POST /api/embeddings` | Générer des embeddings |

## Configuration

Variables d'environnement dans `.env` :
- `OLLAMA_HOSTNAME` — Sous-domaine pour le reverse proxy
- Les modèles sont persistés dans le volume `ollama_storage`
