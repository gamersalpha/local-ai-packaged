# 🌊 Flowise — Constructeur d'IA low-code

## C'est quoi ?

Flowise est un éditeur visuel drag-and-drop pour construire des chaînes LLM (basé sur LangChain). Il permet de créer des chatbots, agents et pipelines RAG sans écrire de code, puis de les exposer via API.

## Ce qu'on peut faire

- Construire des chatflows visuels (chaînes LangChain)
- Créer des agents avec outils personnalisés
- Mettre en place du RAG avec différents vector stores
- Exposer chaque chatflow comme une API REST
- Intégrer dans n'importe quelle application via l'API ou le widget embed
- Connecter Ollama, Qdrant, PostgreSQL et des APIs externes

## Exemple concret : Chatbot RAG avec Ollama + Qdrant

### 1. Accéder à Flowise

Ouvrir `https://flowise.BASE_DOMAIN` ou `http://IP:3001`

### 2. Créer un nouveau Chatflow

**Chatflows** > **Add New**

### 3. Ajouter les nœuds (drag & drop)

Construire cette chaîne :

```
[ChatOllama] ──────────────┐
                            ▼
[Qdrant Upsert] ◄── [RecursiveCharacterTextSplitter] ◄── [Document Loaders]
       │
       ▼
[Conversational Retrieval QA Chain]
       │
       ▼
  [Response]
```

#### Nœud ChatOllama
- Base URL : `http://ollama:11434`
- Model : `llama3.1:8b`
- Temperature : `0.7`

#### Nœud Ollama Embeddings
- Base URL : `http://ollama:11434`
- Model : `nomic-embed-text`

#### Nœud Qdrant
- URL : `http://qdrant:6333`
- Collection : `flowise_docs`

#### Nœud Text Splitter
- Chunk Size : `1000`
- Chunk Overlap : `200`

### 4. Upserter des documents

1. Dans le chatflow, aller dans l'onglet **Upsert**
2. Uploader vos fichiers PDF/TXT
3. Cliquer sur **Upsert** — les documents sont découpés, vectorisés et stockés dans Qdrant

### 5. Tester le chatflow

Utiliser le chat intégré en bas à droite :
```
Q: De quoi parle le document ?
Q: Quelles sont les recommandations ?
Q: Résume la section 3.
```

### 6. Utiliser l'API

Chaque chatflow a un ID unique. Pour l'appeler :

```bash
# Récupérer l'ID du chatflow dans l'URL de Flowise
CHATFLOW_ID="votre-chatflow-id"

curl -X POST "http://localhost:3001/api/v1/prediction/${CHATFLOW_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Quelles sont les bonnes pratiques mentionnées ?",
    "overrideConfig": {
      "sessionId": "user-123"
    }
  }'
```

### 7. Intégrer le widget dans une page web

```html
<script type="module">
  import Chatbot from 'https://cdn.jsdelivr.net/npm/flowise-embed/dist/web.js'
  Chatbot.init({
    chatflowid: 'votre-chatflow-id',
    apiHost: 'https://flowise.BASE_DOMAIN',
    theme: {
      button: { backgroundColor: '#00f0ff' },
      chatWindow: { title: 'Assistant IA' }
    }
  })
</script>
```

## Chatflows pré-construits

Le dossier `flowise/` contient des exports prêts à importer :
- `Web Search + n8n Agent Chatflow.json` — Agent avec recherche web et intégration n8n

Pour importer : **Chatflows** > **Settings** (⚙️) > **Load Chatflow**

## Configuration

Variables d'environnement dans `.env` :
- `FLOWISE_HOSTNAME` — Sous-domaine pour le reverse proxy
- `FLOWISE_USERNAME` / `FLOWISE_PASSWORD` — Identifiants admin (premier lancement uniquement)
- Les données sont persistées dans le volume `flowise` et dans PostgreSQL
