# 🔍 SearXNG — Moteur de recherche web

## C'est quoi ?

SearXNG est un métamoteur de recherche self-hosted et respectueux de la vie privée. Il agrège les résultats de Google, Bing, DuckDuckGo et des dizaines d'autres moteurs sans tracer les utilisateurs. Dans notre stack, il sert de source de données web pour le RAG.

## Ce qu'on peut faire

- Recherche web privée (pas de tracking, pas de pub)
- Fournir des résultats web aux agents IA (RAG augmenté)
- Agrégation de résultats depuis 70+ moteurs de recherche
- Recherche par catégories (web, images, actualités, science, IT...)
- API JSON pour l'intégration programmatique
- Personnalisation des moteurs et des pondérations

## Exemple concret : Utiliser SearXNG pour enrichir le RAG

### 1. Accéder à SearXNG

Ouvrir `http://IP:8081` ou `https://searxng.BASE_DOMAIN`

### 2. Recherche classique

Utiliser l'interface web comme un moteur de recherche normal. Tester des requêtes pour vérifier que les résultats remontent.

### 3. Utiliser l'API JSON

```bash
# Recherche simple
curl "http://localhost:8081/search?q=docker+compose+best+practices&format=json" \
  | python3 -m json.tool | head -50

# Recherche limitée aux actualités
curl "http://localhost:8081/search?q=intelligence+artificielle&format=json&categories=news" \
  | python3 -m json.tool

# Recherche IT/dev
curl "http://localhost:8081/search?q=python+fastapi+tutorial&format=json&categories=it" \
  | python3 -m json.tool
```

### 4. Intégrer dans Open WebUI

Open WebUI utilise SearXNG pour la recherche web en live dans le chat :

1. **Admin Panel** > **Settings** > **Web Search**
2. Activer "Enable Web Search"
3. Search Engine : `searxng`
4. SearXNG Query URL : `http://searxng:8080/search?q=<query>&format=json`
5. Sauvegarder

Ensuite dans le chat, cliquer sur l'icône 🌐 pour activer la recherche web avant de poser une question :
```
🌐 Quelles sont les dernières nouveautés de Docker en 2025 ?
```

### 5. Intégrer dans n8n

Créer un workflow avec un nœud HTTP Request :

```
[Webhook Trigger] → [HTTP Request: SearXNG] → [Code: Extract Results]
    → [AI Agent: Summarize]
```

Nœud **HTTP Request** :
- URL : `http://searxng:8080/search`
- Query Parameters :
  - `q` : `{{ $json.query }}`
  - `format` : `json`
  - `categories` : `general`

Nœud **Code** (extraction) :
```javascript
const results = $input.first().json.results.slice(0, 5);
return results.map(r => ({
  json: {
    title: r.title,
    url: r.url,
    content: r.content
  }
}));
```

### 6. Script Python : Recherche + Résumé IA

```python
import requests

# Rechercher sur SearXNG
results = requests.get("http://localhost:8081/search", params={
    "q": "LLM fine-tuning techniques 2025",
    "format": "json",
    "categories": "it"
}).json()

# Extraire le contexte
context = "\n\n".join([
    f"**{r['title']}**\n{r['content']}\nSource: {r['url']}"
    for r in results["results"][:5]
])

# Envoyer à Ollama pour résumer
summary = requests.post("http://localhost:11434/v1/chat/completions", json={
    "model": "llama3.1:8b",
    "messages": [
        {"role": "system", "content": "Résume les informations suivantes en français."},
        {"role": "user", "content": f"Voici les résultats de recherche :\n\n{context}"}
    ]
}).json()

print(summary["choices"][0]["message"]["content"])
```

## Configuration des moteurs

Le fichier `searxng/settings-base.yml` contient la configuration de base. Pour personnaliser les moteurs :

```yaml
engines:
  - name: google
    engine: google
    shortcut: go
    weight: 1.5    # Prioriser Google

  - name: duckduckgo
    engine: duckduckgo
    shortcut: ddg

  - name: github
    engine: github
    shortcut: gh
    categories: [it]
```

## Configuration

Variables d'environnement dans `.env` :
- `SEARXNG_HOSTNAME` — Sous-domaine pour le reverse proxy
- Le secret SearXNG est auto-généré par `start_services.py`
- Le fichier `settings.yml` est regénéré à chaque déploiement (gitignored)
