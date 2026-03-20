# ⚙️ n8n — Automatisation de workflows IA

## C'est quoi ?

n8n est une plateforme d'automatisation de workflows no-code/low-code. C'est l'équivalent self-hosted de Zapier/Make, mais avec des nœuds IA natifs pour construire des agents, du RAG et des chaînes de traitement LLM.

## Ce qu'on peut faire

- Créer des workflows visuels connectant des centaines de services
- Construire des agents IA avec mémoire, outils et RAG
- Automatiser des tâches (emails, webhooks, cron, fichiers...)
- Connecter Ollama, Qdrant, PostgreSQL et tous les services du stack
- Exposer des workflows via webhook (API REST instantanée)
- Planifier des exécutions récurrentes (cron)

## Exemple concret : Agent RAG avec Ollama + Qdrant

Cet exemple crée un agent qui répond aux questions en cherchant dans une base de connaissances vectorielle.

### 1. Accéder à n8n

Ouvrir `https://n8n.BASE_DOMAIN` ou `http://IP:5678`

### 2. Créer les credentials

#### Ollama
- **Settings** > **Credentials** > **Add Credential**
- Type : `Ollama`
- Base URL : `http://ollama:11434`

#### Qdrant
- Type : `Qdrant`
- URL : `http://qdrant:6333`

### 3. Workflow : Indexer des documents

Créer un workflow avec ces nœuds :

```
[Manual Trigger] → [Read Binary Files] → [Extract Document Text]
    → [Recursive Character Text Splitter] → [Embeddings Ollama]
    → [Qdrant Vector Store (Insert)]
```

Configuration des nœuds :
- **Embeddings Ollama** : modèle `nomic-embed-text`
- **Qdrant Vector Store** :
  - Collection : `knowledge_base`
  - Action : Insert
  - Les documents seront découpés en chunks et stockés avec leurs embeddings

### 4. Workflow : Agent RAG (question/réponse)

```
[Webhook Trigger] → [AI Agent]
    ├── LLM : [Ollama Chat Model] (llama3.1:8b)
    ├── Memory : [Window Buffer Memory]
    └── Tool : [Vector Store Tool]
                 ├── Embeddings : [Ollama Embeddings] (nomic-embed-text)
                 └── Vector Store : [Qdrant Vector Store (Search)]
```

Configuration :
- **Webhook** : Method POST, Path `/rag-agent`
- **AI Agent** : System message :
```
Tu es un assistant expert. Utilise l'outil de recherche vectorielle pour
trouver les informations pertinentes avant de répondre. Réponds toujours
en français. Si tu ne trouves pas l'information, dis-le clairement.
```
- **Vector Store Tool** : Description = "Cherche dans la base de connaissances"
- **Window Buffer Memory** : 10 derniers messages

### 5. Tester l'agent

```bash
curl -X POST https://n8n.BASE_DOMAIN/webhook/rag-agent \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "user-123",
    "message": "Quelles sont les bonnes pratiques de sécurité Docker ?"
  }'
```

### 6. Connecter à Open WebUI

Utiliser le `n8n_pipe.py` pour router les messages Open WebUI vers ce webhook n8n. L'utilisateur chatte dans Open WebUI, et l'agent n8n fait le RAG en arrière-plan.

## Workflows pré-construits

Le dossier `n8n/backup/workflows/` contient des workflows prêts à l'emploi :

| Fichier | Description |
|---------|-------------|
| `V1_Local_RAG_AI_Agent.json` | Agent RAG basique |
| `V2_Local_Supabase_RAG_AI_Agent.json` | Agent RAG avec Supabase |
| `V3_Local_Agentic_RAG_AI_Agent.json` | Agent RAG avancé multi-outils |

Pour importer : **Workflows** > **Import from File**

## Configuration

Variables d'environnement dans `.env` :
- `N8N_HOSTNAME` — Sous-domaine pour le reverse proxy
- `N8N_ENCRYPTION_KEY` — Clé de chiffrement (ne jamais changer après premier lancement)
- `N8N_EXECUTIONS_MODE=queue` — Active le mode queue Redis pour le scaling horizontal
