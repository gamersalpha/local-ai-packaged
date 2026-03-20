# 💬 Open WebUI — Interface de chat IA

## C'est quoi ?

Open WebUI est une interface web moderne pour interagir avec vos modèles LLM. C'est l'équivalent self-hosted de ChatGPT, connecté à Ollama (ou toute API compatible OpenAI).

## Ce qu'on peut faire

- Chat avec tous les modèles Ollama installés
- Upload de documents pour du RAG (question/réponse sur vos fichiers)
- Gestion multi-utilisateurs avec rôles (admin, user)
- Historique des conversations
- System prompts personnalisés et presets
- Connexion à des APIs externes (OpenAI, Anthropic...) en plus d'Ollama
- Web search intégrée via SearXNG
- Custom pipes (plugins Python pour étendre les fonctionnalités)

## Exemple concret : Configurer le RAG sur vos documents

### 1. Accéder à Open WebUI

Ouvrir `https://open-webui.BASE_DOMAIN` ou `http://IP:8080`

### 2. Créer un compte admin

Au premier accès, le premier utilisateur créé devient admin.

### 3. Vérifier la connexion Ollama

- Aller dans **Admin Panel** > **Settings** > **Connections**
- Ollama URL devrait être : `http://ollama:11434`
- Cliquer sur le bouton de test pour vérifier

### 4. Activer la recherche web (SearXNG)

- **Admin Panel** > **Settings** > **Web Search**
- Activer "Enable Web Search"
- Search Engine : `searxng`
- SearXNG URL : `http://searxng:8080`
- Sauvegarder

### 5. Uploader un document pour le RAG

1. Dans le chat, cliquer sur l'icône **+** (attachement)
2. Uploader un PDF, TXT, DOCX ou tout document texte
3. Le document est automatiquement découpé et indexé
4. Poser une question sur le contenu :

```
Résume les points clés de ce document.
Quelles sont les recommandations principales ?
```

### 6. Créer un preset de conversation

- **Workspace** > **Models** > **Create a Model**
- Nom : "Assistant DevOps"
- System Prompt :
```
Tu es un expert DevOps senior. Tu réponds en français avec des exemples
de commandes concrètes. Tu utilises Docker, Kubernetes, Terraform et Ansible.
Quand on te pose une question, tu donnes d'abord la solution rapide puis
tu expliques pourquoi.
```
- Modèle de base : `llama3.1:8b`
- Sauvegarder

Ce preset sera disponible dans le sélecteur de modèles pour tous les utilisateurs.

### 7. Connecter une API externe (optionnel)

Pour utiliser GPT-4 ou Claude en plus d'Ollama :
- **Admin Panel** > **Settings** > **Connections**
- Ajouter une connexion OpenAI :
  - URL : `https://api.openai.com/v1`
  - Clé API : votre clé OpenAI

## Custom Pipe : Connecter n8n

Le fichier `n8n_pipe.py` fourni dans le repo permet de router les messages vers un workflow n8n :

1. **Admin Panel** > **Workspace** > **Functions** > **Import**
2. Importer `n8n_pipe.py`
3. Configurer l'URL du webhook n8n dans les valves du pipe

Cela permet d'utiliser n8n comme "cerveau" derrière Open WebUI avec des agents RAG avancés.

## Configuration

Variables d'environnement dans `.env` :
- `WEBUI_HOSTNAME` — Sous-domaine pour le reverse proxy
- Les données sont persistées dans le volume `open-webui`
- SearXNG est auto-connecté si déployé ensemble
