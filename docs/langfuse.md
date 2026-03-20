# 📊 Langfuse — Observabilité LLM

## C'est quoi ?

Langfuse est une plateforme d'observabilité pour les applications LLM. Elle permet de tracer, évaluer et debugger chaque appel à vos modèles IA. C'est le "Datadog des LLMs" — indispensable pour comprendre ce que font vos agents et optimiser les coûts/performances.

## Ce qu'on peut faire

- Tracer chaque appel LLM (prompt, réponse, latence, tokens)
- Visualiser les chaînes d'exécution complètes (spans imbriqués)
- Évaluer la qualité des réponses (scores manuels ou automatiques)
- Analyser les coûts par modèle, par utilisateur, par session
- Créer des datasets de test pour le fine-tuning
- Comparer les performances entre modèles
- Gérer des prompts versionnés

## Exemple concret : Tracer un agent n8n

### 1. Accéder à Langfuse

Ouvrir `https://langfuse.BASE_DOMAIN` ou `http://IP:3100`

### 2. Créer un compte et un projet

1. Sign up avec email/password
2. Créer un nouveau projet : "Local AI Stack"
3. **Settings** > **API Keys** > Créer une paire de clés
4. Noter le `Public Key` et `Secret Key`

### 3. Configurer n8n pour tracer vers Langfuse

Dans n8n, pour chaque nœud AI Agent ou LLM Chain :

1. Ouvrir les paramètres du nœud **AI Agent**
2. Section **Options** > **Langfuse**
3. Ajouter un credential Langfuse :
   - Host : `http://langfuse-web:3000` (réseau Docker interne)
   - Public Key : votre clé publique
   - Secret Key : votre clé secrète

### 4. Tracer via l'API Python (pour scripts custom)

```python
from langfuse import Langfuse

langfuse = Langfuse(
    public_key="pk-lf-...",
    secret_key="sk-lf-...",
    host="http://IP:3100"  # ou https://langfuse.BASE_DOMAIN
)

# Créer une trace
trace = langfuse.trace(
    name="rag-query",
    user_id="user-123",
    metadata={"source": "api"}
)

# Logger un appel LLM
generation = trace.generation(
    name="ollama-llama3",
    model="llama3.1:8b",
    input=[{"role": "user", "content": "Qu'est-ce que Docker ?"}],
    output="Docker est une plateforme de conteneurisation...",
    usage={"input": 15, "output": 42}
)

# Ajouter un score
trace.score(name="quality", value=0.9, comment="Réponse précise et complète")

langfuse.flush()
```

### 5. Tracer via l'API REST

```bash
curl -X POST "http://localhost:3100/api/public/ingestion" \
  -H "Content-Type: application/json" \
  -u "pk-lf-xxx:sk-lf-xxx" \
  -d '{
    "batch": [{
      "id": "trace-001",
      "type": "trace-create",
      "timestamp": "2025-01-01T00:00:00Z",
      "body": {
        "name": "test-trace",
        "userId": "user-123"
      }
    }]
  }'
```

### 6. Explorer les traces

Dans le dashboard Langfuse :
- **Traces** : voir toutes les exécutions, filtrer par nom/utilisateur/date
- **Sessions** : grouper les traces par conversation
- **Generations** : détail de chaque appel LLM (prompt, réponse, latence)
- **Scores** : évaluations manuelles et automatiques
- **Dashboard** : métriques globales (latence moyenne, tokens consommés, coûts)

### 7. Créer un dataset d'évaluation

1. **Datasets** > **New Dataset** : "test-rag-quality"
2. Ajouter des items (question + réponse attendue) :
   - Input : `{"question": "Qu'est-ce que Docker ?"}`
   - Expected Output : `"Docker est une plateforme de conteneurisation..."`
3. Lancer des évaluations automatiques sur vos traces

## Intégrations dans le stack

| Service | Usage |
|---------|-------|
| **n8n** | Tracing automatique des agents et chaînes LLM |
| **Flowise** | Tracing des chatflows via callback |
| **Ollama** | Suivi des appels modèles locaux |

## Configuration

Variables d'environnement dans `.env` :
- `LANGFUSE_HOSTNAME` — Sous-domaine pour le reverse proxy
- `NEXTAUTH_URL` — URL publique de Langfuse (important pour l'authentification)
- `ENCRYPTION_KEY` — Clé de chiffrement (ne jamais changer)
- Backend : ClickHouse (analytics) + PostgreSQL (données) + MinIO (stockage)
- Port externe : 3100 (remappé depuis le port interne 3000)
