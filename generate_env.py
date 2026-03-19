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
    "WEBUI_HOSTNAME": "openwebui",
    "FLOWISE_HOSTNAME": "flowise",
    "SUPABASE_HOSTNAME": "supabase",
    "LANGFUSE_HOSTNAME": "langfuse",
    "NEO4J_HOSTNAME": "neo4j",
    "SEARXNG_HOSTNAME": "searxng",
    "OLLAMA_HOSTNAME": "ollama",
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

    # 🔐 Régénération forcée de certaines variables
    print("🔐 Régénération forcée : FLOWISE_USERNAME / FLOWISE_PASSWORD / PG_META_CRYPTO_KEY / ENCRYPTION_KEY")
    forced = {
        "FLOWISE_USERNAME": "FLOWISEUSER",
        "FLOWISE_PASSWORD": generate_secret(24),
        "PG_META_CRYPTO_KEY": generate_secret(48),
        "ENCRYPTION_KEY": secrets.token_hex(32),  # Must be 64 hex chars for Langfuse
    }
    for k in forced:
        output_lines = [ln for ln in output_lines if not ln.startswith(f"{k}=")]
    for k, v in forced.items():
        output_lines.append(f"{k}={safe_for_env_write(sanitize_secret(v))}\n")

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
    ip = get_server_ip()
    print("\n🌐 Services disponibles :")
    print(f"  🧠 Ollama      : http://{ip}:11434")
    print(f"  ⚙️  n8n         : http://{ip}:5678")
    print(f"  💬 Open WebUI  : http://{ip}:8080")
    print(f"  🌊 Flowise     : http://{ip}:3001")
    print(f"  📦 Qdrant      : http://{ip}:6333")
    print(f"  🔍 SearXNG     : http://{ip}:8081")
    print(f"  📊 Langfuse    : http://{ip}:3000")
    print(f"  🕸️  Neo4j       : http://{ip}:7474")
    print(f"  🐘 PostgreSQL  : {ip}:5433")


if __name__ == "__main__":
    main()
