# 🕸️ Neo4j — Base de données de graphes

## C'est quoi ?

Neo4j est une base de données orientée graphe. Elle stocke les données sous forme de nœuds et de relations, idéale pour modéliser des réseaux de connaissances, des organigrammes, des dépendances ou tout ce qui est interconnecté.

## Ce qu'on peut faire

- Créer des knowledge graphs (graphes de connaissances)
- Modéliser des relations complexes entre entités
- Requêtes de traversée de graphe ultra-rapides (Cypher)
- Visualiser les relations dans le navigateur Neo4j intégré
- Combiner avec le RAG pour du GraphRAG (recherche contextuelle enrichie)
- Intégrer avec n8n et Flowise pour des agents intelligents

## Exemple concret : Knowledge Graph d'une infrastructure

### 1. Accéder à Neo4j Browser

Ouvrir `http://IP:7474` ou `https://neo4j.BASE_DOMAIN`

Identifiants par défaut : `neo4j` / voir `NEO4J_AUTH` dans `.env`

### 2. Créer des nœuds (serveurs, services)

```cypher
// Créer des serveurs
CREATE (s1:Server {name: "srv-docker-01", ip: "192.168.1.10", os: "Debian 12"})
CREATE (s2:Server {name: "srv-backup-01", ip: "192.168.1.20", os: "Ubuntu 24.04"})

// Créer des services
CREATE (n8n:Service {name: "n8n", type: "automation", port: 5678})
CREATE (ollama:Service {name: "Ollama", type: "llm", port: 11434})
CREATE (qdrant:Service {name: "Qdrant", type: "vectordb", port: 6333})
CREATE (pg:Service {name: "PostgreSQL", type: "database", port: 5432})

// Créer les relations
CREATE (n8n)-[:RUNS_ON]->(s1)
CREATE (ollama)-[:RUNS_ON]->(s1)
CREATE (qdrant)-[:RUNS_ON]->(s1)
CREATE (pg)-[:RUNS_ON]->(s1)
CREATE (n8n)-[:DEPENDS_ON]->(pg)
CREATE (n8n)-[:USES]->(ollama)
CREATE (n8n)-[:USES]->(qdrant)

RETURN *
```

### 3. Requêter le graphe

```cypher
// Tous les services sur un serveur
MATCH (s:Service)-[:RUNS_ON]->(srv:Server {name: "srv-docker-01"})
RETURN s.name, s.type, s.port

// Dépendances d'un service
MATCH (s:Service {name: "n8n"})-[:DEPENDS_ON|USES*1..3]->(dep)
RETURN s.name, dep.name, labels(dep)

// Services sans dépendances (autonomes)
MATCH (s:Service)
WHERE NOT (s)-[:DEPENDS_ON]->()
RETURN s.name
```

### 4. Knowledge Graph pour le RAG

Créer un graphe de connaissances que l'agent IA peut interroger :

```cypher
// Base de connaissances technique
CREATE (docker:Concept {name: "Docker", category: "containerization"})
CREATE (compose:Concept {name: "Docker Compose", category: "orchestration"})
CREATE (k8s:Concept {name: "Kubernetes", category: "orchestration"})
CREATE (volume:Concept {name: "Docker Volume", category: "storage"})

CREATE (compose)-[:IS_PART_OF]->(docker)
CREATE (volume)-[:IS_PART_OF]->(docker)
CREATE (k8s)-[:ALTERNATIVE_TO]->(compose)
CREATE (docker)-[:PREREQUISITE_FOR]->(k8s)

// Ajouter des descriptions pour le RAG
SET docker.description = "Plateforme de conteneurisation permettant d'isoler des applications"
SET compose.description = "Outil pour définir et gérer des applications multi-conteneurs"
```

### 5. Utiliser via l'API REST

```bash
# Exécuter une requête Cypher
curl -X POST http://localhost:7474/db/neo4j/tx/commit \
  -H "Content-Type: application/json" \
  -u neo4j:votre_mot_de_passe \
  -d '{
    "statements": [{
      "statement": "MATCH (n) RETURN count(n) as total_nodes"
    }]
  }'
```

## Intégrations dans le stack

| Service | Usage |
|---------|-------|
| **n8n** | Nœud Neo4j pour lire/écrire dans le graphe |
| **Flowise** | Nœud Neo4j Graph pour du GraphRAG |
| **Langfuse** | Tracer les requêtes GraphRAG |

Dans n8n et Flowise, utiliser `bolt://neo4j:7687` comme URL de connexion.

## Configuration

Variables d'environnement dans `.env` :
- `NEO4J_HOSTNAME` — Sous-domaine pour le reverse proxy
- `NEO4J_AUTH` — Identifiants (format `neo4j/password`)
- Ports : 7474 (HTTP/Browser), 7687 (Bolt), 7473 (HTTPS)
