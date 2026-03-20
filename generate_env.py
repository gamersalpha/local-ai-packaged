#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_env.py - Générateur de .env + (optionnel) lancement Docker Compose

Caractéristiques :
- Génère uniquement des secrets avec A–Z a–z 0–9 ! ?
- Ajoute automatiquement :
    LOCAL_AI_BASE_PATH=/.../local-ai-packaged-infra
    LOCAL_AI_INFRA_PATH=/.../local-ai-packaged-infra/DATAS
- Détection GPU (NVIDIA / AMD / CPU)
- Lancement Docker Compose optionnel (--docker)
"""

import os
import re
import argparse
import secrets
import string
import stat
import subprocess
import shutil
import socket
from getpass import getpass

# -------------------------
# Config et helpers
# -------------------------
SENSITIVE_REGEX = re.compile(r"(PASS(word)?|SECRET|KEY|TOKEN|JWT|SALT|AUTH|ACCESS)", re.IGNORECASE)
# Variables that match SENSITIVE_REGEX but should NOT be treated as secrets
# Variables that match SENSITIVE_REGEX but need special handling (not random A-Z/0-9/!?)
SENSITIVE_EXCLUDE = {"NEO4J_AUTH", "REDIS_AUTH", "ENCRYPTION_KEY"}
# Variables that should NEVER be regenerated once they have a value (encryption keys that
# are baked into volumes/databases — changing them breaks existing data).
NEVER_REGEN = {"N8N_ENCRYPTION_KEY", "ENCRYPTION_KEY"}
VAR_LINE_RE = re.compile(r"^([A-Za-z0-9_]+)=(.*)$")

ALLOWED_SPECIAL = "!?"
ALLOWED_SET = set(string.ascii_letters + string.digits + ALLOWED_SPECIAL)


def generate_secret(length=32):
    """Secret restreint à A–Z a–z 0–9 ! ?"""
    alphabet = string.ascii_letters + string.digits + ALLOWED_SPECIAL
    while True:
        val = "".join(secrets.choice(alphabet) for _ in range(length))
        if any(c.isdigit() for c in val) and any(c.isalpha() for c in val):
            return val


def sanitize_secret(value: str) -> str:
    """Nettoie un secret existant pour ne conserver que les caractères autorisés."""
    if value is None:
        return ""
    chars = []
    for c in str(value):
        if c in ALLOWED_SET:
            chars.append(c)
        else:
            chars.append(secrets.choice(string.ascii_letters + string.digits + ALLOWED_SPECIAL))
    s = "".join(chars)
    if not any(ch.isdigit() for ch in s):
        s += secrets.choice(string.digits)
    if not any(ch.isalpha() for ch in s):
        s += secrets.choice(string.ascii_letters)
    return s


def safe_for_env_write(value: str) -> str:
    """Protège les valeurs pour écriture dans .env."""
    if value is None:
        return ""
    return str(value).replace("$", "$$")


def detect_gpu():
    """Détecte le type de GPU présent (NVIDIA / AMD / CPU)."""
    if shutil.which("nvidia-smi"):
        return "nvidia"
    if shutil.which("rocm-smi") or os.path.isdir("/opt/rocm"):
        return "amd"
    return "cpu"


def get_server_ip():
    """Détermine l'IP locale."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


def run_command(cmd):
    """Exécute une commande shell."""
    print(f"▶️  Commande : {' '.join(cmd)}")
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr)
        raise RuntimeError(f"Commande échouée ({proc.returncode}) : {' '.join(cmd)}")
    else:
        if proc.stdout:
            print(proc.stdout)
        print("✅ Commande réussie !")


def prompt_for(varname, current_value, auto_accept=False, regen_sensitive=False, secret_length=32):
    sensitive = SENSITIVE_REGEX.search(varname) is not None and varname not in SENSITIVE_EXCLUDE

    # Never regenerate encryption keys that are tied to existing data
    if varname in NEVER_REGEN and current_value != "":
        return current_value

    if auto_accept:
        if sensitive and regen_sensitive:
            return generate_secret(secret_length)
        if current_value != "":
            return sanitize_secret(current_value) if sensitive else current_value
        if sensitive:
            return generate_secret(secret_length)
        return ""

    if sensitive:
        print(f"\nVariable sensible détectée: {varname}")
        while True:
            choice = input("Voulez-vous (g)énérer, (t)aper manuellement, (s)auter ? [g/t/s] ").strip().lower()
            if choice in ("g", "", "G"):
                val = generate_secret(secret_length)
                print(f"Généré: {val}")
                ok = input("Utiliser cette valeur ? [Y/n] ").strip().lower()
                if ok in ("", "y", "o"):
                    return val
            elif choice == "t":
                val = getpass(f"Saisir la valeur pour {varname}: ")
                if val:
                    return sanitize_secret(val)
                print("Valeur vide, recommencez ou choisissez 's'.")
            elif choice == "s":
                return ""
            else:
                print("Choix invalide.")
    else:
        if current_value != "":
            ans = input(f"{varname} (défaut: '{current_value}'). Entrée => garder, sinon taper nouvelle valeur: ")
            return ans or current_value
        return input(f"{varname} (pas de défaut). Saisir valeur ou laisser vide: ")


# -------------------------
# Domain expansion
# -------------------------
SERVICE_SUBDOMAIN_DEFAULTS = {
    "N8N_HOSTNAME": "n8n",
    "WEBUI_HOSTNAME": "open-webui",
    "FLOWISE_HOSTNAME": "flowise",
    "SUPABASE_HOSTNAME": "supabase",
    "LANGFUSE_HOSTNAME": "langfuse",
    "NEO4J_HOSTNAME": "neo4j",
    "SEARXNG_HOSTNAME": "searxng",
    "OLLAMA_HOSTNAME": "ollama",
    "QDRANT_HOSTNAME": "qdrant",
    "UNSLOTH_HOSTNAME": "unsloth",
    "HUB_HOSTNAME": "hub",
}


def expand_hostnames(env_lines):
    """If BASE_DOMAIN is set and individual hostnames are not, derive them."""
    env_dict = {}
    for line in env_lines:
        m = VAR_LINE_RE.match(line.strip())
        if m:
            env_dict[m.group(1)] = m.group(2)

    base_domain = env_dict.get("BASE_DOMAIN", "").strip()
    if not base_domain:
        return env_lines

    print(f"🌐 BASE_DOMAIN={base_domain} — expanding hostnames...")
    additions = []
    for var, subdomain in SERVICE_SUBDOMAIN_DEFAULTS.items():
        existing = env_dict.get(var, "").strip()
        if not existing:
            hostname = f"{subdomain}.{base_domain}"
            additions.append(f"{var}={hostname}\n")
            print(f"   {var}={hostname}")

    return env_lines + additions


# -------------------------
# Main
# -------------------------
def main():
    parser = argparse.ArgumentParser(description="Génère .env et peut démarrer Docker Compose.")
    parser.add_argument("--example", "-e", default="./.env.example", help="Chemin vers .env.example")
    parser.add_argument("--output", "-o", default="./.env", help="Chemin du fichier .env généré")
    parser.add_argument("--yes", "-y", action="store_true", help="Accepter les valeurs par défaut sans prompt")
    parser.add_argument("--regen-sensitive", action="store_true", help="Regénérer toutes les variables sensibles")
    parser.add_argument("--domain", type=str, default=None, help="Définir BASE_DOMAIN (ex: home.example.com)")
    parser.add_argument("--docker", action="store_true", help="Construire et démarrer Docker Compose automatiquement")
    parser.add_argument("--secret-length", type=int, default=32, help="Longueur des secrets générés")
    args = parser.parse_args()

    if not os.path.exists(args.example):
        print(f"❌ Fichier {args.example} introuvable")
        return

    with open(args.example, "r", encoding="utf-8") as f:
        lines = f.readlines()

    output_lines = []
    for line in lines:
        m = VAR_LINE_RE.match(line.strip())
        if m:
            var = m.group(1)
            raw_val = m.group(2)
            val_inner = raw_val.strip().strip('"').strip("'")

            if val_inner.upper() in ("", "REPLACE_ME", "CHANGE_ME", "YOUR_VALUE_HERE", "PUT_YOUR_KEY_HERE"):
                val_inner = ""

            new_val = prompt_for(
                var,
                val_inner,
                auto_accept=args.yes,
                regen_sensitive=args.regen_sensitive,
                secret_length=args.secret_length,
            )
            if SENSITIVE_REGEX.search(var) and var not in SENSITIVE_EXCLUDE:
                new_val = sanitize_secret(new_val)

            safe_val = safe_for_env_write(new_val)
            output_lines.append(f"{var}={safe_val}\n")
        else:
            output_lines.append(line)

    # 🔐 Régénération forcée de certaines variables (sauf celles déjà présentes dans NEVER_REGEN)
    # Lire les valeurs existantes pour préserver les clés critiques
    existing_env = {}
    if os.path.exists(args.output):
        with open(args.output, "r", encoding="utf-8") as f:
            for ln in f:
                m = VAR_LINE_RE.match(ln.strip())
                if m:
                    existing_env[m.group(1)] = m.group(2).strip().strip('"').strip("'")

    forced = {
        "FLOWISE_USERNAME": "FLOWISEUSER",
        "FLOWISE_PASSWORD": generate_secret(24),
        "PG_META_CRYPTO_KEY": generate_secret(48),
        "ENCRYPTION_KEY": secrets.token_hex(32),  # Must be 64 hex chars for Langfuse
    }
    # Préserver les clés critiques si elles existent déjà
    for k in list(forced.keys()):
        if k in NEVER_REGEN and existing_env.get(k, "").strip():
            print(f"  🔒 {k} préservée (clé existante)")
            forced[k] = existing_env[k]

    print("🔐 Régénération forcée : FLOWISE_USERNAME / FLOWISE_PASSWORD / PG_META_CRYPTO_KEY / ENCRYPTION_KEY")
    for k in forced:
        output_lines = [ln for ln in output_lines if not ln.startswith(f"{k}=")]
    for k, v in forced.items():
        output_lines.append(f"{k}={safe_for_env_write(v)}\n")

    # 🌐 Définition interactive ou CLI de BASE_DOMAIN
    domain = args.domain
    if domain is None and not args.yes:
        # Chercher la valeur actuelle de BASE_DOMAIN
        current_domain = ""
        for ln in output_lines:
            m = VAR_LINE_RE.match(ln.strip())
            if m and m.group(1) == "BASE_DOMAIN":
                current_domain = m.group(2).strip().strip('"').strip("'")
                break
        prompt_msg = f"🌐 Domaine de base (BASE_DOMAIN) [{current_domain or 'vide'}] : "
        user_input = input(prompt_msg).strip()
        if user_input:
            domain = user_input

    if domain is not None:
        # Remplacer ou ajouter BASE_DOMAIN
        found = False
        for i, ln in enumerate(output_lines):
            m = VAR_LINE_RE.match(ln.strip())
            if m and m.group(1) == "BASE_DOMAIN":
                output_lines[i] = f"BASE_DOMAIN={domain}\n"
                found = True
                break
        if not found:
            output_lines.append(f"BASE_DOMAIN={domain}\n")
        print(f"🌐 BASE_DOMAIN={domain}")

    # 📂 Ajout automatique des chemins dynamiques
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_path = script_dir
    infra_path = os.path.join(base_path, "DATAS")

    output_lines = [
        ln for ln in output_lines
        if not ln.startswith("LOCAL_AI_BASE_PATH=") and not ln.startswith("LOCAL_AI_INFRA_PATH=")
    ]
    output_lines.append(f"LOCAL_AI_BASE_PATH={base_path}\n")
    output_lines.append(f"LOCAL_AI_INFRA_PATH={infra_path}\n")

    # 🌐 Ajout automatique de SERVER_IP
    output_lines = [ln for ln in output_lines if not ln.startswith("SERVER_IP=")]
    output_lines.append(f"SERVER_IP={get_server_ip()}\n")

    # 🌐 Expansion automatique BASE_DOMAIN → hostnames individuels
    output_lines = expand_hostnames(output_lines)

    # 💾 Sauvegarde et écriture
    if os.path.exists(args.output):
        os.replace(args.output, args.output + ".bak")
    with open(args.output, "w", encoding="utf-8") as f:
        f.writelines(output_lines)
    try:
        os.chmod(args.output, stat.S_IRUSR | stat.S_IWUSR)
    except Exception:
        pass

    print(f"✅ Fichier .env généré : {args.output}")
    print(f"📁 LOCAL_AI_BASE_PATH={base_path}")
    print(f"📁 LOCAL_AI_INFRA_PATH={infra_path}")

    # 🚀 Docker Compose (optionnel)
    if args.docker:
        gpu = detect_gpu()
        profile = {"nvidia": "gpu-nvidia", "amd": "gpu-amd", "cpu": "cpu"}[gpu]
        print(f"🔍 GPU détecté : {gpu.upper()} → profil '{profile}'")
        try:
            run_command(["docker", "compose", "-p", "local-ai", "--profile", profile, "-f", "docker-compose.yml", "up", "-d", "--build"])
        except Exception as e:
            print(f"⚠️  Erreur Docker Compose : {e}")

    # 🌐 Affichage des services
    # Lire le .env généré pour détecter BASE_DOMAIN et les hostnames
    env_vars = {}
    if os.path.exists(args.output):
        with open(args.output, "r", encoding="utf-8") as f:
            for ln in f:
                m = VAR_LINE_RE.match(ln.strip())
                if m:
                    env_vars[m.group(1)] = m.group(2).strip().strip('"').strip("'")

    base_domain = env_vars.get("BASE_DOMAIN", "").strip()
    ip = get_server_ip()

    def svc_domain(hostname_var, subdomain):
        """Retourne l'URL domaine si BASE_DOMAIN défini, sinon None."""
        host = env_vars.get(hostname_var, "").strip()
        if host:
            return f"https://{host}"
        if base_domain:
            return f"https://{subdomain}.{base_domain}"
        return None

    def svc_line(emoji, name, hostname_var, subdomain, port):
        """Affiche une ligne : domaine + IP:port, ou juste IP:port."""
        local = f"http://{ip}:{port}"
        domain = svc_domain(hostname_var, subdomain)
        if domain:
            return f"  {emoji} {name}: {domain}  —  {local}"
        return f"  {emoji} {name}: {local}"

    print("\n🌐 Services disponibles :")
    print(svc_line("🧠", "Ollama     ", "OLLAMA_HOSTNAME", "ollama", 11434))
    print(svc_line("⚙️ ", "n8n        ", "N8N_HOSTNAME", "n8n", 5678))
    print(svc_line("💬", "Open WebUI ", "WEBUI_HOSTNAME", "openwebui", 8080))
    print(svc_line("🌊", "Flowise    ", "FLOWISE_HOSTNAME", "flowise", 3001))
    print(svc_line("📦", "Qdrant     ", "QDRANT_HOSTNAME", "qdrant", 6333))
    print(svc_line("🔍", "SearXNG    ", "SEARXNG_HOSTNAME", "searxng", 8081))
    print(svc_line("📊", "Langfuse   ", "LANGFUSE_HOSTNAME", "langfuse", 3000))
    print(svc_line("🕸️ ", "Neo4j      ", "NEO4J_HOSTNAME", "neo4j", 7474))
    print(svc_line("🧬", "Unsloth    ", "UNSLOTH_HOSTNAME", "unsloth", 8888))
    print(svc_line("🏠", "Hub        ", "HUB_HOSTNAME", "hub", 8090))
    print(f"  🐘 PostgreSQL  : {ip}:5433")


if __name__ == "__main__":
    main()
