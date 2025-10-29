# 🧠 Local AI Packaged — Installation et utilisation

**Local AI Packaged** est une stack tout‑en‑un pour héberger un environnement complet d’IA locale :  
Ollama (LLMs), Open WebUI, Flowise, n8n, Supabase, Langfuse, Neo4j, Qdrant, et plus encore — le tout orchestré via Docker Compose.

Ce projet est conçu pour les **auto‑hébergeurs techniques** souhaitant déployer leur propre infrastructure IA sur un serveur local (NAS, mini‑PC, ou machine dédiée).

---

## ⚙️ 1. Prérequis

Avant de commencer, assurez‑vous d’avoir :

- 🐳 **Docker** et **Docker Compose** installés  
- 🐍 **Python 3.8+**  
- 💾 **Git**  
- 💡 Environ **16 Go de RAM** minimum recommandés

### GPU (optionnel)

- **NVIDIA :** [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)  
- **AMD :** ROCm configuré  
- **CPU uniquement :** fonctionne aussi, plus lentement

---

## 🚀 2. Installation rapide

### ① Cloner le dépôt

```bash
git clone https://github.com/gamersalpha/local-ai-packaged.git
cd local-ai-packaged
```

### ② Générer le fichier `.env` automatiquement

Le script `generate_env.py` crée automatiquement toutes les variables nécessaires :  
- mots de passe et clés aléatoires  
- détection du GPU (NVIDIA / AMD / CPU)  
- chemins locaux corrects

```bash
python3 generate_env.py --yes --regen-sensitive --docker
```

Une fois terminé, le script affiche les URLs locales de vos services :

```
🌐 Services disponibles :
  🧠 Ollama      : http://192.168.1.42:11434
  ⚙️ n8n          : http://192.168.1.42:5678
  💬 Open WebUI  : http://192.168.1.42:8080
  🧱 Supabase    : http://192.168.1.42:54323
```

---

## 🧩 3. Lancer et gérer les services

### ▶️ Démarrage automatisé

Le script `start_services.py` orchestre tout le déploiement :  
- vérifie ou crée le `.env`  
- clone automatiquement la stack Docker de **Supabase**  
- (dés)active Caddy si besoin  
- génère la clé SearXNG  
- démarre tous les conteneurs dans le bon ordre

```bash
python3 start_services.py --profile cpu
```

#### Options disponibles

| Option | Description |
|--------|--------------|
| `--profile [cpu|gpu-nvidia|gpu-amd]` | Choix du profil matériel |
| `--environment [private|public]` | Mode de déploiement |
| `--no-supabase` | Désactive Supabase |
| `--no-caddy` | Désactive Caddy |
| `--update` | Tire les dernières images Docker |
| `--dry-run` | Simule le lancement sans exécuter Docker |

Exemples :

```bash
# Lancement CPU
python3 start_services.py --profile cpu

# Lancement GPU (NVIDIA)
python3 start_services.py --profile gpu-nvidia

# Mise à jour avant lancement
python3 start_services.py --update
```

---

### ♻️ Mettre à jour la stack

Utilisez le script `update_services.sh` pour tout rafraîchir automatiquement :

```bash
./update_services.sh
```

Ce script :
1. stoppe tous les conteneurs  
2. tire les nouvelles images Docker  
3. redémarre la stack via `start_services.py`

---

## 🌍 4. Accès aux interfaces

| Service | Description | URL locale par défaut |
|----------|--------------|-----------------------|
| **n8n** | Workflow automation | http://192.168.1.42:5678 |
| **Open WebUI** | Interface de chat LLM | http://192.168.1.42:8080 |
| **Ollama** | API locale des modèles | http://192.168.1.42:11434 |
| **Flowise** | Concepteur de pipelines IA | http://192.168.1.42:3001 |
| **Supabase** | Base de données et auth | http://192.168.1.42:54323 |
| **Langfuse** | Suivi des appels LLM | http://192.168.1.42:3000 |
| **SearXNG** | Recherche web RAG | http://192.168.1.42:8080 |
| **Neo4j** | Base graphe | http://192.168.1.42:7474 |

*(Adaptez les IP selon votre réseau local)*

---

## 🛠️ 5. Dépannage rapide

### Supabase ne démarre pas ?
- Vérifiez que le dossier `supabase/` a bien été créé automatiquement.  
- Supprimez‑le et relancez : `python3 start_services.py --no-caddy`  
- Si besoin, ajoutez dans `.env` : `POOLER_DB_POOL_SIZE=5`

### GPU non détecté ?
- Vérifiez que le **NVIDIA Container Toolkit** ou **ROCm** est bien installé.  
- Vous pouvez toujours démarrer en mode CPU :  
  ```bash
  python3 start_services.py --profile cpu
  ```

### Ports déjà utilisés ?
Modifiez les ports directement dans `docker-compose.yml` avant de relancer.

---

## 🧾 Structure du projet

```
.
├── docker-compose.yml
├── start_services.py
├── update_services.sh
├── generate_env.py
├── supabase/           # auto-cloné par start_services.py (ignoré par Git)
├── n8n/
│   └── backup/
├── searxng/
├── shared/
└── neo4j/
```

> 📘 Le dossier `supabase/` est généré automatiquement et **ne doit pas être versionné**.  
> Il est déjà listé dans `.gitignore`.

---

## 📜 Licence

Sous licence **Apache 2.0**.  
Voir [LICENSE](LICENSE) pour plus d’informations.

---

**Créé avec ❤️ pour la communauté auto‑hébergeuse.**
