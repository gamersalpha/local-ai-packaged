# 📚 Cookbooks — Local AI Packaged

Guides pratiques pour chaque service du stack. Chaque cookbook explique ce que fait le service, ce qu'on peut en faire, et donne un exemple concret fonctionnel.

## Services

| Cookbook | Service | Description |
|---------|---------|-------------|
| [ollama.md](ollama.md) | 🧠 Ollama | Moteur d'inférence LLM local |
| [open-webui.md](open-webui.md) | 💬 Open WebUI | Interface de chat IA |
| [n8n.md](n8n.md) | ⚙️ n8n | Automatisation de workflows IA |
| [flowise.md](flowise.md) | 🌊 Flowise | Constructeur d'IA low-code |
| [qdrant.md](qdrant.md) | 📦 Qdrant | Base de données vectorielle |
| [neo4j.md](neo4j.md) | 🕸️ Neo4j | Base de données de graphes |
| [langfuse.md](langfuse.md) | 📊 Langfuse | Observabilité LLM |
| [searxng.md](searxng.md) | 🔍 SearXNG | Moteur de recherche web |

## Scénario complet : Pipeline RAG de bout en bout

1. **Ollama** : installer `llama3.1:8b` + `nomic-embed-text`
2. **Qdrant** : créer une collection `knowledge_base`
3. **n8n** : workflow d'indexation (PDF → chunks → embeddings → Qdrant)
4. **n8n** : workflow agent RAG (webhook → recherche Qdrant → réponse Ollama)
5. **Open WebUI** : connecter le pipe n8n pour chatter avec l'agent
6. **SearXNG** : activer la recherche web dans Open WebUI pour enrichir les réponses
7. **Langfuse** : tracer tous les appels pour monitorer la qualité
8. **Neo4j** : (optionnel) GraphRAG pour des relations complexes entre entités
