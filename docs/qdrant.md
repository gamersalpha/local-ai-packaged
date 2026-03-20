# 📦 Qdrant — Base de données vectorielle

## C'est quoi ?

Qdrant est une base de données spécialisée dans le stockage et la recherche de vecteurs (embeddings). C'est le moteur de recherche sémantique derrière le RAG : il permet de trouver les passages de texte les plus pertinents par rapport à une question.

## Ce qu'on peut faire

- Stocker des millions de vecteurs avec métadonnées
- Recherche sémantique ultra-rapide (nearest neighbor)
- Filtrage par métadonnées (date, source, catégorie...)
- Collections multiples pour séparer les projets
- API REST et gRPC
- Dashboard web intégré pour explorer les données

## Exemple concret : Créer une base de connaissances

### 1. Accéder au dashboard

Ouvrir `http://IP:6333/dashboard` ou `https://qdrant.BASE_DOMAIN/dashboard`

### 2. Créer une collection

```bash
curl -X PUT "http://localhost:6333/collections/knowledge_base" \
  -H "Content-Type: application/json" \
  -d '{
    "vectors": {
      "size": 768,
      "distance": "Cosine"
    }
  }'
```

> `size: 768` correspond au modèle `nomic-embed-text` d'Ollama. Adaptez selon votre modèle d'embeddings.

### 3. Générer des embeddings avec Ollama et insérer

```bash
# Générer l'embedding d'un texte
EMBEDDING=$(curl -s http://localhost:11434/api/embeddings \
  -d '{"model": "nomic-embed-text", "prompt": "Docker est une plateforme de conteneurisation"}' \
  | python3 -c "import sys,json; print(json.dumps(json.load(sys.stdin)['embedding']))")

# Insérer dans Qdrant
curl -X PUT "http://localhost:6333/collections/knowledge_base/points" \
  -H "Content-Type: application/json" \
  -d "{
    \"points\": [{
      \"id\": 1,
      \"vector\": ${EMBEDDING},
      \"payload\": {
        \"text\": \"Docker est une plateforme de conteneurisation\",
        \"source\": \"wiki\",
        \"category\": \"devops\"
      }
    }]
  }"
```

### 4. Rechercher des documents similaires

```bash
# Générer l'embedding de la question
QUERY_EMB=$(curl -s http://localhost:11434/api/embeddings \
  -d '{"model": "nomic-embed-text", "prompt": "Comment fonctionne la conteneurisation ?"}' \
  | python3 -c "import sys,json; print(json.dumps(json.load(sys.stdin)['embedding']))")

# Recherche sémantique
curl -X POST "http://localhost:6333/collections/knowledge_base/points/search" \
  -H "Content-Type: application/json" \
  -d "{
    \"vector\": ${QUERY_EMB},
    \"limit\": 5,
    \"with_payload\": true
  }"
```

### 5. Filtrer par métadonnées

```bash
curl -X POST "http://localhost:6333/collections/knowledge_base/points/search" \
  -H "Content-Type: application/json" \
  -d "{
    \"vector\": ${QUERY_EMB},
    \"limit\": 5,
    \"with_payload\": true,
    \"filter\": {
      \"must\": [{
        \"key\": \"category\",
        \"match\": {\"value\": \"devops\"}
      }]
    }
  }"
```

### 6. Voir les collections et stats

```bash
# Lister les collections
curl http://localhost:6333/collections

# Info sur une collection
curl http://localhost:6333/collections/knowledge_base

# Nombre de points
curl http://localhost:6333/collections/knowledge_base/points/count
```

## Intégrations dans le stack

| Service | Usage |
|---------|-------|
| **n8n** | Nœud Qdrant Vector Store pour le RAG |
| **Flowise** | Nœud Qdrant pour les chatflows RAG |
| **Open WebUI** | Backend de recherche documentaire |

Dans n8n et Flowise, utiliser `http://qdrant:6333` comme URL (réseau Docker interne).

## Tailles de vecteurs par modèle

| Modèle | Dimensions |
|--------|-----------|
| `nomic-embed-text` | 768 |
| `mxbai-embed-large` | 1024 |
| `all-minilm` | 384 |
| OpenAI `text-embedding-3-small` | 1536 |

## Configuration

Variables d'environnement dans `.env` :
- `QDRANT_HOSTNAME` — Sous-domaine pour le reverse proxy
- Les données sont persistées dans le volume `qdrant_storage`
- Port REST : 6333, Port gRPC : 6334
